"""Protocolo de protección de derechos que muestra el aviso (PLAN.md, Task 13).

Cada jardín debe tener su propio protocolo (Circular 860 de la Superintendencia de
Educación). Su directora lo carga en la app (`ProtocoloJardin`) y el aviso muestra esos
pasos. Mientras no lo cargue, el aviso muestra los pasos provisorios de
`datos/protocolo_proteccion.json` (paráfrasis del protocolo público de la JUNJI), que
también quedan como referencia junto al del jardín. Quién recibe el aviso sale del archivo.

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
    del_jardin: object = None  # el ProtocoloJardin, si los pasos vienen del jardín


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


def protocolo_para(jardin):
    """(protocolo a seguir, pasos provisorios de referencia o None).

    Si la directora cargó el protocolo del jardín, se sigue ese y los provisorios quedan
    como referencia. Si no, se siguen los provisorios.
    """
    provisorio = leer_protocolo()
    del_jardin = getattr(jardin, "protocolo_proteccion", None) if jardin is not None else None
    pasos = tuple(Paso(p) for p in del_jardin.lista_de_pasos()) if del_jardin is not None else ()
    if not pasos:
        return provisorio, None
    fuente = del_jardin.nombre_documento or f"Protocolo de {jardin.nombre}"
    return Protocolo(pasos, fuente, False, provisorio.destinatarios, del_jardin), provisorio
