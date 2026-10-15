"""Emparejamiento de nombres detectados con los niños del curso (PLAN.md, Task 5)."""
import pytest

from registro.coincidencia import (
    AMBIGUO,
    APROXIMADA,
    DESCONOCIDO,
    EXACTA,
    UMBRAL_POR_DEFECTO,
    emparejar,
    normalizar,
)
from registro.models import Curso, Nino

# El fixture de la demo se carga una vez para este módulo (ver test_cargar_demo.py).
from registro.tests.test_cargar_demo import _demo_del_modulo, cargada  # noqa: F401


def _ninos(*nombres_y_alias):
    """Niños sin guardar: el emparejamiento solo mira `nombre` y `alias`."""
    return [Nino(nombre=nombre, alias=list(alias)) for nombre, *alias in nombres_y_alias]


CURSO = _ninos(
    ("Pedro Salinas",),
    ("Emilio Vargas",),
    ("Rubí Contreras",),
    ("Naiara Fuentes",),
    ("Sofía Rojas", "Sofi R"),
    ("Sofía Muñoz", "Sofi M"),
)


def _nombre(nombre_detectado, ninos=CURSO, **kwargs):
    resultado = emparejar(nombre_detectado, ninos, **kwargs)
    return (resultado.nino.nombre if resultado.nino else None), resultado.razon


def test_normaliza_tildes_mayusculas_y_espacios():
    assert normalizar("  SOFÍA   Muñoz ") == "sofia munoz"
    assert normalizar("Rubí\tContreras") == "rubi contreras"
    assert normalizar(None) == ""


@pytest.mark.parametrize("escrito", ["Pedro", "pedro", " PEDRO ", "Pedro Salinas", "pedro   salinas"])
def test_nombre_de_pila_o_completo_coinciden_exacto(escrito):
    assert _nombre(escrito) == ("Pedro Salinas", EXACTA)


def test_sin_tilde_coincide_exacto():
    assert _nombre("Rubi") == ("Rubí Contreras", EXACTA)


def test_naiara_y_nayara_son_la_misma_nina_por_comparacion_aproximada():
    """Sin alias cargado: "Nayara" queda sobre el umbral frente a "Naiara"."""
    assert _nombre("Naiara") == ("Naiara Fuentes", EXACTA)
    assert _nombre("Nayara") == ("Naiara Fuentes", APROXIMADA)


def test_naiara_y_nayara_son_la_misma_nina_por_alias():
    ninos = _ninos(("Naiara Fuentes", "Nayara"), ("Pedro Salinas",))
    assert _nombre("Nayara", ninos) == ("Naiara Fuentes", EXACTA)
    assert emparejar("Nayara", ninos).nino is emparejar("Naiara", ninos).nino


def test_sofia_es_ambigua_porque_hay_dos():
    resultado = emparejar("Sofía", CURSO)
    assert resultado.nino is None and resultado.razon == AMBIGUO
    assert {n.nombre for n in resultado.candidatos} == {"Sofía Rojas", "Sofía Muñoz"}
    assert _nombre("sofia") == (None, AMBIGUO)


def test_el_alias_o_el_apellido_resuelven_la_ambiguedad():
    assert _nombre("Sofi R") == ("Sofía Rojas", EXACTA)
    assert _nombre("Sofia Munoz") == ("Sofía Muñoz", EXACTA)


def test_aproximada_con_mas_de_un_candidato_es_ambigua():
    assert _nombre("Sofi") == (None, AMBIGUO)


@pytest.mark.parametrize("escrito", ["Florencia", "Juan", "", None])
def test_un_nombre_desconocido_queda_sin_nino(escrito):
    assert _nombre(escrito) == (None, DESCONOCIDO)


def test_el_umbral_se_puede_configurar(settings):
    assert _nombre("Nayara", umbral=0.9) == (None, DESCONOCIDO)
    settings.COINCIDENCIA_UMBRAL = 0.9
    assert _nombre("Nayara") == (None, DESCONOCIDO)
    settings.COINCIDENCIA_UMBRAL = UMBRAL_POR_DEFECTO
    assert _nombre("Nayara") == ("Naiara Fuentes", APROXIMADA)


# --- Con el curso de la demo ---------------------------------------------------------------


def test_en_la_demo_nayara_es_naiara_y_sofia_es_ambigua(cargada):
    ninos = list(Curso.objects.get(nombre="Transición Mayor A").ninos.all())
    assert _nombre("Nayara", ninos) == ("Naiara Fuentes", EXACTA)
    assert _nombre("Naiara", ninos) == ("Naiara Fuentes", EXACTA)
    assert _nombre("Sofía", ninos) == (None, AMBIGUO)
    assert _nombre("Florencia", ninos) == (None, DESCONOCIDO)
