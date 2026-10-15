"""Formularios y funciones puras de la ficha (Task 3, spec task3-ficha-nino)."""
from types import SimpleNamespace

import pytest

from registro.ficha import descriptores_vecinos, es_provisorio
from registro.forms import METAS_POR_DEFECTO, FijarNivelForm, MetasForm, etiqueta_nivel, nombres_comunes
from registro.models import MetaSemestre


def _desc(nivel, nombre="", provisorio=False, descripcion=""):
    return SimpleNamespace(nivel=nivel, nombre=nombre, provisorio=provisorio, descripcion=descripcion)


def test_etiqueta_con_nombre_solo_si_el_descriptor_es_oficial():
    assert etiqueta_nivel(3, _desc(3, "Desarrollando")) == "3 · Desarrollando"
    assert etiqueta_nivel(3, _desc(3, "Nivel 3", provisorio=True)) == "3"
    assert etiqueta_nivel(3, _desc(3, "")) == "3"
    assert etiqueta_nivel(3, None) == "3"


def test_nombres_comunes_solo_si_todos_los_nucleos_coinciden():
    assert nombres_comunes({}) == {}
    assert nombres_comunes({"IA": {1: "Comenzando", 2: "Explorando"}}) == {1: "Comenzando", 2: "Explorando"}
    resultado = nombres_comunes({
        "IA": {1: "Comenzando", 2: "Explorando", 3: "Desarrollando"},
        "LV": {1: "Comenzando", 2: "Otro"},
    })
    assert resultado == {1: "Comenzando"}


@pytest.mark.parametrize("nivel_maximo", [2, 8, 9])
def test_las_opciones_van_del_1_al_maximo_con_su_descripcion(nivel_maximo):
    descriptores = {1: _desc(1, "Comenzando", descripcion="Uno"), 2: _desc(2, "Nivel 2", True, "Dos")}
    form = FijarNivelForm(prefix="IA", initial={"nivel": 2}, nivel_maximo=nivel_maximo, descriptores=descriptores)
    opciones = form.opciones
    assert [o.valor for o in opciones] == list(range(1, nivel_maximo + 1))
    assert (opciones[0].texto, opciones[0].descripcion) == ("1 · Comenzando", "Uno")
    assert (opciones[1].texto, opciones[1].descripcion, opciones[1].marcada) == ("2", "Dos", True)
    assert [o.marcada for o in opciones].count(True) == 1
    assert all(o.descripcion == "" for o in opciones[2:])


@pytest.mark.parametrize("valor, valido", [
    ("1", True), ("8", True), ("0", False), ("9", False), ("-1", False), ("abc", False), ("", False), ("3.5", False),
])
def test_el_formulario_solo_acepta_niveles_entre_1_y_el_maximo(valor, valido):
    form = FijarNivelForm({"IA-nivel": valor}, prefix="IA", nivel_maximo=8, descriptores={})
    assert form.is_valid() is valido
    if not valido:
        assert "Elige un nivel entre 1 y 8." in form.errors["nivel"]


def test_el_comentario_tiene_un_maximo_de_500():
    datos = {"IA-nivel": "2", "IA-comentario": "x" * 501}
    form = FijarNivelForm(datos, prefix="IA", nivel_maximo=8, descriptores={})
    assert not form.is_valid() and "comentario" in form.errors
    datos["IA-comentario"] = "x" * 500
    assert FijarNivelForm(datos, prefix="IA", nivel_maximo=8, descriptores={}).is_valid()


def test_descriptores_vecinos():
    d = {n: _desc(n) for n in range(1, 9)}
    assert descriptores_vecinos(d, 3, 8) == (d[3], d[4])
    assert descriptores_vecinos(d, 8, 8) == (d[8], None)
    assert descriptores_vecinos(d, None, 8) == (None, None)
    # Rúbrica de 9 niveles con 8 descriptores.
    assert descriptores_vecinos(d, 8, 9) == (d[8], None)
    assert descriptores_vecinos(d, 9, 9) == (None, None)
    # Rúbrica que bajó de 9 a 8 con un descriptor 9 que quedó: en el 8 no hay siguiente.
    assert descriptores_vecinos({**d, 9: _desc(9)}, 8, 8) == (d[8], None)


def test_es_provisorio():
    assert es_provisorio({}) is True
    assert es_provisorio({1: _desc(1), 2: _desc(2)}) is False
    assert es_provisorio({1: _desc(1), 2: _desc(2, provisorio=True)}) is True


def test_metas_muestra_los_valores_por_defecto_y_los_guardados(curso):
    MetaSemestre.objects.create(curso=curso, semestre_permanencia=2, nivel_esperado=4)
    form = MetasForm(curso=curso, nivel_maximo=8, nombres={})
    iniciales = {s: form.fields[f"semestre_{s}"].initial for s in range(1, 5)}
    assert iniciales == {**METAS_POR_DEFECTO, 2: 4}


def test_metas_usa_los_nombres_comunes_en_las_opciones(curso):
    form = MetasForm(curso=curso, nivel_maximo=8, nombres={3: "Desarrollando"})
    opciones = dict(form.fields["semestre_1"].choices)
    assert list(opciones) == list(range(1, 9))
    assert opciones[3] == "3 · Desarrollando" and opciones[4] == "4"
