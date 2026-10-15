"""Texto de una captura, listo para separar en observaciones (Tasks 8 y 9).

Es el paso 2 del flujo de procesamiento (PLAN.md): el texto escrito se usa tal cual,
la foto se lee con Claude y el audio se transcribe con Transcribe. El procesador
(`procesar_capturas`) llama a `texto_para_separar` y le pasa el resultado a
`registro.ia.separar`, igual para los tres tipos.

Las fotos y los audios no se conservan: apenas se leen o se transcriben, el texto queda
en `captura.texto_extraido` y el archivo se borra del almacenamiento (S3 o disco).
También se borra si no es una foto o un audio válido, porque nunca se va a poder leer.
Solo queda guardado mientras espera a ser procesado o si la lectura falló y se puede
reintentar. La copia que se sube para Transcribe y su salida las borra
`ia.transcripcion.ClienteTranscribe`.

Como el texto queda guardado antes de separar, si la separación falla y la captura
se reintenta, no hace falta el archivo (ni se vuelve a cobrar la lectura).
"""
import logging

from .ia import ImagenInvalida, transcribir_foto
from .ia.transcripcion import ErrorTranscripcion, formato_audio, frases_vocabulario
from .models import Captura

logger = logging.getLogger(__name__)


class ArchivoInvalido(Exception):
    """La captura no tiene un archivo que se pueda leer. Ya se borró; reintentar no sirve."""


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


def borrar_archivo(captura):
    """Borra el archivo de la captura y deja el campo vacío. True si ya no queda archivo.

    Si el almacenamiento falla (por ejemplo, S3 no responde), lo registra y deja el
    nombre en la captura, para que la siguiente vuelta vuelva a intentar borrarlo.
    """
    if not captura.archivo:
        return True
    nombre = captura.archivo.name
    try:
        captura.archivo.storage.delete(nombre)
    except Exception:
        logger.exception("Captura %s: no se pudo borrar %s; se reintenta en la próxima vuelta", captura.pk, nombre)
        return False
    captura.archivo = ""
    captura.save(update_fields=["archivo", "actualizada"])
    logger.info("Captura %s: archivo borrado después de leerlo", captura.pk)
    return True


# Nombre anterior (Task 8), por compatibilidad.
borrar_foto = borrar_archivo


def _leer_archivo(captura):
    with captura.archivo.open("rb") as archivo:
        return archivo.read()


def _guardar_texto(captura, texto):
    # Primero se guarda el texto y después se borra el archivo: si el borrado falla, el texto no se pierde.
    captura.texto_extraido = texto
    captura.save(update_fields=["texto_extraido", "actualizada"])
    borrar_archivo(captura)
    return texto


def _texto_de_foto(captura, cliente):
    if not captura.archivo:
        raise ArchivoInvalido("La captura no tiene foto.")
    try:
        texto = transcribir_foto(_leer_archivo(captura), cliente=cliente)
    except ImagenInvalida as error:
        borrar_archivo(captura)
        raise ArchivoInvalido(str(error)) from error
    return _guardar_texto(captura, texto)


def _texto_de_audio(captura, transcriptor, ninos):
    if not captura.archivo:
        raise ArchivoInvalido("La captura de audio no tiene archivo.")
    audio = _leer_archivo(captura)
    if formato_audio(audio[:12]) is None:
        borrar_archivo(captura)
        raise ArchivoInvalido("El archivo no está en un formato de audio que Transcribe acepte.")
    if transcriptor is None:
        from .ia import ClienteTranscribe

        transcriptor = ClienteTranscribe()
    texto = transcriptor.transcribir(
        audio,
        id_trabajo=f"kimun-captura-{captura.pk}-{captura.intentos}",
        prefijo_vocabulario=prefijo_vocabulario(captura.curso),
        frases=frases_del_curso(ninos if ninos is not None else captura.curso.ninos.all()),
    )
    return _guardar_texto(captura, texto)


def texto_para_separar(captura, cliente=None, transcriptor=None, ninos=None):
    """Texto de la captura. Una foto o un audio sin leer se leen, se guarda el texto y se borra el archivo.

    - cliente: el de Bedrock, para leer fotos (por defecto, `ClienteBedrock()`).
    - transcriptor: el de Transcribe, para audios (por defecto, `ClienteTranscribe()`).
    - ninos: los del curso, para el vocabulario de Transcribe (por defecto, se consultan).

    Lanza `ArchivoInvalido` (no hay archivo o no es una foto o un audio aceptado; ya se
    borró y reintentar no sirve) o `ErrorTranscripcion` (falló Bedrock o Transcribe; el
    archivo se conserva para reintentar). El texto puede venir vacío si no hay nada legible.
    """
    if captura.tipo == Captura.Tipo.TEXTO:
        return captura.texto_original or captura.texto_extraido
    if captura.texto_extraido.strip():
        borrar_archivo(captura)  # por si el borrado anterior falló
        return captura.texto_extraido
    if captura.tipo == Captura.Tipo.FOTO:
        return _texto_de_foto(captura, cliente)
    if captura.tipo == Captura.Tipo.AUDIO:
        return _texto_de_audio(captura, transcriptor, ninos)
    raise ArchivoInvalido(f"Tipo de captura desconocido: {captura.tipo!r}.")


__all__ = [
    "ArchivoInvalido",
    "ErrorTranscripcion",
    "borrar_archivo",
    "frases_del_curso",
    "prefijo_vocabulario",
    "texto_para_separar",
]
