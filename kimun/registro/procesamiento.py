"""De una captura de texto a observaciones pendientes (PLAN.md, Task 5 y "Flujo de procesamiento").

Lo usa `manage.py procesar_capturas`:

1. `tomar_siguiente()` toma una captura pendiente con una actualización condicional
   (`pendiente` → `procesando`, sumando `intentos`). Si dos procesos van por la misma,
   solo a uno le resulta y el otro sigue con la siguiente.
2. `procesar()` llama a `separar()`, empareja cada nombre con `coincidencia.py` y crea
   las observaciones en estado pendiente, todo en una transacción.
3. Si `separar()` falla, la captura queda en `error` con el motivo (en el log y en el
   admin; a quien registró se le muestra un mensaje genérico); `reintentar()` la
   devuelve a `pendiente` para que se vuelva a tomar. `reintentar_errores()` además
   recupera las que quedaron atascadas en `procesando` (UMBRAL_PROCESANDO_ATASCADA).

Las fotos (Task 8) primero se transcriben con Claude (`ia.lectura.leer_foto`, con
`[ilegible]` en vez de adivinar) y los audios (Task 9) con `ia.transcripcion` (con los
nombres del curso como vocabulario). Lo leído o transcrito queda en `texto_extraido` y
pasa por la misma separación que una nota escrita, junto con lo que se escribió al
adjuntar el archivo. Si después falla la separación, al reintentar no se vuelve a leer
la foto ni a transcribir el audio.

Además del proceso de fondo, la página de cada captura (pantalla II de
diseno-interfaz.jpg) procesa al abrirse los textos y las fotos con
`procesar_si_pendiente()`. La actualización condicional de `tomar()` evita que los dos
procesen la misma. Los audios los procesa solo el proceso de fondo: Transcribe por
lotes puede tardar más que el timeout de gunicorn (60 s) y el de CloudFront (30 s).
"""
import logging
from datetime import date, timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .coincidencia import emparejar
from .curriculo import leer_curriculo
from .ia import ClienteBedrock, ClienteTranscribe, ErrorSeparacion, ErrorTranscripcion, separar
from .ia.lectura import ErrorLectura, leer_foto
from .ia.separacion import normalizar_codigo_oa
from .ia.transcripcion import frases_vocabulario
from .models import Captura, Efecto, Nucleo, ObjetivoAprendizaje, Observacion

logger = logging.getLogger(__name__)

TIPOS_PROCESABLES = (Captura.Tipo.TEXTO, Captura.Tipo.FOTO, Captura.Tipo.AUDIO)
LARGO_NOMBRE_DETECTADO = Observacion._meta.get_field("nombre_detectado").max_length
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


def reintentar_errores():
    """Devuelve a pendiente las capturas procesables con error y las atascadas en procesando.

    Una captura queda atascada si el proceso murió a mitad (reinicio del servicio, OOM):
    lleva más de UMBRAL_PROCESANDO_ATASCADA en "procesando". Las que están en proceso
    hace menos que eso no se tocan. Devuelve cuántas volvieron a pendiente.
    """
    ahora = timezone.now()
    errores = _procesables().filter(estado=Captura.Estado.ERROR).update(
        estado=Captura.Estado.PENDIENTE, actualizada=ahora
    )
    atascadas = _procesables().filter(
        estado=Captura.Estado.PROCESANDO, actualizada__lt=ahora - UMBRAL_PROCESANDO_ATASCADA
    ).update(estado=Captura.Estado.PENDIENTE, actualizada=ahora)
    if atascadas:
        logger.warning("%s capturas atascadas en procesando vuelven a pendiente", atascadas)
    return errores + atascadas


def prefijo_vocabulario(curso):
    """Nombre base del vocabulario de Transcribe del curso (los permisos exigen `kimun-*`)."""
    return f"kimun-curso-{curso.pk}"


def frases_del_curso(ninos):
    """Nombre completo, nombre de pila y apodos de cada niño, listos para el vocabulario."""
    nombres = []
    for nino in ninos:
        nombres.append(nino.nombre)
        nombres.extend(nino.nombre.split()[:1])
        nombres.extend(alias for alias in (nino.alias or []) if isinstance(alias, str))
    return frases_vocabulario(nombres)


def _texto_de_audio(captura, ninos, transcriptor):
    """Transcribe el audio y guarda el texto. Si ya estaba transcrito (reintento), lo reutiliza."""
    if captura.texto_extraido.strip():
        return captura.texto_extraido
    if not captura.archivo:
        raise ErrorTranscripcion("La captura de audio no tiene archivo.")
    with captura.archivo.storage.open(captura.archivo.name, "rb") as archivo:
        audio = archivo.read()
    texto = transcriptor.transcribir(
        audio,
        id_trabajo=f"kimun-captura-{captura.pk}-{captura.intentos}",
        prefijo_vocabulario=prefijo_vocabulario(captura.curso),
        frases=frases_del_curso(ninos),
    )
    captura.texto_extraido = texto
    captura.save(update_fields=["texto_extraido", "actualizada"])
    return texto


def _marcar_error(captura, motivo):
    captura.estado = Captura.Estado.ERROR
    captura.error = motivo
    captura.save(update_fields=["estado", "error", "actualizada"])


def _crear_observacion(captura, separada, ninos, nucleos, oas):
    grupal = separada["grupal"]
    nombre = (separada["nombre_detectado"] or "")[:LARGO_NOMBRE_DETECTADO]
    nino = None
    if not grupal:
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


def _texto_a_separar(captura, ninos, cliente, transcriptor):
    """El texto escrito o, en una foto o un audio, lo leído o transcrito más lo que se escribió al adjuntarlo.

    La foto se lee y el audio se transcribe una sola vez: si la separación falla y se
    reintenta, se reusa `texto_extraido`.
    """
    if captura.tipo == Captura.Tipo.AUDIO:
        _texto_de_audio(captura, ninos, transcriptor or ClienteTranscribe())
    elif captura.tipo == Captura.Tipo.FOTO:
        if not captura.texto_extraido:
            if not captura.archivo:
                raise ErrorLectura("La captura de foto no tiene archivo.")
            with captura.archivo.open("rb") as archivo:
                imagen = archivo.read()
            captura.texto_extraido = leer_foto(imagen, cliente=cliente)
            captura.save(update_fields=["texto_extraido", "actualizada"])
    else:
        return captura.texto_original or captura.texto_extraido
    partes = (captura.texto_extraido, captura.texto_original)
    return "\n\n".join(p.strip() for p in partes if p and p.strip())


def procesar(captura, cliente=None, catalogo=None, transcriptor=None):
    """Separa una captura ya tomada y crea sus observaciones pendientes.

    Los audios se transcriben antes con `transcriptor` (por defecto, `ClienteTranscribe()`).
    Devuelve la lista de observaciones creadas (puede ser vacía si la nota no
    describe ninguna), o None si la captura quedó en error.
    """
    curso = captura.curso
    ninos = list(curso.ninos.all())
    try:
        texto = _texto_a_separar(captura, ninos, cliente, transcriptor)
        separadas = separar(
            texto,
            # Fecha local, para que "ayer" se resuelva según la zona del jardín.
            timezone.localdate(captura.creada),
            [n.nombre for n in ninos],
            catalogo if catalogo is not None else leer_curriculo(),
            cliente=cliente,
        )
        nucleos = {n.sigla: n for n in Nucleo.objects.all()}
        oas = {
            oa.codigo: oa
            for oa in ObjetivoAprendizaje.objects.filter(nivel_educativo=curso.nivel_educativo).select_related("nucleo")
        }
        with transaction.atomic():
            creadas = [_crear_observacion(captura, s, ninos, nucleos, oas) for s in separadas]
            captura.estado = Captura.Estado.PROCESADA
            captura.error = ""
            captura.save(update_fields=["estado", "error", "actualizada"])
    except (ErrorSeparacion, ErrorLectura, ErrorTranscripcion) as error:
        logger.warning("Captura %s quedó con error: %s", captura.pk, error)
        _marcar_error(captura, str(error))
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


def procesar_si_pendiente(captura, cliente=None):
    """Toma y procesa la captura si está pendiente y nadie más la tomó. True si la procesó esta llamada.

    La usa la página de la captura, que espera ahí el resultado de Bedrock. Los audios
    no se toman aquí: Transcribe tarda más que el timeout de la página y los procesa
    el proceso de fondo.
    """
    if captura.tipo == Captura.Tipo.AUDIO or not tomar(captura.pk):
        return False
    captura.refresh_from_db()
    procesar(captura, cliente=cliente or ClienteBedrock())
    return True


def reintentar_desde_la_pagina(captura):
    """Devuelve a pendiente una captura con error o atascada en procesando. True si cambió."""
    if esta_atascada(captura):
        return _procesables().filter(pk=captura.pk, estado=Captura.Estado.PROCESANDO).update(
            estado=Captura.Estado.PENDIENTE, actualizada=timezone.now()
        ) == 1
    return reintentar(captura)
