"""Pantallas III y IV de diseno-interfaz.jpg: menú lateral y perfil del niño (gráfico, edad e historial)."""
from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from registro.models import Efecto, MetaSemestre, NivelValidado, Nino, Semestre
from registro.pantallas import texto_edad
from registro.radar import EjeRadar, svg_radar


@pytest.mark.parametrize("nacimiento, hoy, esperado", [
    (date(2020, 5, 14), date(2026, 10, 15), "6 años y 5 meses"),
    (date(2020, 10, 15), date(2026, 10, 15), "6 años"),
    (date(2020, 10, 16), date(2026, 10, 15), "5 años y 11 meses"),
    (date(2025, 9, 1), date(2026, 10, 15), "1 año y 1 mes"),
    (None, date(2026, 10, 15), ""),
    (date(2027, 1, 1), date(2026, 10, 15), ""),
])
def test_texto_edad(nacimiento, hoy, esperado):
    assert texto_edad(nacimiento, hoy) == esperado


def _ejes(*niveles):
    return [EjeRadar(f"N{i}", f"Núcleo {i}", nivel, str(nivel), mediana=4) for i, nivel in enumerate(niveles)]


def test_el_grafico_tiene_un_petalo_por_nucleo_y_un_anillo_por_nivel():
    svg = svg_radar(_ejes(3, 5, 2, 8, 1, 4, 6, 7, 2, 3), nivel_maximo=9, esperado=5)
    assert svg.count('class="radar-petalo"') == 10     # 10 núcleos, como tendrá Integra
    assert svg.count('class="radar-etiqueta"') == 10
    assert svg.count('class="radar-anillo"') == 9      # 9 niveles
    assert svg.count('class="radar-mediana"') == 10 and 'class="radar-esperado"' in svg
    assert 'role="img"' in svg and "Núcleo 3: 8" in svg and "Nivel esperado según su semestre: 5." in svg


def test_las_etiquetas_llevan_el_nombre_completo_del_nucleo():
    ejes = [EjeRadar("CES", "Comprensión del Entorno Sociocultural", 4, "4"), *_ejes(1, 2)]
    svg = svg_radar(ejes, nivel_maximo=8)
    for fila in ("Comprensión", "del Entorno", "Sociocultural", "nivel 4"):
        assert f">{fila}</tspan>" in svg
    assert ">CES<" not in svg


def test_el_grafico_escapa_el_texto_y_necesita_tres_nucleos():
    ejes = [EjeRadar("<b>", "<script>x</script>", 2, "2"), *_ejes(1, 1)]
    svg = svg_radar(ejes, nivel_maximo=8)
    assert "<script>" not in svg and "&lt;script&gt;" in svg
    assert 'class="radar-esperado"' not in svg
    assert svg_radar(_ejes(1, 2), nivel_maximo=8) == ""


@pytest.fixture
def curso_con_rezago(curso, nucleos, educadora):
    """Matías está 3 niveles bajo la mediana en LV; Pedro tiene fecha de nacimiento y un suceso aceptado."""
    hoy = timezone.localdate()
    Semestre.objects.create(nombre="actual", inicio=hoy - timedelta(days=200), fin=hoy + timedelta(days=60))
    MetaSemestre.objects.create(curso=curso, semestre_permanencia=1, nivel_esperado=4)
    ninos = {}
    for nombre in ("Pedro Salinas", "Emilio Vargas", "Rubí Contreras", "Matías Lagos"):
        ninos[nombre] = Nino.objects.create(
            curso=curso, nombre=nombre, fecha_ingreso=hoy - timedelta(days=150), fecha_nacimiento=date(2020, 5, 14)
        )
        for nucleo in nucleos:
            nivel = 2 if (nombre == "Matías Lagos" and nucleo.sigla == "LV") else 5
            NivelValidado.objects.create(nino=ninos[nombre], nucleo=nucleo, nivel=nivel, fecha=hoy - timedelta(days=10),
                                         validado_por=educadora, comentario="Revisión de septiembre")
    return ninos


def test_el_menu_muestra_el_curso_los_ninos_para_tener_presentes_y_la_lista(client, curso, educadora, curso_con_rezago):
    client.force_login(educadora)
    html = client.get(reverse("curso", args=[curso.pk])).content.decode()
    menu = html[html.index('id="menu-lateral"'):html.index("</dialog>")]

    assert curso.nombre in menu and curso.jardin.nombre in menu
    presentes = menu[menu.index("Para tener presentes"):menu.index('id="titulo-ninos"')]
    assert "Matías Lagos" in presentes and "Pedro Salinas" not in presentes
    assert "Revisar en Lenguaje Verbal" in presentes
    assert 'data-buscador' in menu and "Niños y niñas (4)" in menu
    for nino in curso_con_rezago.values():
        assert f'href="{reverse("ficha", args=[nino.pk])}"' in menu
    assert reverse("revision", args=[curso.pk]) in menu and reverse("registrar", args=[curso.pk]) in menu


def test_el_menu_de_la_asistente_no_ofrece_revisar_ni_metas(client, curso, asistente_del_curso, curso_con_rezago):
    client.force_login(asistente_del_curso)
    html = client.get(reverse("registrar", args=[curso.pk])).content.decode()
    menu = html[html.index('id="menu-lateral"'):html.index("</dialog>")]
    assert reverse("registrar", args=[curso.pk]) in menu
    assert reverse("revision", args=[curso.pk]) not in menu and reverse("metas", args=[curso.pk]) not in menu


def test_el_perfil_muestra_edad_grafico_e_historial(client, curso, educadora, curso_con_rezago, nucleos, observar_en):
    pedro = curso_con_rezago["Pedro Salinas"]
    obs = observar_en(pedro, timezone.localdate() - timedelta(days=2), [nucleos[2]], cita="Clasificó hojas por color.")
    obs.efecto = Efecto.AVANCE
    obs.save()
    client.force_login(educadora)

    html = client.get(reverse("ficha", args=[pedro.pk])).content.decode()

    assert texto_edad(date(2020, 5, 14), timezone.localdate()) in html
    assert 'class="radar"' in html and "Nivel en cada núcleo (3)" in html
    historial = html[html.index('id="titulo-historial"'):html.index('id="titulo-detalle"')]
    assert "Clasificó hojas por color." in historial and "Muestra avance" in historial
    assert f'href="{reverse("captura", args=[obs.captura_id])}"' in historial
    assert "Niveles validados" in historial and "Revisión de septiembre" in historial
    assert historial.index("Clasificó hojas por color.") < historial.index("Niveles validados")  # lo más reciente primero


# --- Niños nombrados en la nota, aunque la IA no responda ---------------------------------------


def test_se_reconocen_los_ninos_nombrados_en_la_nota(curso, nucleos):
    from registro.pantallas import ninos_mencionados

    naiara = Nino.objects.create(curso=curso, nombre="Naiara Fuentes", alias=["Nayara"], fecha_ingreso=date(2026, 3, 2),
                                 fecha_nacimiento=date(2024, 11, 2))
    Nino.objects.create(curso=curso, nombre="Pedro Salinas", fecha_ingreso=date(2026, 3, 2))
    hoy = date(2026, 10, 15)

    encontrados = ninos_mencionados("Naiara se quedó dormida durante la actividad recreacional.", curso.ninos.all(), hoy)
    assert [p.nino for p in encontrados] == [naiara] and encontrados[0].edad == "1 año y 11 meses"
    assert [p.nino for p in ninos_mencionados("NAYARA lloró al llegar", curso.ninos.all(), hoy)] == [naiara]
    assert ninos_mencionados("Pedrito y Víctor jugaron", curso.ninos.all(), hoy) == []  # solo coincidencias exactas


def test_sin_conexion_a_bedrock_la_pagina_lo_dice_y_muestra_el_perfil(client, curso, educadora, nucleos):
    from registro.models import Captura

    naiara = Nino.objects.create(curso=curso, nombre="Naiara Fuentes", fecha_ingreso=date(2026, 3, 2))
    captura = Captura.objects.create(
        curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, estado=Captura.Estado.ERROR,
        texto_original="Naiara se quedó dormida durante la actividad recreacional",
        error="Bedrock rechazó la llamada: Unable to locate credentials",
    )
    client.force_login(educadora)

    html = client.get(reverse("captura", args=[captura.pk])).content.decode()

    assert "Kimün no está conectado a la IA en este servidor." in html
    assert "Nombrados en la nota" in html and f'href="{reverse("ficha", args=[naiara.pk])}"' in html
    assert "Unable to locate credentials" not in html
