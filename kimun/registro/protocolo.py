"""Protocolo de protección de derechos que muestra el aviso (PLAN.md, Task 13).

Los pasos, su fuente y quién recibe el aviso viven en `datos/protocolo_proteccion.json`,
no en el código: cuando Integra entregue su protocolo (pregunta 9), se reemplaza ese
archivo. Hoy es provisorio, a partir de los protocolos públicos de la JUNJI.

Si el archivo falta o está mal formado, la app no se cae: usa pasos mínimos
(informar a la directora y no interrogar al niño) y avisa en el log.
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

RUTA_PROTOCOLO = Path(settings.DATOS_DIR) / "protocolo_proteccion.json"
DESTINATARIOS_VALIDOS = ("educadora", "directora")


@dataclass(frozen=True)
class Paso:
    titulo: str
    texto: str = ""


@dataclass(frozen=True)
class Protocolo:
    pasos: tuple
    fuente: str
    provisorio: bool
    destinatarios: tuple


PROTOCOLO_MINIMO = Protocolo(
    pasos=(
        Paso("Informa a la directora del jardín de inmediato"),
        Paso("No interrogues al niño o niña", "No le preguntes quién, cómo ni cuándo."),
    ),
    fuente="",
    provisorio=True,
    destinatarios=DESTINATARIOS_VALIDOS,
)


def validar(datos):
    """Protocolo a partir del JSON. Lanza ValueError si no sirve."""
    if not isinstance(datos, dict):
        raise ValueError("el protocolo debe ser un objeto JSON")
    pasos = []
    for i, paso in enumerate(datos.get("pasos") or [], start=1):
        titulo = paso.get("titulo", "").strip() if isinstance(paso, dict) else ""
        if not titulo:
            raise ValueError(f"el paso {i} no tiene título")
        pasos.append(Paso(titulo, str(paso.get("texto", "")).strip()))
    if not pasos:
        raise ValueError("el protocolo no trae pasos")
    destinatarios = tuple(d for d in datos.get("destinatarios") or [] if d in DESTINATARIOS_VALIDOS)
    if not destinatarios:
        # El aviso nunca puede quedar sin nadie que lo vea.
        raise ValueError(f"destinatarios debe incluir al menos uno de {DESTINATARIOS_VALIDOS}")
    return Protocolo(tuple(pasos), str(datos.get("fuente", "")).strip(), bool(datos.get("provisorio", True)), destinatarios)


def leer_protocolo(ruta=None):
    """El protocolo vigente. Se lee en cada llamada: es un archivo chico y así un cambio se ve sin reiniciar."""
    ruta = Path(ruta or RUTA_PROTOCOLO)
    try:
        return validar(json.loads(ruta.read_text(encoding="utf-8")))
    except (OSError, ValueError) as error:
        logger.error("No se pudo leer el protocolo de protección (%s): %s. Se usan los pasos mínimos.", ruta, error)
        return PROTOCOLO_MINIMO
