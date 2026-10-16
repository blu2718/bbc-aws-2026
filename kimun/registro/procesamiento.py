"""De una captura (nota, foto o audio) a observaciones pendientes (PLAN.md, Tasks 5, 8 y 9, "Flujo de procesamiento").

Lo usa `manage.py procesar_capturas`:

1. `tomar_siguiente()` toma una captura pendiente con una actualización condicional
   (`pendiente` → `procesando`, sumando `intentos`). Si dos procesos van por la misma,
   solo a uno le resulta y el otro sigue con la siguiente.
2. `procesar()` obtiene el texto con `lectura.texto_para_separar()`: la nota tal cual,
   la foto leída con Claude (Task 8) o el audio transcrito con Transcribe, con los
   nombres del curso como vocabulario (Task 9). Luego llama a `separar()`, empareja cada
   nombre con `coincidencia.py` y crea las observaciones en estado pendiente, todo en
   una transacción.
3. Si la lectura o `separar()` fallan, la captura queda en `error` con el motivo (en el
   log y en el admin; a quien registró se le muestra un mensaje genérico); `reintentar()`
   la devuelve a `pendiente` para que se vuelva a tomar. `recuperar_atascadas()` devuelve
   a pendiente las que quedaron atascadas en `procesando` (UMBRAL_PROCESANDO_ATASCADA);
   el worker la llama en cada vuelta.

Solo el proceso de fondo llama a Bedrock y Transcribe: la página de la captura consulta
el estado (`views_registro.estado`), porque una foto puede tardar más que los timeouts web.

Las fotos y los audios no se conservan: apenas se leen, el texto queda en
`texto_extraido` y el archivo se borra. Un reintento después de leerlos usa ese texto y
no vuelve a llamar a Claude ni a Transcribe. Si la lectura falla, el archivo se conserva
para reintentar; si no es una foto o un audio válido, se borra (`lectura.ArchivoInvalido`).
"""
import logging
from datetime import date, timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .coincidencia import emparejar
from .curriculo import leer_curriculo, leer_curriculo_de
from .ia import ErrorSeparacion, ErrorTranscripcion, separar_completo
from .ia.separacion import normalizar_codigo_oa
# frases_del_curso y prefijo_vocabulario se usan también en `preparar_vocabularios`.
from .lectura import ArchivoInvalido, frases_del_curso, prefijo_vocabulario, texto_para_separar  # noqa: F401
from .models import AvisoProteccion, Captura, Efecto, NivelEducativo, Nucleo, ObjetivoAprendizaje, Observacion

logger = logging.getLogger(__name__)

TIPOS_PROCESABLES = (Captura.Tipo.TEXTO, Captura.Tipo.FOTO, Captura.Tipo.AUDIO)
LARGO_NOMBRE_DETECTADO = Observacion._meta.get_field("nombre_detectado").max_length
LARGO_PREGUNTA = 500
# Así queda `nombre_detectado` en las observaciones de algo que hizo todo el curso.
NOMBRE_TODO_EL_CURSO = "todo el curso"
# Una captura que lleva más que esto en "procesando" quedó atascada (el proceso murió a mitad).
# Holgado frente al tiempo máximo de una llamada a Bedrock (90 s por defecto).
UMBRAL_PROCESANDO_ATASCADA = timedelta(minutes=5)


def limite_atascada():
    """Las capturas en "procesando" actualizadas antes de este momento están atascadas."""
    return timezone.now() - UMBRAL_PROCESANDO_ATASCADA


def esta_atascada(captura):
    return captura.estado == Captura.Estado.PROCESANDO and captura.actualizada < limite_atascada()


def _procesables():
    return Captura.objects.filter(tipo__in=TIPOS_PROCESABLES)


def tomar(captura_id):
    """Pasa la captura de pendiente a procesando. True solo para el proceso que la tomó."""
    tomadas = _procesables().filter(pk=captura_id, estado=Captura.Estado.PENDIENTE).update(
        estado=Captura.Estado.PROCESANDO, intentos=F("intentos") + 1, actualizada=timezone.now()
    )
    return tomadas == 1


def tomar_siguiente():
    """La captura pendiente más antigua, ya tomada por este proceso; None si no queda ninguna."""
    while True:
        pk = (
            _procesables().filter(estado=Captura.Estado.PENDIENTE)
            .order_by("creada", "pk").values_list("pk", flat=True).first()
        )
        if pk is None:
            return None
        if tomar(pk):
            return Captura.objects.select_related("curso").get(pk=pk)
        # Otro proceso la tomó entre la consulta y la actualización: se busca la siguiente.


def reintentar(captura):
    """Devuelve a pendiente una captura con error. El motivo se mantiene hasta que se vuelva a tomar."""
    return _procesables().filter(pk=captura.pk, estado=Captura.Estado.ERROR).update(
        estado=Captura.Estado.PENDIENTE, actualizada=timezone.now()
    ) == 1


def recuperar_atascadas():
    """Devuelve a pendiente las capturas atascadas en procesando. Devuelve cuántas.

    Una captura queda atascada si el proceso murió a mitad (reinicio del servicio, OOM):
    lleva más de UMBRAL_PROCESANDO_ATASCADA en "procesando". Las que están en proceso
    hace menos que eso no se tocan. `procesar_capturas` la llama en cada vuelta.
    """
    ahora = timezone.now()
    atascadas = _procesables().filter(
        estado=Captura.Estado.PROCESANDO, actualizada__lt=ahora - UMBRAL_PROCESANDO_ATASCADA
    ).update(estado=Captura.Estado.PENDIENTE, actualizada=ahora)
    if atascadas:
        logger.warning("%s capturas atascadas en procesando vuelven a pendiente", atascadas)
    return atascadas


def reintentar_errores():
    """Devuelve a pendiente las capturas procesables con error y las atascadas en procesando. Devuelve cuántas."""
    errores = _procesables().filter(estado=Captura.Estado.ERROR).update(
        estado=Captura.Estado.PENDIENTE, actualizada=timezone.now()
    )
    return errores + recuperar_atascadas()


def _descartada_como_vulneracion(captura):
    """True si la educadora o la directora ya dijeron "No es una vulneración": se procesa normal."""
    return AvisoProteccion.objects.filter(captura=captura, estado=AvisoProteccion.Estado.NO_ES).exists()


def _poner_en_resguardo(captura, senal):
    """La captura queda en resguardo, sin observaciones ni pregunta, y con un aviso pendiente (Task 13).

    Si quedaban observaciones de un procesamiento anterior, se descartan. En el log va
    solo el id: el texto de la nota nunca se escribe en los registros.
    """
    with transaction.atomic():
        Observacion.todas.filter(captura=captura).update(
            estado=Observacion.Estado.DESCARTADA, actualizada=timezone.now()
        )
        aviso, creado = AvisoProteccion.objects.get_or_create(captura=captura, defaults={"senal": senal})
        if not creado and aviso.estado == AvisoProteccion.Estado.PENDIENTE:
            aviso.senal = senal
            aviso.save(update_fields=["senal"])
        # Un aviso ya resuelto no se reabre: quién lo resolvió y cuándo queda registrado.
        captura.estado = Captura.Estado.EN_RESGUARDO
        captura.error = ""
        captura.pregunta = ""
        captura.save(update_fields=["estado", "error", "pregunta", "actualizada"])
    logger.info("Captura %s queda en resguardo con un aviso de protección", captura.pk)


def _marcar_error(captura, motivo):
    captura.estado = Captura.Estado.ERROR
    captura.error = motivo
    captura.save(update_fields=["estado", "error", "actualizada"])


def _crear_observaciones(captura, separada, ninos, nucleos, oas):
    """Las observaciones de una observación separada: una, o una por niño si fue todo el curso.

    "Todos bailaron" cuenta en la ficha de cada niño del curso, con la misma cita.
    Las notas grupales de contexto ("bajó la asistencia") quedan como una sola, sin niño.
    """
    if not separada.get("todo_el_curso"):
        return [_crear_observacion(captura, separada, ninos, nucleos, oas)]
    return [
        _crear_observacion(captura, separada | {"nombre_detectado": NOMBRE_TODO_EL_CURSO}, ninos, nucleos, oas, nino=nino)
        for nino in ninos
    ]


def _crear_observacion(captura, separada, ninos, nucleos, oas, nino=None):
    grupal = separada["grupal"]
    nombre = (separada["nombre_detectado"] or "")[:LARGO_NOMBRE_DETECTADO]
    if not grupal and nino is None:
        # Las notas grupales son contexto del curso: nunca se asignan a un niño.
        coincidencia = emparejar(nombre, ninos)
        nino = coincidencia.nino
        if nino is None:
            logger.info("Captura %s: «%s» queda sin niño (%s)", captura.pk, nombre, coincidencia.razon)
    obs = Observacion.objects.create(
        captura=captura,
        nino=nino,
        nombre_detectado=nombre,
        fecha=date.fromisoformat(separada["fecha"]),
        cita=separada["cita_literal"],
        interpretacion=separada["interpretacion"] or "",
        apoyo=separada["apoyo"],
        efecto=separada.get("efecto") or Efecto.SIN_DATO,
        grupal=grupal,
        estado=Observacion.Estado.PENDIENTE,
    )
    obs.nucleos.set([nucleos[s] for s in separada["nucleos"] if s in nucleos])
    encontrados = []
    for codigo in separada["oas"]:
        oa = oas.get(normalizar_codigo_oa(codigo) or codigo)
        if oa is None:
            logger.warning("Captura %s: el OA %r no está en la base de datos, se omite", captura.pk, codigo)
        else:
            encontrados.append(oa)
    obs.oas.set(encontrados)
    return obs


def _catalogo_del_curso(curso, catalogo=None):
    """El catálogo de OA del nivel educativo del curso.

    Se usa el que se pasa (el proceso de fondo lo lee una vez) solo si es del mismo
    nivel: una nota de sala cuna nunca se etiqueta con OA de Transición.
    """
    nivel = curso.nivel_educativo
    if catalogo is not None and catalogo.get("nivel_educativo", NivelEducativo.TRANSICION) == nivel:
        return catalogo
    return leer_curriculo_de(nivel)


def procesar(captura, cliente=None, catalogo=None, transcriptor=None):
    """Separa una captura ya tomada y crea sus observaciones pendientes.

    Las fotos se leen antes con `cliente` y los audios se transcriben con `transcriptor`
    (por defecto, `ClienteTranscribe()`); en ambos casos el archivo se borra después.
    Devuelve la lista de observaciones creadas (puede ser vacía si la nota no
    describe ninguna), o None si la captura quedó en error.
    """
    curso = captura.curso
    ninos = list(curso.ninos.all())
    try:
        # La foto o el audio se leen aquí (el texto se guarda y el archivo se borra); una nota se usa tal cual.
        texto = texto_para_separar(captura, cliente=cliente, transcriptor=transcriptor, ninos=ninos)
        separacion = separar_completo(
            texto,
            # Fecha local, para que "ayer" se resuelva según la zona del jardín.
            timezone.localdate(captura.creada),
            [n.nombre for n in ninos],
            _catalogo_del_curso(curso, catalogo),
            cliente=cliente,
            # Si ya dijeron "No es una vulneración", no se vuelve a preguntar: con el mismo
            # prompt el modelo la marcaría de nuevo y la nota quedaría sin observaciones.
            revisar_vulneracion=not _descartada_como_vulneracion(captura),
        )
        if separacion.senal is not None:
            _poner_en_resguardo(captura, separacion.senal)
            return []
        separadas, pregunta = separacion.observaciones, separacion.pregunta
        nucleos = {n.sigla: n for n in Nucleo.objects.all()}
        oas = {
            oa.codigo: oa
            for oa in ObjetivoAprendizaje.objects.filter(nivel_educativo=curso.nivel_educativo).select_related("nucleo")
        }
        with transaction.atomic():
            creadas = [obs for s in separadas for obs in _crear_observaciones(captura, s, ninos, nucleos, oas)]
            captura.estado = Captura.Estado.PROCESADA
            captura.error = ""
            captura.pregunta = (pregunta or "")[:LARGO_PREGUNTA]
            captura.save(update_fields=["estado", "error", "pregunta", "actualizada"])
    except (ErrorSeparacion, ErrorTranscripcion) as error:
        logger.warning("Captura %s quedó con error: %s", captura.pk, error)
        _marcar_error(captura, str(error))
        return None
    except ArchivoInvalido as error:
        # Sin archivo, o no es una foto o un audio aceptado (ya se borró): reintentar no lo arregla.
        logger.warning("Captura %s: el archivo no se puede leer: %s", captura.pk, error)
        _marcar_error(captura, f"Archivo inválido: {error}")
        return None
    except Exception as error:
        # Un error inesperado no debe dejar la captura en "procesando" para siempre.
        logger.exception("Error inesperado al procesar la captura %s", captura.pk)
        _marcar_error(captura, f"Error inesperado: {error}")
        return None
    return creadas


def procesar_pendientes(cliente=None, catalogo=None, transcriptor=None):
    """Toma y procesa capturas hasta que no quede ninguna pendiente. Entrega (captura, resultado)."""
    if catalogo is None:
        catalogo = leer_curriculo()
    while (captura := tomar_siguiente()) is not None:
        yield captura, procesar(captura, cliente=cliente, catalogo=catalogo, transcriptor=transcriptor)


def reintentar_desde_la_pagina(captura):
    """Devuelve a pendiente una captura con error o atascada en procesando. True si cambió."""
    if esta_atascada(captura):
        return _procesables().filter(
            pk=captura.pk, estado=Captura.Estado.PROCESANDO,
            actualizada=captura.actualizada, intentos=captura.intentos,
        ).update(
            estado=Captura.Estado.PENDIENTE, actualizada=timezone.now()
        ) == 1
    return reintentar(captura)
