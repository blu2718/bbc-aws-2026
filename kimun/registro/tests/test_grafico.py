"""Gráfico de evolución de los niveles validados (PLAN.md, Task 3)."""
import xml.etree.ElementTree as ET
from datetime import date
from types import SimpleNamespace

import pytest
from django.template.loader import render_to_string

from registro.grafico import (
    ALTO,
    ANCHO,
    MARGEN_DER,
    MARGEN_INF,
    MARGEN_IZQ,
    MARGEN_SUP,
    Punto,
    evolucion_del_nino,
    puntos_evolucion,
    svg_evolucion,
)
from registro.models import DescriptorNivel, NivelEducativo, NivelValidado, Nino, Nucleo

SVG = "{http://www.w3.org/2000/svg}"
MARZO, JUNIO, OCTUBRE = date(2026, 3, 2), date(2026, 6, 1), date(2026, 10, 15)


def _arbol(svg):
    """Parsea el SVG; falla si no es XML válido."""
    return ET.fromstring(str(svg))


def _circulos(svg):
    return [(float(c.get("cx")), float(c.get("cy"))) for c in _arbol(svg).iter(f"{SVG}circle")]


def _marcas(svg, clase):
    return [t.text for t in _arbol(svg).iter(f"{SVG}text") if t.get("class") == clase]


# --- Puntos -------------------------------------------------------------------------


def test_puntos_en_orden_de_fecha_y_el_mismo_dia_vale_el_ultimo_registrado():
    registrados = [
        SimpleNamespace(fecha=JUNIO, nivel=3, comentario=""),
        SimpleNamespace(fecha=MARZO, nivel=1, comentario="Nivel inicial."),
        SimpleNamespace(fecha=JUNIO, nivel=4, comentario="Corrige el 3."),
    ]
    assert puntos_evolucion(registrados) == [Punto(MARZO, 1, "Nivel inicial."), Punto(JUNIO, 4, "Corrige el 3.")]


def test_puntos_sin_comentario():
    assert puntos_evolucion([SimpleNamespace(fecha=MARZO, nivel=2)]) == [Punto(MARZO, 2, "")]


# --- SVG ----------------------------------------------------------------------------


def test_sin_puntos_no_hay_grafico():
    assert svg_evolucion([], 8) == ""


def test_es_xml_valido_con_un_punto_por_validacion():
    svg = svg_evolucion([Punto(MARZO, 1), Punto(JUNIO, 3), Punto(OCTUBRE, 4)], 8)
    raiz = _arbol(svg)
    assert raiz.get("viewBox") == f"0 0 {ANCHO} {ALTO}"
    assert len(_circulos(svg)) == 3


def test_el_nivel_1_va_abajo_y_el_maximo_arriba():
    svg = svg_evolucion([Punto(MARZO, 1), Punto(JUNIO, 8)], 8)
    (x1, y1), (x2, y2) = _circulos(svg)
    assert y1 == ALTO - MARGEN_INF
    assert y2 == MARGEN_SUP
    assert (x1, x2) == (MARGEN_IZQ, ANCHO - MARGEN_DER)


@pytest.mark.parametrize("nivel_maximo", [8, 9])
def test_el_eje_tiene_una_marca_por_nivel_de_la_rubrica(nivel_maximo):
    svg = svg_evolucion([Punto(MARZO, 1)], nivel_maximo)
    assert _marcas(svg, "eje-y") == [str(n) for n in range(1, nivel_maximo + 1)]


def test_con_rubrica_de_9_el_nivel_9_queda_arriba():
    svg = svg_evolucion([Punto(MARZO, 1), Punto(JUNIO, 9)], 9)
    assert _circulos(svg)[1][1] == MARGEN_SUP


def test_un_nivel_sobre_la_rubrica_no_se_sale_del_grafico():
    # Si la rúbrica pasa de 9 a 8, un 9 ya validado debe seguir dentro del dibujo.
    svg = svg_evolucion([Punto(MARZO, 9)], 8)
    assert _circulos(svg)[0][1] >= MARGEN_SUP
    assert _marcas(svg, "eje-y")[-1] == "9"


def test_los_escalones_mantienen_el_nivel_hasta_la_validacion_siguiente():
    svg = svg_evolucion([Punto(MARZO, 1), Punto(JUNIO, 3)], 8)
    camino = _arbol(svg).find(f"{SVG}path").get("d")
    # Horizontal hasta junio (H) y después sube (V): no una diagonal.
    assert camino.split()[3] == "H"
    assert camino.split()[5] == "V"


def test_hasta_prolonga_el_ultimo_nivel_y_se_muestra_en_el_eje():
    svg = svg_evolucion([Punto(MARZO, 1), Punto(JUNIO, 3)], 8, hasta=OCTUBRE)
    camino = _arbol(svg).find(f"{SVG}path").get("d")
    assert camino.endswith(f"H {ANCHO - MARGEN_DER:.1f}")
    assert _circulos(svg)[-1][0] < ANCHO - MARGEN_DER
    assert _marcas(svg, "eje-x") == ["02-03-2026", "15-10-2026"]


def test_hasta_anterior_al_ultimo_punto_no_lo_corta():
    svg = svg_evolucion([Punto(MARZO, 1), Punto(JUNIO, 3)], 8, hasta=MARZO)
    assert _marcas(svg, "eje-x") == ["02-03-2026", "01-06-2026"]


def test_un_solo_punto_sin_rango_queda_al_centro():
    svg = svg_evolucion([Punto(MARZO, 2)], 8)
    assert _circulos(svg)[0][0] == (MARGEN_IZQ + ANCHO - MARGEN_DER) / 2
    assert _marcas(svg, "eje-x") == ["02-03-2026"]


def test_texto_accesible_resume_la_evolucion():
    svg = svg_evolucion([Punto(MARZO, 1), Punto(JUNIO, 3)], 8, etiqueta="Lenguaje Verbal")
    raiz = _arbol(svg)
    esperado = "Lenguaje Verbal: nivel 1 el 02-03-2026, nivel 3 el 01-06-2026. Nivel actual: 3 (de 8 niveles)."
    assert raiz.get("role") == "img"
    assert raiz.get("aria-label") == esperado
    assert raiz.find(f"{SVG}title").text == esperado


def test_con_nombres_de_la_rubrica_el_nivel_se_muestra_con_numero_y_nombre():
    registrados = [SimpleNamespace(fecha=MARZO, nivel=1), SimpleNamespace(fecha=JUNIO, nivel=3)]
    puntos = puntos_evolucion(registrados, {1: "Comenzando", 3: "Desarrollando"})
    assert [p.texto for p in puntos] == ["1 · Comenzando", "3 · Desarrollando"]
    svg = svg_evolucion(puntos, 8)
    assert _arbol(svg).get("aria-label").endswith("Nivel actual: 3 · Desarrollando (de 8 niveles).")


def test_sin_nombre_el_nivel_se_muestra_solo_con_el_numero():
    assert puntos_evolucion([SimpleNamespace(fecha=MARZO, nivel=4)], {1: "Comenzando"})[0].texto == "4"


def test_escapa_la_etiqueta():
    svg = svg_evolucion([Punto(MARZO, 1)], 8, etiqueta='<script>"x"</script>')
    assert "<script>" not in svg
    assert _arbol(svg).get("aria-label").startswith('<script>"x"</script>:')


# --- Con la base de datos -------------------------------------------------------------


@pytest.fixture
def nino(curso, nucleos):
    return Nino.objects.create(curso=curso, nombre="Pedro", fecha_ingreso=MARZO)


def test_evolucion_del_nino_trae_todos_los_nucleos_en_orden(nino, nucleos, educadora):
    lv = nucleos[1]
    NivelValidado.objects.create(nino=nino, nucleo=lv, nivel=3, fecha=JUNIO, validado_por=educadora, comentario="x")
    evoluciones = evolucion_del_nino(nino, hasta=OCTUBRE)

    assert list(evoluciones) == ["IA", "LV", "PM"]
    assert [(p.fecha, p.nivel) for p in evoluciones["LV"].puntos] == [(MARZO, 1), (JUNIO, 3)]
    assert evoluciones["LV"].actual.nivel == 3
    assert [(p.fecha, p.nivel) for p in evoluciones["IA"].puntos] == [(MARZO, 1)]
    assert _marcas(evoluciones["LV"].svg, "eje-x") == ["02-03-2026", "15-10-2026"]


def test_usa_el_maximo_de_la_rubrica_del_curso(nino, rubrica):
    rubrica.cantidad_niveles = 9
    rubrica.save()
    svg = evolucion_del_nino(nino, hasta=OCTUBRE)["IA"].svg
    assert _marcas(svg, "eje-y")[-1] == "9"
    assert "Nivel actual: 1 (de 9 niveles)." in _arbol(svg).get("aria-label")


def test_el_mismo_dia_coincide_con_el_nivel_actual(nino, nucleos, educadora):
    lv = nucleos[1]
    NivelValidado.objects.create(nino=nino, nucleo=lv, nivel=3, fecha=JUNIO, validado_por=educadora)
    NivelValidado.objects.create(nino=nino, nucleo=lv, nivel=2, fecha=JUNIO, validado_por=educadora)
    assert evolucion_del_nino(nino)["LV"].actual.nivel == nino.nivel_actual(lv).nivel == 2


def test_un_nucleo_sin_niveles_queda_sin_grafico(nino):
    nuevo = Nucleo.objects.create(sigla="LA", nombre="Lenguajes Artísticos", orden=9)
    evolucion = evolucion_del_nino(nino)["LA"]
    assert (evolucion.nucleo, evolucion.puntos, evolucion.svg, evolucion.actual) == (nuevo, [], "", None)


def test_la_cantidad_de_consultas_no_crece_con_las_validaciones(nino, nucleos, educadora, django_assert_max_num_queries):
    for mes in range(4, 11):
        for nucleo in nucleos:
            NivelValidado.objects.create(
                nino=nino, nucleo=nucleo, nivel=mes - 2, fecha=date(2026, mes, 1), validado_por=educadora
            )
    nino = Nino.objects.get(pk=nino.pk)  # sin el curso en caché
    with django_assert_max_num_queries(5):
        evoluciones = evolucion_del_nino(nino, hasta=OCTUBRE)
    assert len(evoluciones["PM"].puntos) == 8


# --- Plantilla con el gráfico y la tabla equivalente -------------------------------------


def test_la_plantilla_muestra_el_grafico_y_la_tabla_equivalente(nino, nucleos, educadora):
    NivelValidado.objects.create(
        nino=nino, nucleo=nucleos[1], nivel=3, fecha=JUNIO, validado_por=educadora, comentario="Relata un cuento."
    )
    html = render_to_string("registro/_evolucion.html", {"evolucion": evolucion_del_nino(nino)["LV"]})
    assert html.count("<svg") == 1
    assert "<caption>Niveles validados en Lenguaje Verbal</caption>" in html
    assert '<time datetime="2026-06-01">01-06-2026</time>' in html
    assert "<td>3</td>" in html and "Relata un cuento." in html
    assert '<time datetime="2026-03-02">02-03-2026</time>' in html and "Nivel inicial al ingresar." in html


def test_toma_los_nombres_de_los_descriptores_oficiales(nino, nucleos, educadora):
    ia, lv, _pm = nucleos
    crear = DescriptorNivel.objects.create
    crear(nivel_educativo=NivelEducativo.TRANSICION, nucleo=ia, nivel=3, nombre="Desarrollando", descripcion="x",
          provisorio=False)
    crear(nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, nivel=3, nombre="Nivel 3", descripcion="x")
    for nucleo in (ia, lv):
        NivelValidado.objects.create(nino=nino, nucleo=nucleo, nivel=3, fecha=JUNIO, validado_por=educadora)

    evoluciones = evolucion_del_nino(nino)
    assert evoluciones["IA"].actual.texto == "3 · Desarrollando"
    # El nombre provisorio repetiría el número: se muestra "3", no "3 · Nivel 3".
    assert evoluciones["LV"].actual.texto == "3"


def test_la_plantilla_muestra_el_nombre_del_nivel_si_lo_hay(nino, nucleos, educadora):
    NivelValidado.objects.create(nino=nino, nucleo=nucleos[0], nivel=3, fecha=JUNIO, validado_por=educadora)
    nombres = {"IA": {1: "Comenzando", 3: "Desarrollando"}}
    evolucion = evolucion_del_nino(nino, nombres=nombres)["IA"]
    html = render_to_string("registro/_evolucion.html", {"evolucion": evolucion})
    assert "<td>3 · Desarrollando</td>" in html and "<td>1 · Comenzando</td>" in html
    assert "Nivel actual: 3 · Desarrollando." in html
    # Los núcleos sin nombres siguen con el número.
    assert evolucion_del_nino(nino, nombres=nombres)["LV"].actual.texto == "1"


def test_la_plantilla_sin_niveles_lo_dice_en_texto(nino):
    Nucleo.objects.create(sigla="LA", nombre="Lenguajes Artísticos", orden=9)
    html = render_to_string("registro/_evolucion.html", {"evolucion": evolucion_del_nino(nino)["LA"]})
    assert "<svg" not in html
    assert "Sin niveles validados en Lenguajes Artísticos." in html
