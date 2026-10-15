"""Vista del jardín para la directora: comparación de salas del mismo nivel educativo (PLAN.md, Task 12)."""
from datetime import date
from decimal import Decimal
from fractions import Fraction
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from registro.alertas import (
    PROPORCION_MINIMA_VALIDADOS,
    UMBRAL_SALA_BAJO,
    comparar_salas,
    promedio,
    redondear,
    resumen_del_jardin,
)
from registro.models import Curso, Jardin, NivelEducativo, NivelValidado, Nino, Nucleo, Rubrica
from registro.permisos import jardines_que_dirige

LV = SimpleNamespace(pk=1, nombre="Lenguaje Verbal", sigla="LV")
PM = SimpleNamespace(pk=2, nombre="Pensamiento Matemático", sigla="PM")


def _sala(pk, nombre, nivel_educativo=NivelEducativo.TRANSICION):
    return SimpleNamespace(pk=pk, nombre=nombre, nivel_educativo=nivel_educativo)


A, B, C = _sala(1, "Sala A"), _sala(2, "Sala B"), _sala(3, "Sala C")


def _celda(resumen, curso, nucleo):
    for grupo in resumen.grupos:
        for fila in grupo.filas:
            if fila.nucleo.pk == nucleo.pk:
                for celda in fila.celdas:
                    if celda.curso.pk == curso.pk:
                        return celda
    raise LookupError((curso.nombre, nucleo.nombre))


# --- Promedios -----------------------------------------------------------------------------


def test_promedio_exacto_ignorando_vacios():
    assert promedio([4, 5, 6]) == 5
    assert promedio([2, 3]) == Fraction(5, 2)
    assert promedio([5, None]) == 5
    assert promedio([]) is None
    assert promedio([None]) is None


def test_el_promedio_de_cada_sala_se_redondea_a_un_decimal_y_se_muestra_con_coma():
    resumen = comparar_salas([A, B], [LV], {(1, 1): [2, 3], (2, 1): [4, 5, 5]})
    assert _celda(resumen, A, LV).promedio == Decimal("2.5")
    assert _celda(resumen, A, LV).texto_promedio == "2,5"
    assert _celda(resumen, B, LV).promedio == Decimal("4.7")  # 14/3
    assert _celda(resumen, B, LV).texto_promedio == "4,7"
    assert _celda(resumen, B, LV).promedio_demas == Decimal("2.5")
    # Un promedio entero también muestra un decimal, para que se vea que está redondeado.
    resumen = comparar_salas([A], [LV], {(1, 1): [5, 5]})
    assert _celda(resumen, A, LV).texto_promedio == "5,0"


@pytest.mark.parametrize(
    "valor, esperado",
    [
        (Fraction(76, 25), "3.0"),  # 3,04
        (Fraction(61, 20), "3.1"),  # 3,05: la mitad hacia arriba
        (Fraction(59, 20), "3.0"),  # 2,95
        (Fraction(14, 3), "4.7"),
        (Fraction(16, 3), "5.3"),
        (3, "3.0"),
        (Fraction(-1, 20), "-0.1"),  # la mitad lejos del cero, como ROUND_HALF_UP
        (Decimal("2.25"), "2.3"),
    ],
)
def test_redondear_a_un_decimal_con_la_mitad_hacia_arriba(valor, esperado):
    assert str(redondear(valor)) == esperado
    assert redondear(None) is None


# --- Ejemplo de Integra y umbral -------------------------------------------------------------


def test_ejemplo_de_integra_dos_salas_en_6_y_una_en_3():
    niveles = {(1, 1): [6, 6, 6], (2, 1): [6, 5, 7], (3, 1): [3, 3, 3]}
    resumen = comparar_salas([A, B, C], [LV], niveles)

    assert [a.curso.nombre for a in resumen.alertas] == ["Sala C"]
    alerta = resumen.alertas[0]
    assert alerta.texto_alerta == "Revisar: Sala C, 3,0 niveles bajo el resto del jardín en Lenguaje Verbal"
    assert alerta.texto_celda == "Revisar: 3,0 niveles bajo el resto"
    assert not _celda(resumen, A, LV).alerta and _celda(resumen, A, LV).texto_alerta == ""
    assert not _celda(resumen, B, LV).alerta
    assert resumen.umbral == UMBRAL_SALA_BAJO == 2


@pytest.mark.parametrize(
    "niveles_a, niveles_b, niveles_c, umbral, hay_alerta",
    [
        ([5, 5], [5, 5], [3, 3], 2, True),  # justo 2 niveles: dispara
        ([5, 5], [5, 5], [3, 4], 2, False),  # 1,5 niveles: no
        ([5], [5], [3] * 9 + [4], 2, False),  # 3,1: 1,9 niveles, bajo 2: no
        ([6, 5, 5], [6, 5, 5], [3, 4, 3], 2, True),  # 5,3 − 3,3 = 2,0
        ([5, 5], [5, 5], [3, 3], 3, False),  # umbral configurable
        ([5, 5], [5, 5], [4, 4], 1, True),
    ],
)
def test_umbral_en_el_borde(niveles_a, niveles_b, niveles_c, umbral, hay_alerta):
    niveles = {(1, 1): niveles_a, (2, 1): niveles_b, (3, 1): niveles_c}
    resumen = comparar_salas([A, B, C], [LV], niveles, umbral=umbral)
    assert _celda(resumen, C, LV).alerta is hay_alerta
    assert bool(resumen.alertas) is hay_alerta


def test_salas_en_5_5_y_3_04_se_ven_y_se_comparan_redondeadas():
    """Lo que muestra la tabla (5,0 · 5,0 · 3,0) es lo que decide la alerta: 2,0 niveles, aunque sin redondear sean 1,96."""
    niveles = {(1, 1): [5], (2, 1): [5], (3, 1): [3] * 24 + [4]}  # 76/25 = 3,04
    assert promedio(niveles[(3, 1)]) == Fraction(76, 25)

    resumen = comparar_salas([A, B, C], [LV], niveles)

    assert [_celda(resumen, s, LV).texto_promedio for s in (A, B, C)] == ["5,0", "5,0", "3,0"]
    c = _celda(resumen, C, LV)
    assert c.diferencia == Decimal("2.0")
    assert c.alerta
    assert [a.texto_alerta for a in resumen.alertas] == [
        "Revisar: Sala C, 2,0 niveles bajo el resto del jardín en Lenguaje Verbal"
    ]
    assert c.texto_celda == "Revisar: 2,0 niveles bajo el resto"


def test_la_alerta_coincide_siempre_con_los_promedios_que_muestra_la_tabla():
    """De 3,00 a 4,00 en pasos de 0,05: la alerta sale si y solo si los valores mostrados distan 2 o más."""
    for k in range(21):
        niveles = {(1, 1): [5], (2, 1): [6], (3, 1): [3] * (20 - k) + [4] * k}
        resumen = comparar_salas([A, B, C], [LV], niveles)
        mostrados = [Decimal(_celda(resumen, s, LV).texto_promedio.replace(",", ".")) for s in (A, B, C)]
        demas = redondear(Fraction(mostrados[0] + mostrados[1]) / 2)
        c = _celda(resumen, C, LV)
        assert c.promedio_demas == demas, k
        assert c.alerta is (demas - mostrados[2] >= 2), k
        if c.alerta:
            assert c.texto_celda == f"Revisar: {str(demas - mostrados[2]).replace('.', ',')} niveles bajo el resto"


def test_la_diferencia_se_muestra_con_un_decimal():
    resumen = comparar_salas([A, B, C], [LV], {(1, 1): [5], (2, 1): [6], (3, 1): [3]})
    assert resumen.alertas[0].texto_alerta == "Revisar: Sala C, 2,5 niveles bajo el resto del jardín en Lenguaje Verbal"
    resumen = comparar_salas([A, B], [LV], {(1, 1): [5], (2, 1): [4]}, umbral=1)
    assert resumen.alertas[0].texto_celda == "Revisar: 1,0 niveles bajo el resto"
    assert resumen.texto_umbral == "1 nivel"


def test_salas_de_distinto_nivel_educativo_no_se_comparan():
    medio = _sala(4, "Medio Mayor", NivelEducativo.MEDIO)
    niveles = {(1, 1): [6, 6], (2, 1): [6, 6], (4, 1): [3, 3]}
    resumen = comparar_salas([A, B, medio], [LV], niveles)

    assert resumen.alertas == []
    assert [g.nivel_educativo for g in resumen.grupos] == [NivelEducativo.MEDIO, NivelEducativo.TRANSICION]
    grupo_medio = resumen.grupos[0]
    assert grupo_medio.nombre == "Nivel medio"
    assert not grupo_medio.comparable
    assert [c.pk for c in grupo_medio.cursos] == [4]
    celda = _celda(resumen, medio, LV)
    assert celda.promedio == 3 and celda.promedio_demas is None and not celda.alerta


def test_un_jardin_con_un_solo_curso_no_genera_alerta():
    resumen = comparar_salas([C], [LV, PM], {(3, 1): [1, 1], (3, 2): [1]})
    assert resumen.alertas == []
    assert not resumen.grupos[0].comparable


def test_una_sala_sin_datos_no_tiene_alerta_ni_entra_en_el_promedio_de_las_demas():
    niveles = {(1, 1): [6, 6], (2, 1): [3, 3]}  # C no tiene niños
    resumen = comparar_salas([A, B, C], [LV], niveles)

    sin_datos = _celda(resumen, C, LV)
    assert sin_datos.promedio is None and sin_datos.diferencia is None and not sin_datos.alerta
    assert not sin_datos.suficiente
    assert sin_datos.texto_promedio == "Sin datos suficientes"
    # B se compara solo con A (6), no con un 0 de C.
    assert _celda(resumen, B, LV).promedio_demas == 6
    assert [a.curso.nombre for a in resumen.alertas] == ["Sala B"]


def test_una_sala_sin_niveles_validados_muestra_sin_datos_suficientes():
    """None es un niño sin nivel validado en el núcleo (por ejemplo, solo con el nivel inicial automático)."""
    niveles = {(1, 1): [6, 6], (2, 1): [6, 6], (3, 1): [None, None, None]}
    resumen = comparar_salas([A, B, C], [LV], niveles)

    c = _celda(resumen, C, LV)
    assert c.texto_promedio == "Sin datos suficientes"
    assert (c.validados, c.ninos) == (0, 3)
    assert not c.alerta and resumen.alertas == []
    assert _celda(resumen, A, LV).promedio_demas == 6


# --- Mínimo de niños con nivel validado ---------------------------------------------------------


@pytest.mark.parametrize(
    "niveles_c, suficiente",
    [
        ([3, 3, None, None], True),  # justo la mitad: entra
        ([3, 3, 3, None, None, None], True),
        ([3, 3, 3, 3] + [None] * 5, False),  # 4 de 9: menos de la mitad
        ([3, 3, None, None, None], False),  # 2 de 5
        ([3, 3, 3, 3, 3] + [None] * 4, True),  # 5 de 9
    ],
)
def test_una_sala_entra_si_al_menos_la_mitad_tiene_nivel_validado(niveles_c, suficiente):
    niveles = {(1, 1): [6, 6], (2, 1): [6, 6], (3, 1): niveles_c}
    resumen = comparar_salas([A, B, C], [LV], niveles)

    c = _celda(resumen, C, LV)
    assert c.suficiente is suficiente
    assert (c.validados, c.ninos) == (sum(1 for n in niveles_c if n is not None), len(niveles_c))
    if suficiente:
        assert c.promedio == 3 and c.alerta
        assert [a.curso.nombre for a in resumen.alertas] == ["Sala C"]
    else:
        assert c.promedio is None and c.texto_promedio == "Sin datos suficientes"
        assert not c.alerta and resumen.alertas == []


def test_el_minimo_es_configurable():
    niveles = {(1, 1): [6, 6], (2, 1): [6, 6], (3, 1): [3, 3, None, None]}  # la mitad
    assert PROPORCION_MINIMA_VALIDADOS == Fraction(1, 2)
    assert _celda(comparar_salas([A, B, C], [LV], niveles), C, LV).alerta

    con_tres_cuartos = comparar_salas([A, B, C], [LV], niveles, proporcion_minima=Fraction(3, 4))
    c = _celda(con_tres_cuartos, C, LV)
    assert not c.suficiente and not c.alerta and con_tres_cuartos.alertas == []
    assert c.texto_promedio == "Sin datos suficientes"
    assert con_tres_cuartos.texto_minimo == "3 de cada 4"
    # También acepta un Decimal, sin pasar por float.
    assert not _celda(comparar_salas([A, B, C], [LV], niveles, proporcion_minima=Decimal("0.75")), C, LV).suficiente
    assert _celda(comparar_salas([A, B, C], [LV], niveles, proporcion_minima=Decimal("0.5")), C, LV).suficiente


def test_una_sala_bajo_el_minimo_no_altera_el_promedio_de_las_demas():
    niveles = {(1, 1): [6, 6], (2, 1): [3, 3], (3, 1): [1, None, None, None]}  # C: 1 de 4
    resumen = comparar_salas([A, B, C], [LV], niveles)

    assert not _celda(resumen, C, LV).suficiente
    # B se compara solo con A (6,0), sin el 1 de C.
    assert _celda(resumen, B, LV).promedio_demas == 6
    assert _celda(resumen, A, LV).promedio_demas == 3
    assert [a.texto_alerta for a in resumen.alertas] == [
        "Revisar: Sala B, 3,0 niveles bajo el resto del jardín en Lenguaje Verbal"
    ]


def test_funciona_con_9_niveles_y_10_nucleos_sin_cambiar_codigo():
    nucleos = [SimpleNamespace(pk=10 + i, nombre=f"Núcleo {i}", sigla=f"K{i}") for i in range(10)]
    niveles = {}
    for n in nucleos:
        niveles[(1, n.pk)] = [9, 9]
        niveles[(2, n.pk)] = [9, 9]
        niveles[(3, n.pk)] = [6, 6]
    resumen = comparar_salas([A, B, C], nucleos, niveles)

    assert len(resumen.grupos[0].filas) == 10
    assert len(resumen.alertas) == 10
    assert {a.texto_celda for a in resumen.alertas} == {"Revisar: 3,0 niveles bajo el resto"}
    assert _celda(resumen, A, nucleos[0]).texto_promedio == "9,0"


def test_las_alertas_van_de_mayor_a_menor_diferencia():
    niveles = {(1, 1): [6], (2, 1): [6], (3, 1): [4], (1, 2): [6], (2, 2): [6], (3, 2): [2]}
    resumen = comparar_salas([A, B, C], [LV, PM], niveles)
    assert [a.nucleo.sigla for a in resumen.alertas] == ["PM", "LV"]


# --- Con la base ---------------------------------------------------------------------------


def _nino(curso, nombre, niveles, fecha=date(2026, 9, 30)):
    """Niño con su nivel validado más reciente en cada núcleo: {núcleo: nivel}."""
    nino = Nino.objects.create(curso=curso, nombre=nombre, fecha_ingreso=date(2026, 3, 2))
    for nucleo, nivel in niveles.items():
        NivelValidado.objects.create(nino=nino, nucleo=nucleo, nivel=nivel, fecha=fecha, validado_por=curso.educadora)
    return nino


@pytest.fixture
def tres_salas(curso, jardin, nucleos, otra_educadora):
    """Tres salas de Transición: A y B en 6 en Lenguaje Verbal, C en 3. En los demás núcleos, todas en 5."""
    ia, lv, pm = nucleos
    b = Curso.objects.create(jardin=jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora)
    c = Curso.objects.create(jardin=jardin, nombre="Transición C", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora)
    for sala, nivel_lv in [(curso, 6), (b, 6), (c, 3)]:
        for i in range(2):
            _nino(sala, f"Niño {i} de {sala.nombre}", {ia: 5, lv: nivel_lv, pm: 5})
    return curso, b, c


def test_resumen_del_jardin_usa_el_ultimo_nivel_validado(tres_salas, nucleos):
    a, b, c = tres_salas
    _ia, lv, _pm = nucleos
    # Un nivel más alto pero más antiguo no cuenta.
    for nino in c.ninos.all():
        NivelValidado.objects.create(nino=nino, nucleo=lv, nivel=8, fecha=date(2026, 7, 3))

    resumen = resumen_del_jardin(a.jardin)

    assert _celda(resumen, c, lv).promedio == 3
    assert [x.texto_alerta for x in resumen.alertas] == [
        "Revisar: Transición C, 3,0 niveles bajo el resto del jardín en Lenguaje Verbal"
    ]
    assert [s.cantidad_ninos for s in resumen.grupos[0].cursos] == [2, 2, 2]


def test_un_nivel_sin_validado_por_mas_reciente_no_cambia_el_promedio(tres_salas, nucleos):
    a, _b, c = tres_salas
    _ia, lv, _pm = nucleos
    for nino in c.ninos.all():
        NivelValidado.objects.create(nino=nino, nucleo=lv, nivel=8, fecha=date(2026, 10, 10))  # sin validado_por
        assert nino.nivel_actual(lv).nivel == 8  # la tabla del curso sí lo toma como actual

    resumen = resumen_del_jardin(a.jardin)

    assert _celda(resumen, c, lv).promedio == 3  # se usa el validado más reciente
    assert [x.texto_alerta for x in resumen.alertas] == [
        "Revisar: Transición C, 3,0 niveles bajo el resto del jardín en Lenguaje Verbal"
    ]


def test_una_sala_con_solo_el_nivel_inicial_automatico_no_tiene_datos_suficientes(tres_salas, nucleos, otra_educadora):
    a, b, c = tres_salas
    d = Curso.objects.create(jardin=a.jardin, nombre="Transición D", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora)
    for i in range(3):
        Nino.objects.create(curso=d, nombre=f"Niño {i} de D", fecha_ingreso=date(2026, 3, 2))  # nivel 1 sin validado_por
    assert NivelValidado.objects.filter(nino__curso=d, validado_por__isnull=True, nivel=1).count() == 3 * len(nucleos)

    resumen = resumen_del_jardin(a.jardin)

    for nucleo in nucleos:
        celda = _celda(resumen, d, nucleo)
        assert celda.texto_promedio == "Sin datos suficientes"
        assert (celda.validados, celda.ninos) == (0, 3)
        assert not celda.alerta
    # D no entra en el promedio de las demás: C sigue 3,0 bajo A y B.
    _ia, lv, _pm = nucleos
    assert _celda(resumen, c, lv).promedio_demas == 6
    assert [x.curso.nombre for x in resumen.alertas] == ["Transición C"]


@pytest.mark.parametrize("sin_validar, suficiente", [(2, True), (3, False)])
def test_resumen_del_jardin_aplica_el_minimo_de_ninos_validados(tres_salas, nucleos, sin_validar, suficiente):
    """C tiene 2 niños validados; con 2 más sin validar es justo la mitad, con 3 es menos."""
    a, _b, c = tres_salas
    for i in range(sin_validar):
        Nino.objects.create(curso=c, nombre=f"Recién llegado {i}", fecha_ingreso=date(2026, 10, 1))
    _ia, lv, _pm = nucleos

    resumen = resumen_del_jardin(a.jardin)

    celda = _celda(resumen, c, lv)
    assert (celda.validados, celda.ninos) == (2, 2 + sin_validar)
    assert celda.suficiente is suficiente
    assert bool(resumen.alertas) is suficiente
    if not suficiente:
        assert celda.texto_promedio == "Sin datos suficientes"
        # Con un mínimo más bajo sí entra.
        assert resumen_del_jardin(a.jardin, proporcion_minima=Fraction(1, 3)).alertas


def test_resumen_del_jardin_ignora_otros_jardines_y_hace_pocas_consultas(
    tres_salas, nucleos, otra_educadora, django_assert_max_num_queries
):
    a, _b, _c = tres_salas
    otro = Jardin.objects.create(nombre="Otro jardín")
    ajena = Curso.objects.create(jardin=otro, nombre="Transición Z", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora)
    _nino(ajena, "Niño ajeno", {n: 1 for n in nucleos})

    with django_assert_max_num_queries(5):
        resumen = resumen_del_jardin(a.jardin)

    assert [s.nombre for s in resumen.grupos[0].cursos] == ["Transición A", "Transición B", "Transición C"]


def test_resumen_del_jardin_con_rubrica_de_9_niveles(jardin, educadora, otra_educadora, nucleos):
    Rubrica.objects.create(nivel_educativo=NivelEducativo.MEDIO, cantidad_niveles=9)
    salas = [
        Curso.objects.create(jardin=jardin, nombre=f"Medio {letra}", nivel_educativo=NivelEducativo.MEDIO, educadora=educadora)
        for letra in "ABC"
    ]
    for sala, nivel in zip(salas, [9, 9, 6]):
        _nino(sala, f"Niño de {sala.nombre}", {n: nivel for n in nucleos})

    resumen = resumen_del_jardin(jardin)

    assert {a.curso.nombre for a in resumen.alertas} == {"Medio C"}
    assert len(resumen.alertas) == len(nucleos)
    assert _celda(resumen, salas[0], nucleos[0]).texto_promedio == "9,0"


# --- Permisos y vista ----------------------------------------------------------------------


def test_jardines_que_dirige(jardin, directora_del_jardin, educadora, asistente_del_curso):
    assert list(jardines_que_dirige(directora_del_jardin)) == [jardin]
    assert not jardines_que_dirige(educadora).exists()
    assert not jardines_que_dirige(asistente_del_curso).exists()
    assert not jardines_que_dirige(AnonymousUser()).exists()


def test_la_directora_ve_el_resumen_con_la_alerta_de_la_sala_rezagada(client, tres_salas, directora_del_jardin):
    a, b, c = tres_salas
    client.force_login(directora_del_jardin)

    respuesta = client.get(reverse("jardin", args=[a.jardin.pk]))

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Revisar: Transición C, 3,0 niveles bajo el resto del jardín en Lenguaje Verbal" in html
    assert html.count('class="celda-alerta"') == 1
    assert "Revisar: 3,0 niveles bajo el resto" in html
    assert "al menos la mitad de sus niños y niñas tiene nivel validado" in html
    assert '<th scope="row">Lenguaje Verbal</th>' in html
    for sala in (a, b, c):
        assert f'href="{reverse("curso", args=[sala.pk])}"' in html
        assert f'href="{reverse("capturar", args=[sala.pk])}"' in html  # la directora también registra
    # Las alertas van antes que la tabla.
    assert html.index("Sugerencias de revisión") < html.index('class="tabla-jardin"')


def test_la_vista_muestra_sin_datos_suficientes(client, tres_salas, nucleos, otra_educadora, directora_del_jardin):
    a, _b, _c = tres_salas
    d = Curso.objects.create(jardin=a.jardin, nombre="Transición D", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora)
    Nino.objects.create(curso=d, nombre="Niño de D", fecha_ingreso=date(2026, 3, 2))  # solo el nivel inicial automático
    client.force_login(directora_del_jardin)

    html = client.get(reverse("jardin", args=[a.jardin.pk])).content.decode()

    assert html.count('class="celda-sin-datos"') == len(nucleos)
    assert html.count("Sin datos suficientes") >= len(nucleos)
    assert html.count('class="celda-alerta"') == 1
    assert "Revisar: Transición C, 3,0 niveles bajo el resto del jardín en Lenguaje Verbal" in html


def test_sin_alertas_lo_dice(client, curso, nucleos, directora_del_jardin):
    _nino(curso, "Pedro", {n: 4 for n in nucleos})
    client.force_login(directora_del_jardin)
    html = client.get(reverse("jardin", args=[curso.jardin.pk])).content.decode()
    assert "Ninguna sala está 2 niveles o más bajo las demás salas de su nivel educativo." in html
    assert "Con una sola sala de este nivel educativo no hay con quién comparar." in html


@pytest.fixture
def directora_de_otro_jardin(directora_del_jardin, django_user_model):
    otra = django_user_model.objects.create_user("elena", password="clave-de-prueba-123")
    Jardin.objects.create(nombre="Otro jardín", directora=otra)
    return otra


@pytest.mark.parametrize("quien", ["educadora", "asistente_del_curso", "directora_de_otro_jardin"])
def test_otras_usuarias_reciben_404(client, curso, quien, request):
    client.force_login(request.getfixturevalue(quien))
    assert client.get(reverse("jardin", args=[curso.jardin.pk])).status_code == 404


def test_sin_sesion_pide_login(client, curso):
    respuesta = client.get(reverse("jardin", args=[curso.jardin.pk]))
    assert respuesta.status_code == 302
    assert reverse("login") in respuesta["Location"]


def test_la_vista_funciona_con_9_niveles_y_10_nucleos(client, jardin, educadora, directora_del_jardin):
    Rubrica.objects.create(nivel_educativo=NivelEducativo.MEDIO, cantidad_niveles=9)
    nucleos = [Nucleo.objects.create(sigla=f"K{i}", nombre=f"Núcleo {i}", orden=i) for i in range(10)]
    salas = [
        Curso.objects.create(jardin=jardin, nombre=f"Medio {letra}", nivel_educativo=NivelEducativo.MEDIO, educadora=educadora)
        for letra in "ABC"
    ]
    for sala, nivel in zip(salas, [9, 9, 6]):
        _nino(sala, f"Niño de {sala.nombre}", {n: nivel for n in nucleos})
    client.force_login(directora_del_jardin)

    html = client.get(reverse("jardin", args=[jardin.pk])).content.decode()

    assert "Revisar: Medio C, 3,0 niveles bajo el resto del jardín en Núcleo 9" in html
    assert html.count('class="celda-alerta"') == 10


# --- Navegación ----------------------------------------------------------------------------


def test_la_directora_llega_al_resumen_desde_el_inicio(client, curso, directora_del_jardin):
    # Dirige un solo jardín: el inicio la lleva a su resumen, antes que a registrar.
    client.force_login(directora_del_jardin)
    respuesta = client.get(reverse("inicio"))
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("jardin", args=[curso.jardin.pk])

    # Dirige dos jardines: el inicio enlaza al resumen de cada uno.
    otro = Jardin.objects.create(nombre="Otro jardín", directora=directora_del_jardin)
    respuesta = client.get(reverse("inicio"))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert f'href="{reverse("jardin", args=[curso.jardin.pk])}"' in html
    assert f'href="{reverse("jardin", args=[otro.pk])}"' in html


def test_la_educadora_y_la_asistente_siguen_yendo_a_registrar(client, curso, educadora, asistente_del_curso,
                                                              directora_del_jardin):
    for usuaria in (educadora, asistente_del_curso):
        client.force_login(usuaria)
        respuesta = client.get(reverse("inicio"))
        assert respuesta.status_code == 302
        assert respuesta["Location"] == reverse("registrar", args=[curso.pk])


def test_la_tabla_del_curso_enlaza_al_resumen_solo_para_la_directora(client, curso, educadora, directora_del_jardin):
    enlace = f'href="{reverse("jardin", args=[curso.jardin.pk])}"'
    client.force_login(directora_del_jardin)
    assert enlace in client.get(reverse("curso", args=[curso.pk])).content.decode()
    client.force_login(educadora)
    assert enlace not in client.get(reverse("curso", args=[curso.pk])).content.decode()
