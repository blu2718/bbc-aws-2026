"""Cobertura de evidencia por OA (PLAN.md, Task 3)."""
from datetime import date
from types import SimpleNamespace

import pytest

from registro.cobertura import agrupar_por_nucleo, cobertura_del_nino, cobertura_por_oa, oas_sin_evidencia
from registro.models import Captura, NivelEducativo, Nino, ObjetivoAprendizaje, Observacion

# --- Funciones puras (sin base de datos) ------------------------------------------


def _oa(pk, sigla="LV"):
    return SimpleNamespace(pk=pk, nucleo=SimpleNamespace(sigla=sigla))


def test_oa_sin_evidencia_queda_en_cero_y_sin_fecha():
    [c] = cobertura_por_oa([_oa(1)], [])
    assert (c.cantidad, c.ultima_fecha, c.sin_evidencia) == (0, None, True)


def test_cuenta_cada_evidencia_y_toma_la_fecha_mas_reciente_aunque_no_venga_ultima():
    evidencias = [(1, date(2026, 5, 10)), (1, date(2026, 9, 1)), (1, date(2026, 3, 1))]
    [c] = cobertura_por_oa([_oa(1)], evidencias)
    assert (c.cantidad, c.ultima_fecha, c.sin_evidencia) == (3, date(2026, 9, 1), False)


def test_respeta_el_orden_de_los_oa_e_ignora_los_que_no_se_muestran():
    oas = [_oa(3), _oa(1), _oa(2)]
    evidencias = [(2, date(2026, 4, 1)), (99, date(2026, 4, 2))]
    resultado = cobertura_por_oa(oas, evidencias)
    assert [(c.oa.pk, c.cantidad) for c in resultado] == [(3, 0), (1, 0), (2, 1)]


def test_oas_sin_evidencia_son_la_sugerencia_de_que_observar():
    oas = [_oa(1), _oa(2), _oa(3)]
    coberturas = cobertura_por_oa(oas, [(2, date(2026, 4, 1))])
    assert [oa.pk for oa in oas_sin_evidencia(coberturas)] == [1, 3]


def test_agrupar_por_nucleo_respeta_el_orden():
    coberturas = cobertura_por_oa([_oa(1, "LV"), _oa(2, "LV"), _oa(3, "PM")], [])
    agrupado = agrupar_por_nucleo(coberturas)
    assert list(agrupado) == ["LV", "PM"]
    assert [c.oa.pk for c in agrupado["LV"]] == [1, 2]


# --- Con la base de datos -----------------------------------------------------------


@pytest.fixture
def nino(curso, nucleos):
    return Nino.objects.create(curso=curso, nombre="Pedro", fecha_ingreso=date(2026, 3, 2))


@pytest.fixture
def otro_nino(curso, nucleos):
    return Nino.objects.create(curso=curso, nombre="Emilio", fecha_ingreso=date(2026, 3, 2))


@pytest.fixture
def oas(nucleos):
    """OA 1 y 2 de LV y OA 1 de PM en Transición. IA queda sin OA a propósito."""
    _ia, lv, pm = nucleos
    crear = ObjetivoAprendizaje.objects.create
    return {
        "LV1": crear(nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, numero=1, texto="x"),
        "LV2": crear(nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, numero=2, texto="x"),
        "PM1": crear(nivel_educativo=NivelEducativo.TRANSICION, nucleo=pm, numero=1, texto="x"),
        # Otro nivel educativo: no debe aparecer en la ficha de un niño de Transición.
        "LV1_medio": crear(nivel_educativo=NivelEducativo.MEDIO, nucleo=lv, numero=1, texto="x"),
    }


@pytest.fixture
def observar(curso, educadora):
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="x")

    def crear(nino, fecha, oas, estado=Observacion.Estado.ACEPTADA, grupal=False):
        obs = Observacion.objects.create(
            captura=captura, nino=nino, fecha=fecha, cita="x", estado=estado, grupal=grupal
        )
        obs.oas.set(oas)
        return obs

    return crear


def _por_codigo(cobertura):
    return {c.oa.codigo: (c.cantidad, c.ultima_fecha) for lista in cobertura.values() for c in lista}


def test_cuenta_solo_las_observaciones_aceptadas_del_nino(nino, otro_nino, oas, observar):
    lv1 = [oas["LV1"]]
    observar(nino, date(2026, 9, 1), lv1)
    observar(nino, date(2026, 10, 5), lv1)
    observar(nino, date(2026, 10, 10), lv1, estado=Observacion.Estado.PENDIENTE)
    observar(nino, date(2026, 10, 12), lv1, estado=Observacion.Estado.DESCARTADA)
    observar(otro_nino, date(2026, 10, 14), lv1)

    assert _por_codigo(cobertura_del_nino(nino))["OA 1 LV"] == (2, date(2026, 10, 5))


def test_una_observacion_con_varios_oa_cuenta_para_cada_uno(nino, oas, observar):
    observar(nino, date(2026, 10, 1), [oas["LV1"], oas["PM1"]])
    resultado = _por_codigo(cobertura_del_nino(nino))
    assert resultado["OA 1 LV"] == (1, date(2026, 10, 1))
    assert resultado["OA 1 PM"] == (1, date(2026, 10, 1))


def test_las_notas_grupales_no_cuentan(nino, oas, observar):
    observar(nino, date(2026, 10, 1), [oas["LV1"]], grupal=True)
    observar(None, date(2026, 10, 2), [oas["LV1"]], grupal=True)
    assert _por_codigo(cobertura_del_nino(nino))["OA 1 LV"] == (0, None)


def test_muestra_todos_los_oa_de_su_nivel_educativo_agrupados_por_nucleo(nino, oas, observar):
    observar(nino, date(2026, 10, 1), [oas["LV2"]])
    cobertura = cobertura_del_nino(nino)

    # IA no tiene OA en Transición en estos datos; el OA de nivel medio no aparece.
    assert list(cobertura) == ["LV", "PM"]
    assert [c.oa.codigo for c in cobertura["LV"]] == ["OA 1 LV", "OA 2 LV"]
    assert [oa.codigo for oa in oas_sin_evidencia(cobertura["LV"])] == ["OA 1 LV"]
    assert [oa.codigo for oa in oas_sin_evidencia(cobertura["PM"])] == ["OA 1 PM"]


def test_la_evidencia_de_otro_nivel_educativo_no_se_mezcla(nino, oas, observar):
    observar(nino, date(2026, 10, 1), [oas["LV1_medio"]])
    assert _por_codigo(cobertura_del_nino(nino))["OA 1 LV"] == (0, None)


def test_la_cantidad_de_consultas_no_crece_con_las_observaciones(nino, oas, observar, django_assert_max_num_queries):
    for dia in range(1, 21):
        observar(nino, date(2026, 10, dia), [oas["LV1"], oas["LV2"], oas["PM1"]])
    nino = Nino.objects.get(pk=nino.pk)  # sin el curso en caché
    with django_assert_max_num_queries(3):
        cobertura = cobertura_del_nino(nino)
    assert _por_codigo(cobertura)["OA 2 LV"] == (20, date(2026, 10, 20))
