"""Nivel esperado, brechas, datos desactualizados y distribución del curso (PLAN.md, Task 2)."""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from registro.alertas import (
    Brecha,
    EstadoDatos,
    Gravedad,
    calcular_tabla,
    distribucion,
    estado_datos,
    gravedad,
    mediana,
    nivel_esperado,
    semestre_de_permanencia,
    tabla_del_curso,
)
from registro.models import (
    Captura,
    Curso,
    MetaSemestre,
    NivelEducativo,
    NivelValidado,
    Nino,
    Nucleo,
    ObjetivoAprendizaje,
    Observacion,
    Rubrica,
    Semestre,
)

# Semestres de la demo: entre uno y otro hay vacaciones.
SEMESTRES = [
    SimpleNamespace(inicio=date(2025, 7, 28), fin=date(2025, 12, 19)),
    SimpleNamespace(inicio=date(2026, 3, 2), fin=date(2026, 7, 3)),
    SimpleNamespace(inicio=date(2026, 7, 20), fin=date(2026, 12, 18)),
]
METAS = {1: 1, 2: 3, 3: 5, 4: 7}


# --- Semestre de permanencia ---------------------------------------------------------


@pytest.mark.parametrize(
    "ingreso, hoy, esperado",
    [
        (date(2025, 7, 28), date(2025, 7, 28), 1),  # el primer día ya cuenta
        (date(2025, 7, 28), date(2026, 10, 15), 3),
        (date(2026, 3, 2), date(2026, 10, 15), 2),
        (date(2026, 7, 20), date(2026, 10, 15), 1),
    ],
)
def test_semestre_de_permanencia_cuenta_desde_el_de_ingreso_inclusive(ingreso, hoy, esperado):
    assert semestre_de_permanencia(ingreso, hoy, SEMESTRES) == esperado


def test_ingresar_a_mitad_de_semestre_cuenta_ese_semestre_completo():
    assert semestre_de_permanencia(date(2025, 9, 15), date(2025, 9, 16), SEMESTRES) == 1
    assert semestre_de_permanencia(date(2025, 9, 15), date(2026, 10, 15), SEMESTRES) == 3
    # El último día del semestre todavía cuenta como ingreso en ese semestre.
    assert semestre_de_permanencia(date(2025, 12, 19), date(2026, 3, 2), SEMESTRES) == 2


def test_en_vacaciones_se_mantiene_el_ultimo_semestre_cursado():
    assert semestre_de_permanencia(date(2025, 7, 28), date(2026, 1, 20), SEMESTRES) == 1
    assert semestre_de_permanencia(date(2025, 7, 28), date(2026, 7, 10), SEMESTRES) == 2


def test_ingresar_en_vacaciones_parte_en_el_semestre_siguiente():
    # Ingresa en enero: su semestre 1 es 2026-1.
    assert semestre_de_permanencia(date(2026, 1, 10), date(2026, 3, 2), SEMESTRES) == 1
    assert semestre_de_permanencia(date(2026, 1, 10), date(2026, 7, 20), SEMESTRES) == 2
    # Mientras siguen las vacaciones, está en su primer semestre.
    assert semestre_de_permanencia(date(2026, 1, 10), date(2026, 1, 20), SEMESTRES) == 1


def test_el_orden_de_los_semestres_no_importa():
    assert semestre_de_permanencia(date(2025, 7, 28), date(2026, 10, 15), list(reversed(SEMESTRES))) == 3


def test_sin_semestres_no_hay_semestre_de_permanencia():
    assert semestre_de_permanencia(date(2025, 7, 28), date(2026, 10, 15), []) is None


# --- Nivel esperado ------------------------------------------------------------------


@pytest.mark.parametrize("semestre, esperado", [(1, 1), (2, 3), (3, 5), (4, 7)])
def test_nivel_esperado_sale_de_la_tabla_del_curso(semestre, esperado):
    assert nivel_esperado(semestre, METAS, nivel_maximo=8) == esperado


@pytest.mark.parametrize("semestre", [5, 6, 10])
def test_despues_de_la_tabla_se_espera_el_maximo_de_la_rubrica(semestre):
    assert nivel_esperado(semestre, METAS, nivel_maximo=8) == 8
    assert nivel_esperado(semestre, METAS, nivel_maximo=9) == 9


def test_un_semestre_sin_meta_usa_la_meta_anterior():
    assert nivel_esperado(3, {1: 1, 2: 3, 4: 7}, nivel_maximo=8) == 3


def test_la_meta_no_supera_el_maximo_de_la_rubrica():
    assert nivel_esperado(4, {1: 1, 4: 9}, nivel_maximo=8) == 8


def test_sin_tabla_o_sin_semestre_no_hay_nivel_esperado():
    assert nivel_esperado(2, {}, nivel_maximo=8) is None
    assert nivel_esperado(None, METAS, nivel_maximo=8) is None


def test_antes_de_la_primera_meta_se_espera_el_nivel_1():
    assert nivel_esperado(1, {2: 3}, nivel_maximo=8) == 1


# --- Mediana y brechas -----------------------------------------------------------------


def test_mediana_con_cantidad_impar():
    assert mediana([5, 1, 4]) == 4


def test_mediana_con_cantidad_par_promedia_los_dos_centrales():
    assert mediana([2, 5, 4, 6]) == 4.5
    assert mediana([4, 6]) == 5


def test_mediana_con_un_solo_nino_es_su_nivel():
    assert mediana([3]) == 3


def test_mediana_ignora_los_vacios_y_sin_datos_no_hay_mediana():
    assert mediana([None, 2, 4, None]) == 3
    assert mediana([]) is None
    assert mediana([None]) is None


@pytest.mark.parametrize(
    "valor, esperada",
    [
        (-2, Gravedad.NORMAL),  # sobre la referencia
        (0, Gravedad.NORMAL),
        (1, Gravedad.NORMAL),
        (1.5, Gravedad.NORMAL),
        (2, Gravedad.AVISO),
        (2.5, Gravedad.ALERTA),
        (3, Gravedad.ALERTA),
        (None, Gravedad.NORMAL),
    ],
)
def test_gravedad_de_la_brecha(valor, esperada):
    assert gravedad(valor) == esperada


def test_brecha_2_es_aviso_y_3_es_alerta_con_texto_de_sugerencia():
    aviso = Brecha.calcular(referencia=5, nivel=3, contra=Brecha.ESPERADO)
    alerta = Brecha.calcular(referencia=5, nivel=2, contra=Brecha.ESPERADO)
    assert (aviso.valor, aviso.gravedad) == (2, Gravedad.AVISO)
    assert (alerta.valor, alerta.gravedad) == (3, Gravedad.ALERTA)
    assert aviso.texto == "Observar: 2 niveles bajo lo esperado"
    assert alerta.texto == "Revisar: 3 niveles bajo lo esperado"


def test_texto_de_brecha_con_pares_y_mediana_decimal():
    brecha = Brecha.calcular(referencia=4.5, nivel=2, contra=Brecha.PARES)
    assert brecha.texto == "Revisar: 2,5 niveles bajo la mediana del curso"


def test_brecha_normal_o_sin_referencia_no_muestra_texto():
    assert Brecha.calcular(referencia=5, nivel=4, contra=Brecha.ESPERADO).texto == ""
    sin_referencia = Brecha.calcular(referencia=None, nivel=4, contra=Brecha.PARES)
    assert (sin_referencia.valor, sin_referencia.texto) == (None, "")


# --- Datos desactualizados -----------------------------------------------------------


def test_14_dias_esta_al_dia_y_15_esta_desactualizado():
    hoy = date(2026, 10, 15)
    assert estado_datos(hoy - timedelta(days=14), hoy) == EstadoDatos.AL_DIA
    assert estado_datos(hoy - timedelta(days=15), hoy) == EstadoDatos.DESACTUALIZADO
    assert estado_datos(hoy, hoy) == EstadoDatos.AL_DIA


def test_sin_observaciones_es_sin_datos():
    assert estado_datos(None, date(2026, 10, 15)) == EstadoDatos.SIN_DATOS


# --- Distribución -----------------------------------------------------------------------


def test_distribucion_cuenta_ninos_por_nivel_y_marca_el_mas_frecuente():
    d = distribucion([1, 3, 3, 5, None], nivel_maximo=8)
    assert d.conteos == [(1, 1), (2, 0), (3, 2), (4, 0), (5, 1), (6, 0), (7, 0), (8, 0)]
    assert d.mas_frecuentes == (3,)


def test_distribucion_con_empate_muestra_todos_los_niveles_empatados():
    assert distribucion([2, 2, 5, 5, 4], nivel_maximo=8).mas_frecuentes == (2, 5)


def test_distribucion_con_9_niveles_y_sin_ninos():
    d = distribucion([], nivel_maximo=9)
    assert [nivel for nivel, _ in d.conteos] == list(range(1, 10))
    assert d.mas_frecuentes == ()


def test_distribucion_no_pierde_un_nivel_sobre_el_maximo():
    """Si la rúbrica se achicó después de validar un nivel, la columna sigue apareciendo."""
    d = distribucion([9, 2], nivel_maximo=8)
    assert d.conteos[-1] == (9, 1)


# --- Tabla del curso (sin base de datos) ------------------------------------------------


def _nucleos(cantidad):
    return [SimpleNamespace(pk=i, sigla=f"N{i}", nombre=f"Núcleo {i}") for i in range(1, cantidad + 1)]


def test_tabla_con_10_nucleos_y_9_niveles_sin_cambiar_codigo():
    hoy = date(2026, 10, 15)
    nucleos = _nucleos(10)
    ninos = [SimpleNamespace(pk=i, nombre=f"Niño {i}", fecha_ingreso=date(2025, 7, 28)) for i in range(1, 6)]
    # Todos en 7 en todos los núcleos, salvo el niño 5 en el núcleo 10, que va en 4.
    niveles = {(n.pk, k.pk): 7 for n in ninos for k in nucleos}
    niveles[(5, 10)] = 4
    metas = {1: 1, 2: 3, 3: 6, 4: 8}

    tabla = calcular_tabla(ninos, nucleos, niveles, {}, metas, SEMESTRES, nivel_maximo=9, hoy=hoy)

    assert tabla.niveles == list(range(1, 10))
    assert [d.nucleo.sigla for d in tabla.distribuciones] == [f"N{i}" for i in range(1, 11)]
    assert tabla.distribuciones[9].conteos[3] == (4, 1)
    fila = tabla.filas[4]
    assert (fila.semestre, fila.nivel_esperado) == (3, 6)
    assert len(fila.celdas) == 10
    celda = fila.celdas[9]
    assert (celda.pares.valor, celda.pares.gravedad) == (3, Gravedad.ALERTA)
    assert (celda.esperado.valor, celda.esperado.gravedad) == (2, Gravedad.AVISO)
    assert celda.gravedad == Gravedad.ALERTA
    # Al pasar el semestre 4 se espera el máximo de esta rúbrica: 9.
    tabla_2027 = calcular_tabla(ninos, nucleos, niveles, {}, metas, SEMESTRES + [
        SimpleNamespace(inicio=date(2027, 3, 1), fin=date(2027, 7, 2)),
        SimpleNamespace(inicio=date(2027, 7, 19), fin=date(2027, 12, 17)),
    ], nivel_maximo=9, hoy=date(2027, 8, 1))
    assert tabla_2027.filas[0].nivel_esperado == 9


def test_tabla_marca_datos_desactualizados_y_sin_datos_por_nucleo():
    hoy = date(2026, 10, 15)
    nucleos = _nucleos(3)
    nino = SimpleNamespace(pk=1, nombre="Pedro", fecha_ingreso=date(2026, 3, 2))
    ultimas = {(1, 1): hoy - timedelta(days=3), (1, 2): hoy - timedelta(days=20)}

    tabla = calcular_tabla([nino], nucleos, {(1, 1): 3, (1, 2): 3, (1, 3): 3}, ultimas, METAS, SEMESTRES, 8, hoy)

    al_dia, viejo, sin = tabla.filas[0].celdas
    assert (al_dia.datos, al_dia.texto_datos) == (EstadoDatos.AL_DIA, "")
    assert (viejo.datos, viejo.texto_datos) == (EstadoDatos.DESACTUALIZADO, "Datos de hace 20 días")
    assert (sin.datos, sin.texto_datos) == (EstadoDatos.SIN_DATOS, "Sin datos")


def test_tabla_con_un_solo_nino_no_lo_compara_consigo_mismo_como_rezagado():
    nucleos = _nucleos(1)
    nino = SimpleNamespace(pk=1, nombre="Pedro", fecha_ingreso=date(2025, 7, 28))
    tabla = calcular_tabla([nino], nucleos, {(1, 1): 1}, {}, METAS, SEMESTRES, 8, date(2026, 10, 15))
    celda = tabla.filas[0].celdas[0]
    assert (celda.pares.valor, celda.pares.gravedad) == (0, Gravedad.NORMAL)
    # Igual queda bajo lo esperado (semestre 3, se espera 5).
    assert celda.esperado.texto == "Revisar: 4 niveles bajo lo esperado"


def test_tabla_muestra_el_nombre_del_nivel_cuando_la_rubrica_lo_trae():
    nucleos = _nucleos(2)
    nino = SimpleNamespace(pk=1, nombre="Pedro", fecha_ingreso=date(2025, 7, 28))
    tabla = calcular_tabla(
        [nino], nucleos, {(1, 1): 3, (1, 2): 3}, {}, METAS, SEMESTRES, 8, date(2026, 10, 15),
        nombres={"N1": {3: "Desarrollando"}},
    )
    assert [c.texto_nivel for c in tabla.filas[0].celdas] == ["3 · Desarrollando", "3"]
    assert tabla.distribuciones[0].texto_mas_frecuentes == "3 · Desarrollando"


# --- Tabla del curso (con la base de datos) ----------------------------------------------


@pytest.fixture
def semestres(db):
    for i, s in enumerate(SEMESTRES):
        Semestre.objects.create(nombre=f"S{i}", inicio=s.inicio, fin=s.fin)


@pytest.fixture
def metas(curso):
    for semestre, nivel in METAS.items():
        MetaSemestre.objects.create(curso=curso, semestre_permanencia=semestre, nivel_esperado=nivel)


def _validar(nino, sigla, nivel, fecha):
    return NivelValidado.objects.create(nino=nino, nucleo=Nucleo.objects.get(sigla=sigla), nivel=nivel, fecha=fecha)


def test_tabla_del_curso_usa_el_ultimo_nivel_validado(curso, nucleos, semestres, metas):
    nino = Nino.objects.create(curso=curso, nombre="Pedro", fecha_ingreso=date(2025, 7, 28))
    _validar(nino, "LV", 4, date(2026, 7, 3))
    _validar(nino, "LV", 2, date(2026, 9, 30))

    tabla = tabla_del_curso(curso, hoy=date(2026, 10, 15))

    lv = tabla.filas[0].celdas[[n.sigla for n in tabla.nucleos].index("LV")]
    assert lv.nivel == 2
    assert lv.esperado.texto == "Revisar: 3 niveles bajo lo esperado"


def test_un_nino_bajo_sus_pares_genera_alerta_solo_en_ese_nucleo(curso, nucleos, semestres, metas):
    ninos = [Nino.objects.create(curso=curso, nombre=f"N{i}", fecha_ingreso=date(2025, 7, 28)) for i in range(5)]
    for n in ninos:
        for sigla in ("IA", "LV", "PM"):
            _validar(n, sigla, 5, date(2026, 9, 30))
    _validar(ninos[0], "LV", 2, date(2026, 10, 1))

    tabla = tabla_del_curso(curso, hoy=date(2026, 10, 15))

    ia, lv, pm = tabla.filas[0].celdas
    assert lv.pares.texto == "Revisar: 3 niveles bajo la mediana del curso"
    assert ia.gravedad == pm.gravedad == Gravedad.NORMAL
    assert all(c.gravedad == Gravedad.NORMAL for f in tabla.filas[1:] for c in f.celdas)


@pytest.fixture
def observar(curso, educadora):
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="x")

    def crear(nino, fecha, nucleos=(), oas=(), estado=Observacion.Estado.ACEPTADA, grupal=False):
        obs = Observacion.objects.create(captura=captura, nino=nino, fecha=fecha, cita="x", estado=estado, grupal=grupal)
        obs.nucleos.set(nucleos)
        obs.oas.set(oas)
        return obs

    return crear


def test_datos_recientes_cuentan_solo_observaciones_aceptadas_e_individuales(curso, nucleos, semestres, observar):
    ia, lv, pm = nucleos
    hoy = date(2026, 10, 15)
    nino = Nino.objects.create(curso=curso, nombre="Pedro", fecha_ingreso=date(2025, 7, 28))
    observar(nino, hoy - timedelta(days=20), [ia])
    observar(nino, hoy, [ia], estado=Observacion.Estado.PENDIENTE)
    observar(nino, hoy, [ia], estado=Observacion.Estado.DESCARTADA)
    observar(nino, hoy, [lv], grupal=True)
    # Una observación etiquetada solo con un OA cuenta para su núcleo.
    oa = ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=pm, numero=1, texto="x")
    observar(nino, hoy - timedelta(days=2), oas=[oa])

    celdas = tabla_del_curso(curso, hoy=hoy).filas[0].celdas

    assert [c.datos for c in celdas] == [EstadoDatos.DESACTUALIZADO, EstadoDatos.SIN_DATOS, EstadoDatos.AL_DIA]
    assert celdas[0].ultima_observacion == hoy - timedelta(days=20)


def test_tabla_del_curso_con_rubrica_de_9_niveles_y_10_nucleos(db, educadora, jardin, semestres):
    Rubrica.objects.create(nivel_educativo=NivelEducativo.MEDIO, cantidad_niveles=9)
    for i in range(10):
        Nucleo.objects.create(sigla=f"K{i}", nombre=f"Núcleo {i}", orden=i)
    curso = Curso.objects.create(jardin=jardin, nombre="Medio A", nivel_educativo=NivelEducativo.MEDIO, educadora=educadora)
    nino = Nino.objects.create(curso=curso, nombre="Pedro", fecha_ingreso=date(2025, 7, 28))
    _validar(nino, "K9", 9, date(2026, 9, 30))

    tabla = tabla_del_curso(curso, hoy=date(2026, 10, 15))

    assert len(tabla.nucleos) == 10
    assert tabla.niveles == list(range(1, 10))
    assert tabla.distribuciones[9].conteos[-1] == (9, 1)
    assert tabla.filas[0].celdas[9].nivel == 9
    # Sin tabla de metas, no hay nivel esperado ni brecha con lo esperado.
    assert tabla.filas[0].nivel_esperado is None
    assert tabla.filas[0].celdas[0].esperado.texto == ""


def test_tabla_del_curso_hace_pocas_consultas(curso, nucleos, semestres, metas, observar, django_assert_max_num_queries):
    ninos = [Nino.objects.create(curso=curso, nombre=f"N{i}", fecha_ingreso=date(2025, 7, 28)) for i in range(15)]
    for n in ninos:
        observar(n, date(2026, 10, 1), nucleos)
    curso = Curso.objects.get(pk=curso.pk)
    with django_assert_max_num_queries(10):
        tabla = tabla_del_curso(curso, hoy=date(2026, 10, 15))
    assert len(tabla.filas) == 15
