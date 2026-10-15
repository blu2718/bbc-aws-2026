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
   la devuelve a `pendiente` para que se vuelva a tomar. `reintentar_errores()` además
   recupera las que quedaron atascadas en `procesando` (UMBRAL_PROCESANDO_ATASCADA).

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
from .curriculo import leer_curriculo
from .ia import ErrorSeparacion, ErrorTranscripcion, separar
from .ia.separacion import normalizar_codigo_oa
# frases_del_curso y prefijo_vocabulario se usan también en `preparar_vocabularios`.
from .lectura import ArchivoInvalido, frases_del_curso, prefijo_vocabulario, texto_para_separar  # noqa: F401
from .models import Captura, Nucleo, ObjetivoAprendizaje, Observacion

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
