"""Lectura de fotos de notas manuscritas (Task 8).

Funciones puras: no dependen de Django. La foto llega como bytes y vuelve el
texto transcrito tal cual, con `[ilegible]` donde no se pudo leer. Después
ese texto pasa por la misma separación que una nota escrita (`separacion.separar`).

- `detectar_formato(contenido)`: formato de imagen según sus primeros bytes, o None.
- `validar_imagen(contenido)`: formato aceptado por Bedrock y tamaño dentro del límite.
- `transcribir_foto(contenido, cliente=None)`: texto de la foto.
"""

import logging
from pathlib import Path

from .bedrock import ClienteBedrock, ErrorBedrock
# El mismo error que el de los audios (Task 9): la captura queda con error y se puede reintentar.
from .transcripcion import ErrorTranscripcion

logger = logging.getLogger(__name__)

RUTA_PROMPT = Path(__file__).resolve().parent / "prompts" / "transcripcion_foto.md"
NOMBRE_HERRAMIENTA = "registrar_transcripcion"
MENSAJE = "Transcribe la nota de la foto."

# Límite de Converse por imagen: 3,75 MB (docs/investigacion_servicios.md, "Fotos").
# Se usa el valor decimal, que es el más estricto de las dos lecturas posibles.
TAMANO_MAXIMO = 3_750_000
# Formatos que acepta Converse, con la extensión con que se guardan.
EXTENSIONES = {"jpeg": "jpg", "png": "png", "gif": "gif", "webp": "webp"}



class ImagenInvalida(ValueError):
    """El archivo no es una imagen aceptada o pasa del tamaño máximo."""


def detectar_formato(contenido):
    """'jpeg', 'png', 'gif' o 'webp' según la firma del archivo; None si no es ninguno.

    No se confía en la extensión ni en el tipo MIME que manda el navegador.
    """
    cabecera = bytes(contenido[:12])
    if cabecera.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if cabecera.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if cabecera[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP":
        return "webp"
    return None


def mensaje_demasiado_grande(tamano):
    """Mensaje para la usuaria, con coma decimal: "La foto pesa 5,2 MB y el máximo es 3,75 MB..."."""
    pesa = f"{tamano / 1_000_000:.1f}".replace(".", ",")
    maximo = f"{TAMANO_MAXIMO / 1_000_000:.2f}".replace(".", ",")
    return (
        f"La foto pesa {pesa} MB y el máximo es {maximo} MB. "
        "Vuelve a tomarla desde esta página, que la achica antes de subirla."
    )


def validar_imagen(contenido):
    """Devuelve el formato. Lanza ImagenInvalida con un mensaje para la usuaria si no sirve."""
    if not contenido:
        raise ImagenInvalida("El archivo está vacío.")
    formato = detectar_formato(contenido)
    if formato is None:
        raise ImagenInvalida("El archivo no es una foto en formato JPEG, PNG, GIF o WebP.")
    if len(contenido) > TAMANO_MAXIMO:
        raise ImagenInvalida(mensaje_demasiado_grande(len(contenido)))
    return formato


def construir_prompt():
    return RUTA_PROMPT.read_text(encoding="utf-8")


def construir_herramienta():
    return {
        "name": NOMBRE_HERRAMIENTA,
        "description": "Registra el texto transcrito de la foto, tal como está escrito.",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "Texto de la nota tal como está escrito, con [ilegible] donde no se pudo leer. Vacío si no hay texto.",
                    },
                },
                "required": ["texto"],
            }
        },
    }


def transcribir_foto(contenido, cliente=None):
    """Texto de la foto, sin espacios sobrantes al inicio ni al final ("" si no tiene texto).

    `cliente` es cualquier objeto con `invocar_herramienta(system, mensaje, herramienta, imagenes)`;
    por defecto, `ClienteBedrock()`. Lanza ImagenInvalida si la foto no sirve (no se
    llama al modelo) y ErrorTranscripcion si la respuesta no se puede usar.
    """
    formato = validar_imagen(contenido)
    if cliente is None:
        cliente = ClienteBedrock()
    try:
        entrada = cliente.invocar_herramienta(
            construir_prompt(), MENSAJE, construir_herramienta(), imagenes=[(formato, bytes(contenido))]
        )
    except ErrorBedrock as error:
        raise ErrorTranscripcion(str(error)) from error
    texto = entrada.get("texto") if isinstance(entrada, dict) else None
    if not isinstance(texto, str):
        raise ErrorTranscripcion("La respuesta no trae el campo 'texto'.")
    texto = texto.strip()
    if not texto:
        logger.info("La foto no tiene texto legible.")
    return texto
