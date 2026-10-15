"""Solicitudes, generación, procesamiento y vigencia de propuestas (Task 7, puntos 1 a 4).

La captura de evidencia y su huella comparten una representación. El procesador
reclama cada trabajo con un token y llama al modelo fuera de la transacción.
"""
from dataclasses import dataclass, field
from datetime import timedelta
import hashlib
import json
import uuid

from django.core.exceptions import ValidationError
from django.db import connection, OperationalError, transaction
from django.db.models import F, Q
from django.utils import timezone

from .models import DescriptorNivel, Manifestacion, Nino, NivelValidado, Nucleo, Observacion, PropuestaNivel, Rubrica, validar_nivel
from .ia.bedrock import ClienteBedrock
from .ia.propuesta import ErrorConfiguracionPropuesta, ErrorPropuesta, VERSION_PROMPT, leer_prompt, proponer

MAX_INTENTOS = 3
CADUCIDAD_SEGUNDOS = 300
ACTIVAS = (PropuestaNivel.Estado.SOLICITADA, PropuestaNivel.Estado.PROCESANDO)


@dataclass(frozen=True)
class EntradaPropuesta:
    datos: dict = field(repr=False)
    identidades: list = field(repr=False)
    huella: str
    nivel_referencia: object = field(repr=False)
    rubrica_provisoria: bool
    version_prompt: str


@dataclass(frozen=True)
class GeneracionPropuesta:
    entrada: EntradaPropuesta
    respuesta: dict = field(repr=False)
    modelo: str
    uso: dict


def _capturar_entrada(nino, nucleo, version_prompt):
    # Volver a leer evita que objetos relacionados cacheados oculten cambios.
    nino = Nino.objects.select_related("curso").get(pk=nino.pk)
    nucleo = Nucleo.objects.get(pk=nucleo.pk)
    educativo = nino.curso.nivel_educativo
    referencia = nino.nivel_actual(nucleo)
    rubricas = list(Rubrica.objects.filter(nivel_educativo=educativo).values("cantidad_niveles"))
    maximo = rubricas[0]["cantidad_niveles"] if rubricas else 0
    descriptores = list(DescriptorNivel.objects.filter(
        nivel_educativo=educativo, nucleo=nucleo, nivel__lte=maximo,
    ).order_by("nivel").values("nivel", "nombre", "descripcion", "conducta", "ejemplos", "provisorio"))
    provisoria = not descriptores or any(d["provisorio"] for d in descriptores)
    # El segundo ejemplo oficial se reserva para evaluación: no forma parte de la entrada.
    for descriptor in descriptores:
        if isinstance(descriptor["ejemplos"], list):
            descriptor["ejemplos"] = descriptor["ejemplos"][:1]
    observaciones = Observacion.objects.filter(
        nino=nino, captura__curso_id=nino.curso_id, estado=Observacion.Estado.ACEPTADA, grupal=False,
    ).filter(Q(nucleos=nucleo) | Q(oas__nucleo=nucleo, oas__nivel_educativo=educativo)).distinct().prefetch_related(
        "nucleos", "oas__nucleo",
    ).order_by("fecha", "id")
    evidencia = [{
        "id": o.pk, "fecha": o.fecha.isoformat(), "cita": o.cita, "apoyo": o.apoyo,
        "nucleos": sorted(n.pk for n in o.nucleos.all()),
        "oas": sorted(oa.codigo for oa in o.oas.all()
                      if oa.nucleo_id == nucleo.pk and oa.nivel_educativo == educativo),
    } for o in observaciones]
    entrada = {
        "version_prompt": version_prompt,
        "nino": nino.codigo, "nivel_educativo": educativo,
        "referencia": ({"id": referencia.pk, "nivel": referencia.nivel,
                        "fecha": referencia.fecha.isoformat()} if referencia else None),
        "rubrica": rubricas,
        "nucleo": {"sigla": nucleo.sigla, "nombre": nucleo.nombre},
        "descriptores": descriptores,
        "evidencia": evidencia,
        "oas": list(nucleo.oas.filter(nivel_educativo=educativo).order_by("numero").values("id", "numero", "texto")),
    }
    if provisoria:
        entrada["trayectoria"] = {"inicio_nt1": nucleo.esperado_inicio_nt1, "continuidad": nucleo.continuidad_basica}
        entrada["manifestaciones"] = list(Manifestacion.objects.filter(
            oa__nucleo=nucleo, oa__nivel_educativo=educativo,
        ).order_by("oa_id", "anio", "orden", "pk").values("oa_id", "anio", "orden", "texto"))
    identidades = list(Nino.objects.filter(curso_id=nino.curso_id).order_by("pk").values("codigo", "nombre", "alias"))
    # El catálogo de identidades solo participa del hash local. También se incluye
    # el archivo de prompt, para detectar cambios aunque se conserve su versión.
    huella = hashlib.sha256(json.dumps(
        {"datos": entrada, "identidades": identidades, "prompt": leer_prompt()},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return EntradaPropuesta(entrada, identidades, huella, referencia, provisoria, version_prompt)


def _entrada(nino, nucleo, version_prompt):
    entrada = _capturar_entrada(nino, nucleo, version_prompt)
    return entrada.huella, entrada.nivel_referencia, entrada.rubrica_provisoria


@transaction.atomic
def preparar_evidencia(nino, nucleo):
    """Captura consistente para generar y posteriormente guardar con la misma huella."""
    return _capturar_entrada(nino, nucleo, VERSION_PROMPT)


def generar_propuesta(nino, nucleo, *, cliente=None):
    """Genera y valida sin guardar; el procesador usa la misma función de evaluación."""
    entrada = preparar_evidencia(nino, nucleo)
    return evaluar_entrada(entrada, cliente=cliente)


def evaluar_entrada(entrada, *, cliente=None):
    """Consulta el modelo usando exactamente la captura recibida, fuera de la transacción."""
    cliente = cliente if cliente is not None else ClienteBedrock()
    respuesta = proponer(entrada.datos, entrada.identidades, cliente=cliente)
    hubo_llamada = bool(entrada.datos["evidencia"])
    return GeneracionPropuesta(entrada, respuesta, getattr(cliente, "modelo", "") if hubo_llamada else "",
                              dict(getattr(cliente, "ultimo_uso", None) or {}) if hubo_llamada else {})


def huella_entrada(nino, nucleo, *, version_prompt=VERSION_PROMPT):
    """SHA-256 reproducible del contexto que puede influir en la propuesta."""
    return _entrada(nino, nucleo, version_prompt)[0]


@transaction.atomic
def registrar_entrada(propuesta, *, version_prompt=VERSION_PROMPT):
    """Fija la entrada antes de generar. No permite reescribir trazabilidad histórica."""
    actual = PropuestaNivel.objects.get(pk=propuesta.pk)
    if actual.estado not in (PropuestaNivel.Estado.SOLICITADA, PropuestaNivel.Estado.PROCESANDO):
        raise ValidationError("Solo se prepara la entrada de una solicitud pendiente o en procesamiento.")
    if not version_prompt:
        raise ValidationError("La versión del prompt es obligatoria.")
    huella, referencia, provisoria = _entrada(actual.nino, actual.nucleo, version_prompt)
    actual.huella_entrada, actual.nivel_referencia = huella, referencia
    actual.rubrica_provisoria, actual.version_prompt = provisoria, version_prompt
    actual.save(update_fields=["huella_entrada", "nivel_referencia", "rubrica_provisoria", "version_prompt", "actualizada"])
    for campo in ("huella_entrada", "nivel_referencia", "rubrica_provisoria", "version_prompt", "actualizada"):
        setattr(propuesta, campo, getattr(actual, campo))
    return propuesta


def entrada_vigente(propuesta, *, version_prompt=VERSION_PROMPT):
    """Compara sin mutar. Una propuesta heredada sin huella no es verificable."""
    if not propuesta.huella_entrada or propuesta.version_prompt != version_prompt:
        return False
    return propuesta.huella_entrada == huella_entrada(propuesta.nino, propuesta.nucleo, version_prompt=version_prompt)


def comprobar_vigencia(propuesta, *, version_prompt=VERSION_PROMPT):
    """Invalida sugerencias listas que cambiaron; conserva resoluciones históricas."""
    with transaction.atomic():
        actual = PropuestaNivel.objects.get(pk=propuesta.pk)
        vigente = entrada_vigente(actual, version_prompt=version_prompt)
        if not vigente:
            PropuestaNivel.objects.filter(pk=actual.pk, estado=PropuestaNivel.Estado.LISTA).update(
                estado=PropuestaNivel.Estado.OBSOLETA, actualizada=timezone.now(),
            )
        propuesta.refresh_from_db()
        return vigente and propuesta.estado != PropuestaNivel.Estado.OBSOLETA


@transaction.atomic
def solicitar_propuesta(nino, nucleo, *, reintentar=False):
    """Devuelve (propuesta, creada); serializa solicitudes del niño también en SQLite.

    La primera operación es una escritura sin cambio de valor: evita ascender un
    bloqueo de lectura a escritura y no depende de select_for_update en SQLite.
    La restricción única sigue siendo la defensa final para solicitudes activas.
    """
    if not Nino.objects.filter(pk=nino.pk).update(codigo=F("codigo")):
        raise Nino.DoesNotExist
    propuestas = PropuestaNivel.objects.filter(nino_id=nino.pk, nucleo_id=nucleo.pk)
    activa = propuestas.filter(estado__in=ACTIVAS).first()
    if activa:
        return activa, False
    ultima = propuestas.order_by("-creada", "-pk").first()
    if ultima and ultima.estado == PropuestaNivel.Estado.LISTA:
        try:
            if entrada_vigente(ultima):
                return ultima, False
        except ErrorPropuesta:
            pass  # La configuración se diagnostica y registra en el procesador.
    if ultima and ultima.estado == PropuestaNivel.Estado.ERROR and not reintentar:
        return ultima, False
    propuestas.filter(estado=PropuestaNivel.Estado.LISTA).update(
        estado=PropuestaNivel.Estado.OBSOLETA, actualizada=timezone.now(),
    )
    return PropuestaNivel.objects.create(nino_id=nino.pk, nucleo_id=nucleo.pk), True


def tomar_siguiente():
    """Toma un trabajo con una actualización condicional atómica y un token nuevo."""
    try:
        candidatos = list(PropuestaNivel.objects.filter(
            estado=PropuestaNivel.Estado.SOLICITADA, intentos__lt=MAX_INTENTOS,
        ).select_related("nino__curso", "nucleo").order_by("creada", "pk")[:100])
    except OperationalError as error:
        if connection.vendor == "sqlite" and "locked" in str(error).lower():
            return None
        raise
    for trabajo in candidatos:
        token, ahora = uuid.uuid4(), timezone.now()
        try:
            tomada = PropuestaNivel.objects.filter(
                pk=trabajo.pk, estado=PropuestaNivel.Estado.SOLICITADA, intentos=trabajo.intentos,
                nino_id=trabajo.nino_id, nucleo_id=trabajo.nucleo_id,
            ).update(
                estado=PropuestaNivel.Estado.PROCESANDO, token_procesamiento=token,
                procesamiento_iniciado=ahora, intentos=F("intentos") + 1, actualizada=ahora, error="",
            )
        except OperationalError as error:
            if connection.vendor == "sqlite" and "locked" in str(error).lower():
                return None  # Otro escritor trabaja; el bucle volverá a consultar.
            raise
        if tomada:
            trabajo.estado, trabajo.token_procesamiento = PropuestaNivel.Estado.PROCESANDO, token
            trabajo.procesamiento_iniciado, trabajo.actualizada = ahora, ahora
            trabajo.intentos += 1
            trabajo.error = ""
            return trabajo
    return None


def _propietario(trabajo):
    return PropuestaNivel.objects.filter(pk=trabajo.pk, estado=PropuestaNivel.Estado.PROCESANDO,
                                        token_procesamiento=trabajo.token_procesamiento)


@transaction.atomic
def _preparar_trabajo(trabajo):
    # Reservar la escritura antes de leer el contexto mantiene consistente la
    # captura y la titularidad del intento, sin sostenerla durante la llamada.
    if not _propietario(trabajo).update(actualizada=timezone.now()):
        return None
    entrada = _capturar_entrada(trabajo.nino, trabajo.nucleo, VERSION_PROMPT)
    _propietario(trabajo).update(
        huella_entrada=entrada.huella, nivel_referencia=entrada.nivel_referencia,
        rubrica_provisoria=entrada.rubrica_provisoria, version_prompt=entrada.version_prompt,
    )
    return entrada


@transaction.atomic
def _guardar_resultado(trabajo, generacion):
    Nino.objects.filter(pk=trabajo.nino_id).update(codigo=F("codigo"))
    if not _propietario(trabajo).update(actualizada=timezone.now()):
        return  # Un intento recuperado no puede publicar el resultado anterior.
    entrada = generacion.entrada
    if huella_entrada(trabajo.nino, trabajo.nucleo) != entrada.huella:
        _propietario(trabajo).update(
            estado=PropuestaNivel.Estado.OBSOLETA, token_procesamiento=None,
            modelo=generacion.modelo, uso_modelo=generacion.uso,
            error="La entrada cambió durante la generación; se solicitó una propuesta nueva.",
        )
        solicitar_propuesta(trabajo.nino, trabajo.nucleo, reintentar=True)
        return
    r = generacion.respuesta
    _propietario(trabajo).update(
        estado=PropuestaNivel.Estado.LISTA, token_procesamiento=None, nivel=r["nivel"],
        evidencia_suficiente=r["evidencia_suficiente"], justificacion=r["justificacion"],
        conductas_observadas=r["conductas_observadas"], modelo=generacion.modelo,
        uso_modelo=generacion.uso, error="", actualizada=timezone.now(),
    )
    trabajo.observaciones_citadas.set(r["observaciones_citadas"])


def procesar_siguiente(*, cliente=None):
    """Procesa como máximo una solicitud. Nunca modifica niveles validados."""
    trabajo = tomar_siguiente()
    if trabajo is None:
        return None
    entrada = None
    cliente = cliente if cliente is not None else ClienteBedrock()
    try:
        entrada = _preparar_trabajo(trabajo)
        if entrada is not None:
            generacion = evaluar_entrada(entrada, cliente=cliente)
            _guardar_resultado(trabajo, generacion)
    except Exception as error:
        # No persistir mensajes de SDK, respuestas crudas ni repr de evidencia.
        if isinstance(error, ErrorConfiguracionPropuesta):
            mensaje = "No se pudo preparar la rúbrica o la evidencia. Revisa los datos antes de reintentar."
        elif isinstance(error, ErrorPropuesta):
            mensaje = "No se pudo generar una propuesta válida. Puedes reintentar."
        else:
            mensaje = "El procesamiento falló. Puedes reintentar."
        _propietario(trabajo).update(estado=PropuestaNivel.Estado.ERROR, token_procesamiento=None,
                                    error=mensaje, actualizada=timezone.now(),
                                    modelo=getattr(cliente, "modelo", "") if entrada and entrada.datos["evidencia"] else "")
    trabajo.refresh_from_db()
    return trabajo


def recuperar_interrumpidas(*, caducidad=CADUCIDAD_SEGUNDOS, limite=100):
    """Recupera hasta limite intentos vencidos; después de tres, requiere reintento humano."""
    if caducidad < 120 or limite < 1:
        raise ValueError("La caducidad debe ser al menos 120 segundos y el límite positivo.")
    vencimiento = timezone.now() - timedelta(seconds=caducidad)
    vencidas = list(PropuestaNivel.objects.filter(
        estado=PropuestaNivel.Estado.PROCESANDO, procesamiento_iniciado__lt=vencimiento,
    ).order_by("procesamiento_iniciado", "pk")[:limite])
    recuperadas = 0
    for trabajo in vencidas:
        agotada = trabajo.intentos >= MAX_INTENTOS
        recuperadas += _propietario(trabajo).filter(procesamiento_iniciado__lt=vencimiento).update(
            estado=PropuestaNivel.Estado.ERROR if agotada else PropuestaNivel.Estado.SOLICITADA,
            token_procesamiento=None, procesamiento_iniciado=None, actualizada=timezone.now(),
            error=("Se agotaron los intentos de recuperación. Puedes reintentar."
                   if agotada else "El procesamiento se interrumpió; se reintentará."),
        )
    return recuperadas


@dataclass(frozen=True)
class ResolucionPropuesta:
    propuesta: PropuestaNivel
    validacion: NivelValidado | None
    realizada: bool


def _bloquear_nino_que_valida(nino_id, usuaria):
    if not usuaria.is_authenticated or not Nino.objects.filter(pk=nino_id, curso__educadora=usuaria).update(codigo=F("codigo")):
        raise ValidationError("Solo la educadora del curso puede decidir el nivel.")


def _invalidar_listas(nino_id, nucleo_id):
    PropuestaNivel.objects.filter(nino_id=nino_id, nucleo_id=nucleo_id, estado=PropuestaNivel.Estado.LISTA).update(
        estado=PropuestaNivel.Estado.OBSOLETA, actualizada=timezone.now(),
    )


@transaction.atomic
def fijar_nivel_manual(nino, nucleo, usuaria, *, nivel, comentario, hoy):
    """Guarda el nivel independiente y retira sugerencias basadas en el historial anterior."""
    _bloquear_nino_que_valida(nino.pk, usuaria)
    validacion = NivelValidado.objects.create(nino=nino, nucleo=nucleo, nivel=nivel, fecha=hoy,
                                              validado_por=usuaria, comentario=comentario)
    _invalidar_listas(nino.pk, nucleo.pk)
    return validacion


def resolver_propuesta(propuesta, usuaria, *, accion, nivel=None, comentario=""):
    """Decide una vez y conserva la sugerencia original. No realiza llamadas al modelo.

    La obsolescencia se confirma antes de devolver el error al formulario; lanzar
    la excepción dentro del bloque atómico desharía esa invalidación.
    """
    estados = {"aceptar": PropuestaNivel.Estado.ACEPTADA, "ajustar": PropuestaNivel.Estado.AJUSTADA,
               "rechazar": PropuestaNivel.Estado.RECHAZADA}
    if accion not in estados:
        raise ValidationError("Acción de propuesta desconocida.")
    if not isinstance(comentario, str) or len(comentario) > 500:
        raise ValidationError("El comentario debe ser un texto de hasta 500 caracteres.")
    error_vigencia = ""
    with transaction.atomic():
        _bloquear_nino_que_valida(propuesta.nino_id, usuaria)
        p = PropuestaNivel.objects.select_related("nino__curso", "nucleo").get(pk=propuesta.pk, nino_id=propuesta.nino_id)
        if p.estado in estados.values():
            validacion = NivelValidado.objects.filter(propuesta=p).first()
            if p.estado == estados[accion] and (accion == "rechazar" or (
                validacion is not None and (accion != "ajustar" or validacion.nivel == nivel)
            )):
                return ResolucionPropuesta(p, validacion, False)
            raise ValidationError("La propuesta ya fue resuelta; no se puede cambiar su decisión.")
        if p.estado != PropuestaNivel.Estado.LISTA:
            raise ValidationError("Solo se puede decidir una propuesta lista y vigente.")
        if accion != "rechazar" and (not p.evidencia_suficiente or p.nivel is None):
            raise ValidationError("Faltan observaciones: no se puede validar un nivel desde esta propuesta.")
        try:
            entrada = _capturar_entrada(p.nino, p.nucleo, VERSION_PROMPT)
            vigente = bool(p.huella_entrada) and p.version_prompt == VERSION_PROMPT and p.huella_entrada == entrada.huella
            if accion != "rechazar":
                citadas = set(p.observaciones_citadas.values_list("pk", flat=True))
                vigente = vigente and bool(citadas) and citadas <= {o["id"] for o in entrada.datos["evidencia"]}
        except ErrorPropuesta:
            vigente = False
        if not vigente:
            PropuestaNivel.objects.filter(pk=p.pk, estado=PropuestaNivel.Estado.LISTA).update(
                estado=PropuestaNivel.Estado.OBSOLETA, actualizada=timezone.now(),
            )
            error_vigencia = "La propuesta está desactualizada. Solicita una nueva antes de decidir."
        else:
            elegido = p.nivel if accion == "aceptar" else nivel
            if accion != "rechazar":
                if type(elegido) is not int:
                    raise ValidationError("Elige un nivel entero dentro de la rúbrica.")
                validar_nivel(elegido, p.nino.curso.nivel_educativo)
                if accion == "ajustar" and elegido == p.nivel:
                    raise ValidationError("Elige un nivel diferente o acepta la propuesta original.")
            p.estado, p.resuelta_por, p.resuelta_en = estados[accion], usuaria, timezone.now()
            p.save(update_fields=["estado", "resuelta_por", "resuelta_en", "actualizada"])
            validacion = None
            if accion != "rechazar":
                validacion = NivelValidado.objects.create(nino=p.nino, nucleo=p.nucleo, nivel=elegido,
                                                          fecha=timezone.localdate(), validado_por=usuaria,
                                                          comentario=comentario, propuesta=p)
                _invalidar_listas(p.nino_id, p.nucleo_id)
            return ResolucionPropuesta(p, validacion, True)
    raise ValidationError(error_vigencia)
