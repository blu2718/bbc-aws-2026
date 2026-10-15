"""Fixtures de los tests de IA. Sin Django, sin base de datos, sin red ni boto3."""

import json
from datetime import date
from pathlib import Path

import pytest

RUTA_CURRICULO = Path(__file__).resolve().parents[4] / "datos" / "curriculo_transicion.json"


class ClienteFalso:
    """Reemplaza a ClienteBedrock: devuelve respuestas predefinidas y guarda las llamadas."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def invocar_herramienta(self, system, mensaje, herramienta):
        self.llamadas.append({"system": system, "mensaje": mensaje, "herramienta": herramienta})
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


@pytest.fixture
def catalogo():
    return json.loads(RUTA_CURRICULO.read_text(encoding="utf-8"))


@pytest.fixture
def catalogo_10_nucleos():
    """Catálogo sintético con otra cantidad de núcleos y siglas inventadas."""
    return {
        "nivel_educativo": "transicion",
        "nucleos": [
            {
                "sigla": f"N{i}",
                "nombre": f"Núcleo sintético {i}",
                "campo_nuevo": "se ignora",
                "oas": [
                    {"numero": j, "codigo": f"OA {j} N{i}", "texto": f"Objetivo {j} del núcleo {i}", "conductas": {}}
                    for j in range(1, 3)
                ],
            }
            for i in range(1, 11)
        ],
    }


@pytest.fixture
def fecha_captura():
    return date(2026, 5, 25)


@pytest.fixture
def nombres_curso():
    return ["Pedro Salinas", "Emilio Vargas", "Rubí Contreras", "Naiara Fuentes", "Sofía Rojas", "Sofía Muñoz"]


@pytest.fixture
def cliente_falso():
    return ClienteFalso


@pytest.fixture
def obs():
    return _obs


def _obs(**campos):
    """Observación cruda como la devolvería el modelo, con valores por defecto."""
    base = {
        "nombre_detectado": "Pedro",
        "fecha": "2026-05-25",
        "cita_literal": "Pedro clasificó las hojas por tamaño",
        "interpretacion": None,
        "nucleos": ["PM"],
        "oas": ["OA 2 PM"],
        "apoyo": "autonomo",
        "grupal": False,
    }
    base.update(campos)
    return base
