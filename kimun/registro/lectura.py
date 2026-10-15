"""Texto de una captura, listo para separar en observaciones (Task 8).

Es el paso 2 del flujo de procesamiento (PLAN.md): el texto escrito se usa tal
cual y la foto se transcribe con Claude. El procesador de la Task 5
(`procesar_capturas`) llama a `texto_para_separar` y le pasa el resultado a
`registro.ia.separar`, igual para texto que para foto.

La foto no se conserva: apenas se lee, el texto queda en `captura.texto_extraido`
y la foto se borra del almacenamiento (S3 o disco). También se borra si el archivo
no es una foto válida, porque nunca se va a poder leer. Solo queda guardada mientras
espera a ser leída o si la lectura falló y se puede reintentar.

Como el texto queda guardado antes de separar, si la separación falla y la captura
se reintenta, no hace falta la foto (ni se vuelve a cobrar la lectura).
"""
import logging

from .ia import ImagenInvalida, transcribir_foto
from .models import Captura

logger = logging.getLogger(__name__)


def borrar_foto(captura):
    """Borra el archivo de la captura y deja el campo vacío. True si ya no queda archivo.

    Si el almacenamiento falla (por ejemplo, S3 no responde), lo registra y deja el
    nombre en la captura, para que la siguiente lectura vuelva a intentar borrarlo.
    """
    if not captura.archivo:
        return True
    nombre = captura.archivo.name
    try:
        captura.archivo.storage.delete(nombre)
    except Exception:
        logger.exception("Captura %s: no se pudo borrar la foto %s; se reintenta en la próxima vuelta", captura.pk, nombre)
        return False
    captura.archivo = ""
    captura.save(update_fields=["archivo", "actualizada"])
    logger.info("Captura %s: foto borrada después de leerla", captura.pk)
    return True


def texto_para_separar(captura, cliente=None):
    """Texto de la captura. Para una foto sin transcribir, la lee, guarda el texto y borra la foto.

    Puede lanzar `ImagenInvalida` (el archivo no es una foto aceptada; ya se borró y
    reintentar no sirve) o `ErrorTranscripcion` (falló Bedrock o su respuesta; la foto
    se conserva para reintentar). El texto puede venir vacío si la foto no tiene nada legible.
    """
    if captura.tipo == Captura.Tipo.TEXTO:
        return captura.texto_original or captura.texto_extraido
    if captura.texto_extraido:
        if captura.tipo == Captura.Tipo.FOTO:
            borrar_foto(captura)  # por si el borrado anterior falló
        return captura.texto_extraido
    if captura.tipo == Captura.Tipo.FOTO:
        if not captura.archivo:
            raise ImagenInvalida("La captura no tiene foto.")
        with captura.archivo.open("rb") as archivo:
            contenido = archivo.read()
        try:
            texto = transcribir_foto(contenido, cliente=cliente)
        except ImagenInvalida:
            borrar_foto(captura)
            raise
        # Primero se guarda el texto y después se borra la foto: si el borrado falla, el texto no se pierde.
        captura.texto_extraido = texto
        captura.save(update_fields=["texto_extraido", "actualizada"])
        borrar_foto(captura)
        return captura.texto_extraido
    raise NotImplementedError(f"La lectura de capturas de tipo {captura.tipo!r} llega con la Task 9.")
