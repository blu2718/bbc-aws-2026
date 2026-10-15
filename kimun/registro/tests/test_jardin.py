"""Vista del jardín para la directora: comparación de salas del mismo nivel educativo (PLAN.md, Task 12)."""
from datetime import date
from fractions import Fraction
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from registro.alertas import UMBRAL_SALA_BAJO, comparar_salas, promedio, resumen_del_jardin
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


def test_el_promedio_de_cada_sala_se_muestra_con_un_decimal():
    resumen = comparar_salas([A, B], [LV], {(1, 1): [2, 3], (2, 1): [4, 5, 5]})
    assert _celda(resumen, A, LV).promedio == Fraction(5, 2)
    assert _celda(resumen, A, LV).texto_promedio == "2,5"
    assert _celda(resumen, B, LV).promedio == Fraction(14, 3)
    assert _celda(resumen, B, LV).texto_promedio == "4,7"
    assert _celda(resumen, B, LV).promedio_demas == Fraction(5, 2)


# --- Ejemplo de Integra y umbral -------------------------------------------------------------


def test_ejemplo_de_integra_dos_salas_en_6_y_una_en_3():
    niveles = {(1, 1): [6, 6, 6], (2, 1): [6, 5, 7], (3, 1): [3, 3, 3]}
    resumen = comparar_salas([A, B, C], [LV], niveles)

    assert [a.curso.nombre for a in resumen.alertas] == ["Sala C"]
    alerta = resumen.alertas[0]
    assert alerta.texto_alerta == "Revisar: Sala C, 3 niveles bajo el resto del jardín en Lenguaje Verbal"
    assert alerta.texto_celda == "Revisar: 3 niveles bajo el resto"
    assert not _celda(resumen, A, LV).alerta and _celda(resumen, A, LV).texto_alerta == ""
    assert not _celda(resumen, B, LV).alerta
    assert resumen.umbral == UMBRAL_SALA_BAJO == 2


@pytest.mark.parametrize(
    "niveles_a, niveles_b, niveles_c, umbral, hay_alerta",
    [
        ([5, 5], [5, 5], [3, 3], 2, True),  # justo 2 niveles: dispara
        ([5, 5], [5, 5], [3, 4], 2, False),  # 1,5 niveles: no
        ([6, 5, 5], [6, 5, 5], [3, 4, 3], 2, True),  # 16/3 − 10/3 = 2 exacto, sin error de decimales
        ([5, 5], [5, 5], [3, 3], 3, False),  # umbral configurable
        ([5, 5], [5, 5], [4, 4], 1, True),
    ],
)
def test_umbral_en_el_borde(niveles_a, niveles_b, niveles_c, umbral, hay_alerta):
    niveles = {(1, 1): niveles_a, (2, 1): niveles_b, (3, 1): niveles_c}
    resumen = comparar_salas([A, B, C], [LV], niveles, umbral=umbral)
    assert _celda(resumen, C, LV).alerta is hay_alerta
    assert bool(resumen.alertas) is hay_alerta


def test_la_diferencia_se_redondea_a_un_decimal_y_1_nivel_va_en_singular():
    resumen = comparar_salas([A, B, C], [LV], {(1, 1): [5], (2, 1): [6], (3, 1): [3]})
    assert resumen.alertas[0].texto_alerta == "Revisar: Sala C, 2,5 niveles bajo el resto del jardín en Lenguaje Verbal"
    resumen = comparar_salas([A, B], [LV], {(1, 1): [5], (2, 1): [4]}, umbral=1)
    assert resumen.alertas[0].texto_celda == "Revisar: 1 nivel bajo el resto"


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
    assert sin_datos.texto_promedio == "–"
    # B se compara solo con A (6), no con un 0 de C.
    assert _celda(resumen, B, LV).promedio_demas == 6
    assert [a.curso.nombre for a in resumen.alertas] == ["Sala B"]


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
    assert {a.texto_celda for a in resumen.alertas} == {"Revisar: 3 niveles bajo el resto"}
    assert _celda(resumen, A, nucleos[0]).texto_promedio == "9"


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
        "Revisar: Transición C, 3 niveles bajo el resto del jardín en Lenguaje Verbal"
    ]
    assert [s.cantidad_ninos for s in resumen.grupos[0].cursos] == [2, 2, 2]


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
    assert _celda(resumen, salas[0], nucleos[0]).texto_promedio == "9"


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
    assert "Revisar: Transición C, 3 niveles bajo el resto del jardín en Lenguaje Verbal" in html
    assert html.count('class="celda-alerta"') == 1
    assert "Revisar: 3 niveles bajo el resto" in html
    assert '<th scope="row">Lenguaje Verbal</th>' in html
    for sala in (a, b, c):
        assert f'href="{reverse("curso", args=[sala.pk])}"' in html
    # Las alertas van antes que la tabla.
    assert html.index("Sugerencias de revisión") < html.index('class="tabla-jardin"')


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

    assert "Revisar: Medio C, 3 niveles bajo el resto del jardín en Núcleo 9" in html
    assert html.count('class="celda-alerta"') == 10


# --- Navegación ----------------------------------------------------------------------------


def test_la_directora_llega_al_resumen_desde_el_inicio(client, curso, directora_del_jardin):
    client.force_login(directora_del_jardin)
    respuesta = client.get(reverse("inicio"))
    # Aunque vea un solo curso, no se la redirige: el inicio enlaza al resumen.
    assert respuesta.status_code == 200
    assert f'href="{reverse("jardin", args=[curso.jardin.pk])}"' in respuesta.content.decode()


def test_la_tabla_del_curso_enlaza_al_resumen_solo_para_la_directora(client, curso, educadora, directora_del_jardin):
    enlace = f'href="{reverse("jardin", args=[curso.jardin.pk])}"'
    client.force_login(directora_del_jardin)
    assert enlace in client.get(reverse("curso", args=[curso.pk])).content.decode()
    client.force_login(educadora)
    assert enlace not in client.get(reverse("curso", args=[curso.pk])).content.decode()
