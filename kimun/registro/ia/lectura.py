"""Lectura de la foto de un cuaderno o post-it (PLAN.md, Task 8).

Claude transcribe la foto tal cual, con `[ilegible]` en vez de adivinar. El
texto que sale de aquí pasa después por la misma separación que una nota
escrita (`separacion.separar`).

Funciones puras: no dependen de Django. `cliente` es cualquier objeto con
`invocar_herramienta(system, mensaje, herramienta, imagenes=...)`.
"""

from pathlib import Path

from .bedrock import ClienteBedrock, ErrorBedrock

RUTA_PROMPT = Path(__file__).resolve().parent / "prompts" / "lectura_foto.md"
NOMBRE_HERRAMIENTA = "registrar_transcripcion"
# Formatos de imagen que acepta la API Converse de Bedrock.
FORMATOS = ("jpeg", "png", "gif", "webp")
MENSAJE = "Transcribe el texto de la foto adjunta."


class ErrorLectura(Exception):
    """No se pudo leer la foto. La captura debe quedar con error y poder reintentarse."""


def formato_de_imagen(cabecera):
    """'jpeg', 'png', 'gif' o 'webp' según los primeros bytes del archivo; None si no es una de ellas."""
    if cabecera.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if cabecera.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if cabecera[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP":
        return "webp"
    return None


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
                        "description": "Texto de la foto, sin corregir, con [ilegible] donde no se lee. Vacío si no hay texto.",
                    },
                },
                "required": ["texto"],
            }
        },
    }


def leer_foto(imagen, cliente=None):
    """Texto de la foto (bytes de un JPEG, PNG, GIF o WebP). Puede ser "" si no tiene texto legible."""
    formato = formato_de_imagen(imagen[:16])
    if formato is None:
        raise ErrorLectura("La foto no es JPEG, PNG, GIF ni WebP.")
    if cliente is None:
        cliente = ClienteBedrock()
    try:
        entrada = cliente.invocar_herramienta(
            RUTA_PROMPT.read_text(encoding="utf-8"), MENSAJE, construir_herramienta(), imagenes=[(formato, imagen)]
        )
    except ErrorBedrock as error:
        raise ErrorLectura(str(error)) from error
    texto = entrada.get("texto") if isinstance(entrada, dict) else None
    if not isinstance(texto, str):
        raise ErrorLectura("La respuesta no trae el texto de la foto.")
    return texto.strip()
