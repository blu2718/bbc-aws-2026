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


# --- Resumen de la quincena (PLAN.md, Task 2) -----------------------------------------

from registro.cobertura import Quincena, cobertura_quincena, cobertura_quincena_del_curso, quincena_de  # noqa: E402


@pytest.mark.parametrize(
    "fecha, inicio, fin",
    [
        (date(2026, 10, 1), date(2026, 10, 1), date(2026, 10, 15)),
        (date(2026, 10, 15), date(2026, 10, 1), date(2026, 10, 15)),
        (date(2026, 10, 16), date(2026, 10, 16), date(2026, 10, 31)),
        (date(2026, 10, 31), date(2026, 10, 16), date(2026, 10, 31)),
        (date(2026, 9, 30), date(2026, 9, 16), date(2026, 9, 30)),
        (date(2026, 2, 28), date(2026, 2, 16), date(2026, 2, 28)),
        (date(2028, 2, 29), date(2028, 2, 16), date(2028, 2, 29)),  # año bisiesto
    ],
)
def test_quincena_va_del_1_al_15_y_del_16_a_fin_de_mes(fecha, inicio, fin):
    assert quincena_de(fecha) == Quincena(inicio, fin)


def test_quincena_anterior_y_siguiente_cruzan_meses_y_anios():
    marzo = quincena_de(date(2026, 3, 1))
    assert marzo.anterior() == Quincena(date(2026, 2, 16), date(2026, 2, 28))
    assert marzo.anterior().anterior() == Quincena(date(2026, 2, 1), date(2026, 2, 15))
    assert quincena_de(date(2026, 1, 3)).anterior() == Quincena(date(2025, 12, 16), date(2025, 12, 31))
    assert quincena_de(date(2026, 12, 20)).siguiente() == Quincena(date(2027, 1, 1), date(2027, 1, 15))
    assert quincena_de(date(2026, 10, 15)).siguiente() == Quincena(date(2026, 10, 16), date(2026, 10, 31))


def test_quincena_contiene_sus_bordes():
    q = quincena_de(date(2026, 10, 20))
    assert q.contiene(date(2026, 10, 16)) and q.contiene(date(2026, 10, 31))
    assert not q.contiene(date(2026, 10, 15)) and not q.contiene(date(2026, 11, 1))


def _nucleo(pk, sigla):
    return SimpleNamespace(pk=pk, sigla=sigla)


def test_cobertura_quincena_cuenta_observaciones_y_ninos_por_nucleo():
    lv, pm, ia = _nucleo(1, "LV"), _nucleo(2, "PM"), _nucleo(3, "IA")
    q = quincena_de(date(2026, 10, 1))
    evidencias = [
        # (observación, niño, fecha, núcleo)
        (10, 1, date(2026, 10, 1), 1),
        (10, 1, date(2026, 10, 1), 1),  # la misma observación por núcleo y por OA cuenta una vez
        (11, 1, date(2026, 10, 15), 1),
        (12, 2, date(2026, 10, 3), 1),
        (12, 2, date(2026, 10, 3), 2),
        (13, 3, date(2026, 10, 16), 3),  # fuera de la quincena
        (14, 3, date(2026, 9, 30), 3),  # fuera de la quincena
    ]

    resultado = cobertura_quincena([lv, pm, ia], evidencias, q)

    assert [(c.nucleo.sigla, c.observaciones, c.ninos, c.sin_observaciones) for c in resultado] == [
        ("LV", 3, 2, False),
        ("PM", 1, 1, False),
        ("IA", 0, 0, True),
    ]


def test_cobertura_quincena_del_curso_cuenta_solo_aceptadas_individuales_del_curso(
    curso, nino, otro_nino, nucleos, oas, observar, educadora, jardin
):
    from registro.models import Curso

    ia, lv, pm = nucleos
    q = quincena_de(date(2026, 10, 5))

    def obs(n, fecha, nucleos_obs=(), oas_obs=(), **kw):
        o = observar(n, fecha, oas_obs, **kw)
        o.nucleos.set(nucleos_obs)
        return o

    obs(nino, date(2026, 10, 2), [lv], [oas["LV1"]])
    obs(otro_nino, date(2026, 10, 3), oas_obs=[oas["PM1"]])  # PM sale del OA
    obs(nino, date(2026, 10, 4), [ia], estado=Observacion.Estado.PENDIENTE)
    obs(None, date(2026, 10, 4), [ia], grupal=True)
    obs(nino, date(2026, 10, 16), [ia])  # quincena siguiente
    otro_curso = Curso.objects.create(
        jardin=jardin, nombre="Otro", nivel_educativo=NivelEducativo.TRANSICION, educadora=educadora
    )
    ajeno = Nino.objects.create(curso=otro_curso, nombre="Ajeno", fecha_ingreso=date(2026, 3, 2))
    obs(ajeno, date(2026, 10, 4), [ia])

    resultado = {c.nucleo.sigla: (c.observaciones, c.ninos) for c in cobertura_quincena_del_curso(curso, q)}

    assert resultado == {"IA": (0, 0), "LV": (1, 1), "PM": (1, 1)}
