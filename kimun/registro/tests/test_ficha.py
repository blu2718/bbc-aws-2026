"""Ficha del niño (Task 3, spec task3-ficha-nino): acceso, rúbrica, evidencia y situación del curso.

La situación (esperado, mediana y señales) sale de `alertas.tabla_del_curso`
(Task 2), la misma que usa la tabla del curso.
"""
from datetime import date, timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from registro.ficha import armar_ficha
from registro.models import (
    DescriptorNivel,
    MetaSemestre,
    NivelEducativo,
    NivelValidado,
    Nino,
    ObjetivoAprendizaje,
    Observacion,
    Semestre,
)
from registro.permisos import ninos_que_valida

JUNIO = date(2026, 6, 1)


def _ficha(client, nino):
    return client.get(reverse("ficha", args=[nino.pk]))


def _seccion(html, sigla, siguiente=None):
    inicio = html.index(f'id="nucleo-{sigla}"')
    return html[inicio:html.index(f'id="nucleo-{siguiente}"')] if siguiente else html[inicio:]


# --- Acceso y permisos -------------------------------------------------------------------


def test_ninos_que_valida_son_solo_los_de_sus_cursos(nino, educadora, otra_educadora, asistente_del_curso,
                                                    directora_del_jardin):
    assert list(ninos_que_valida(educadora)) == [nino]
    for usuaria in (otra_educadora, asistente_del_curso, directora_del_jardin):
        assert not ninos_que_valida(usuaria).exists()


def test_la_educadora_ve_la_ficha_con_formulario_y_enlace_a_metas(client, nino, curso, educadora, descriptores):
    client.force_login(educadora)
    html = _ficha(client, nino).content.decode()
    assert "Pedro Salinas" in html and curso.nombre in html
    assert f'href="{reverse("curso", args=[curso.pk])}"' in html
    assert f'href="{reverse("metas", args=[curso.pk])}"' in html
    assert html.count("Guardar nivel") == 3  # un formulario por núcleo


@pytest.mark.parametrize("rol", ["asistente_del_curso", "directora_del_jardin"])
def test_asistente_y_directora_ven_la_ficha_sin_formulario(client, nino, request, rol):
    client.force_login(request.getfixturevalue(rol))
    respuesta = _ficha(client, nino)
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Pedro Salinas" in html
    assert "Guardar nivel" not in html and "Editar metas del curso" not in html


def test_una_educadora_ajena_o_un_nino_inexistente_dan_404(client, nino, otra_educadora, educadora):
    client.force_login(otra_educadora)
    assert _ficha(client, nino).status_code == 404
    client.force_login(educadora)
    assert client.get(reverse("ficha", args=[nino.pk + 999])).status_code == 404


def test_sin_sesion_redirige_al_login(client, nino, curso):
    urls = [
        reverse("ficha", args=[nino.pk]),
        reverse("fijar_nivel", args=[nino.pk, "IA"]),
        reverse("metas", args=[curso.pk]),
    ]
    for url in urls:
        for respuesta in (client.get(url), client.post(url, {})):
            assert respuesta.status_code == 302 and reverse("login") in respuesta["Location"]


# --- La rúbrica en cada núcleo ---------------------------------------------------------------


def test_cada_nucleo_muestra_su_nivel_y_la_rubrica(client, nino, educadora, descriptores, nucleos):
    NivelValidado.objects.create(nino=nino, nucleo=nucleos[0], nivel=3, fecha=JUNIO, validado_por=educadora)
    client.force_login(educadora)
    html = _ficha(client, nino).content.decode()

    posiciones = [html.index(f'id="nucleo-{s}"') for s in ("IA", "LV", "PM")]
    assert posiciones == sorted(posiciones)

    ia = _seccion(html, "IA", "LV")
    assert "Nivel actual: <strong>3 · Desarrollando</strong>" in ia
    assert "Descripción IA 3" in ia and "Conducta IA 3" in ia
    assert "<summary>Ejemplos de registro</summary>" in ia and "Ejemplo IA 3 a" in ia
    assert "Qué observar después" in ia and "Descripción IA 4" in ia and "Conducta IA 4" in ia
    assert "Rúbrica provisoria" not in ia

    lv = _seccion(html, "LV", "PM")
    assert "Rúbrica provisoria" in lv and "Descripción LV 1" in lv
    assert "Nivel actual: <strong>1</strong>" in lv  # "1", no "1 · Nivel 1"

    pm = _seccion(html, "PM")
    assert "Rúbrica provisoria" in pm
    assert "Sin descriptor en la rúbrica para este nivel" in pm
    assert "Qué observar después" not in pm


def test_en_el_nivel_maximo_no_hay_que_observar_despues(client, nino, educadora, descriptores, nucleos):
    NivelValidado.objects.create(nino=nino, nucleo=nucleos[0], nivel=8, fecha=JUNIO, validado_por=educadora)
    client.force_login(educadora)
    ia = _seccion(_ficha(client, nino).content.decode(), "IA", "LV")
    assert "8 · Profundizando" in ia
    assert "Qué observar después" not in ia


def test_los_pasos_sugeridos_aparecen_solo_si_existen(client, nino, educadora, descriptores, nucleos):
    client.force_login(educadora)
    assert "Pasos sugeridos" not in _ficha(client, nino).content.decode()
    DescriptorNivel.objects.filter(nucleo=nucleos[0], nivel=1).update(pasos_sugeridos="Proponer juegos de turnos.")
    html = _ficha(client, nino).content.decode()
    assert "Pasos sugeridos" in html and "Proponer juegos de turnos." in html


# --- Evolución, evidencia y observaciones -----------------------------------------------------


def test_evidencia_por_oa_y_observaciones_aceptadas(client, nino, educadora, nucleos, observar_en):
    ia, lv, _pm = nucleos
    oa1 = ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, numero=1, texto="a")
    ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, numero=2, texto="b")
    observar_en(nino, date(2026, 9, 1), [lv], cita="Relató un cuento.", oas=[oa1])
    observar_en(nino, date(2026, 10, 1), [lv], cita="Nombró a sus compañeros.", oas=[oa1])
    observar_en(nino, date(2026, 10, 2), [lv], cita="Pendiente.", estado=Observacion.Estado.PENDIENTE)
    observar_en(nino, date(2026, 10, 3), [lv], cita="Grupal.", grupal=True)
    observar_en(nino, date(2026, 10, 4), [ia], cita="Se vistió solo.")

    client.force_login(educadora)
    html = _ficha(client, nino).content.decode()
    lv_html = _seccion(html, "LV", "PM")

    assert "OA 1 LV" in lv_html and "01-10-2026" in lv_html
    assert "1 de 2 OA con evidencia" in lv_html
    assert "Sin evidencia todavía: sugerencia de qué observar" in lv_html  # OA 2 LV
    assert lv_html.index("Nombró a sus compañeros.") < lv_html.index("Relató un cuento.")
    for ajena in ("Pendiente.", "Grupal.", "Se vistió solo."):
        assert ajena not in lv_html
    assert "<svg" in lv_html
    assert "Sin observaciones aceptadas." in _seccion(html, "PM")


def test_escapa_citas_y_comentarios(client, nino, educadora, nucleos, observar_en):
    observar_en(nino, date(2026, 10, 1), [nucleos[0]], cita="<script>alert(1)</script>")
    NivelValidado.objects.create(nino=nino, nucleo=nucleos[0], nivel=2, fecha=date(2026, 10, 1),
                                 validado_por=educadora, comentario="<b>ok</b>")
    client.force_login(educadora)
    html = _ficha(client, nino).content.decode()
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html
    assert "<b>ok</b>" not in html


def test_la_cantidad_de_consultas_no_crece(nino, educadora, nucleos, observar_en):
    def contar():
        fresco = Nino.objects.get(pk=nino.pk)
        with CaptureQueriesContext(connection) as consultas:
            armar_ficha(fresco, educadora)
        return len(consultas)

    # Con cero observaciones Django se salta la consulta del prefetch; se parte con una.
    observar_en(nino, date(2026, 3, 10), nucleos)
    antes = contar()
    for mes in range(4, 11):
        for nucleo in nucleos:
            NivelValidado.objects.create(nino=nino, nucleo=nucleo, nivel=2, fecha=date(2026, mes, 1),
                                         validado_por=educadora)
        observar_en(nino, date(2026, mes, 2), nucleos)
    assert contar() == antes


# --- Situación del curso (alertas.py, Task 2) ---------------------------------------------------


@pytest.fixture
def rezagado(curso, nucleos, educadora, observar_en):
    """Un niño en su semestre 3 (esperado 5) con nivel 1 en IA, y dos pares en nivel 4 (mediana 4).

    LV tiene una observación de hace 20 días; IA y PM nunca tuvieron.
    """
    hoy = timezone.localdate()
    ingreso = hoy - timedelta(days=400)
    for i, (inicio, fin) in enumerate([(0, 150), (180, 330), (360, 430)], start=1):
        Semestre.objects.create(nombre=f"S{i}", inicio=ingreso + timedelta(days=inicio),
                                fin=ingreso + timedelta(days=fin))
    for semestre, nivel in {1: 1, 2: 3, 3: 5, 4: 7}.items():
        MetaSemestre.objects.create(curso=curso, semestre_permanencia=semestre, nivel_esperado=nivel)
    ia, lv, _pm = nucleos
    nino = Nino.objects.create(curso=curso, nombre="Rubí Contreras", fecha_ingreso=ingreso)
    for nombre in ("Par Uno", "Par Dos"):
        par = Nino.objects.create(curso=curso, nombre=nombre, fecha_ingreso=ingreso)
        NivelValidado.objects.create(nino=par, nucleo=ia, nivel=4, fecha=hoy, validado_por=educadora)
    observar_en(nino, hoy - timedelta(days=20), [lv])
    return nino


def test_la_ficha_muestra_esperado_mediana_senales_y_avisos(client, rezagado, educadora):
    client.force_login(educadora)
    html = _ficha(client, rezagado).content.decode()

    ia = _seccion(html, "IA", "LV")
    assert "Nivel esperado: 5" in ia and "Mediana del curso: 4" in ia
    assert 'class="senal senal-alerta">Revisar: 3 niveles bajo la mediana del curso' in ia
    assert 'class="senal senal-alerta">Revisar: 4 niveles bajo lo esperado' in ia
    assert ia.index("bajo la mediana del curso") < ia.index("bajo lo esperado")  # pares primero
    assert "Sin observaciones aceptadas en este núcleo" in ia

    lv = _seccion(html, "LV", "PM")
    assert "Mediana del curso: 1" in lv
    assert "bajo la mediana del curso" not in lv
    assert "Sin observaciones aceptadas en los últimos 14 días" in lv


def test_subir_un_nivel_a_mano_hace_desaparecer_la_alerta(client, rezagado, educadora):
    client.force_login(educadora)
    respuesta = client.post(reverse("fijar_nivel", args=[rezagado.pk, "IA"]), {"IA-nivel": "4"},
                            HTTP_HX_REQUEST="true")
    html = respuesta.content.decode()
    assert "Nivel guardado: 4." in html
    assert "senal-alerta" not in html
    assert "bajo la mediana del curso" not in html and "bajo lo esperado" not in html
    assert "Sin observaciones aceptadas en este núcleo" in html  # el aviso de datos sigue


def test_editar_metas_cambia_las_alertas(client, rezagado, curso, educadora):
    client.force_login(educadora)
    assert "Revisar: 4 niveles bajo lo esperado" in _ficha(client, rezagado).content.decode()

    metas = {"semestre_1": "1", "semestre_2": "1", "semestre_3": "1", "semestre_4": "7"}
    client.post(reverse("metas", args=[curso.pk]), metas)

    ia = _seccion(_ficha(client, rezagado).content.decode(), "IA", "LV")
    assert "Nivel esperado: 1" in ia
    assert "bajo lo esperado" not in ia
    assert "Revisar: 3 niveles bajo la mediana del curso" in ia  # la de pares no depende de las metas


def test_la_ficha_y_la_tabla_del_curso_muestran_las_mismas_senales(client, rezagado, curso, educadora):
    client.force_login(educadora)
    tabla = client.get(reverse("curso", args=[curso.pk])).content.decode()
    ficha = _ficha(client, rezagado).content.decode()
    for texto in ("Revisar: 3 niveles bajo la mediana del curso", "Revisar: 4 niveles bajo lo esperado"):
        assert texto in tabla and texto in ficha


# --- Fortalezas primero (Política de Calidad, pp. 42 y 52-54) ------------------------------


def test_la_ficha_muestra_lo_logrado_antes_que_lo_pendiente(client, educadora, nino, nucleos, descriptores, observar_en):
    from django.urls import reverse
    from django.utils import timezone

    from registro.models import Apoyo, NivelEducativo, ObjetivoAprendizaje

    ia = nucleos[0]
    oa = ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=ia, numero=1, texto="Comunicar.")
    ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=ia, numero=2, texto="Otro.")
    obs = observar_en(nino, timezone.localdate(), [ia], cita="Se puso la chaqueta solo", oas=[oa])
    obs.apoyo = Apoyo.AUTONOMO
    obs.save(update_fields=["apoyo"])
    observar_en(nino, timezone.localdate(), [ia], cita="Pidió ayuda para ordenar")

    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[nino.pk])).content.decode()
    seccion = html[html.index('id="nucleo-IA"'):]
    logros = seccion.index("Lo que ya muestra")
    assert logros < seccion.index("El nivel actual en la rúbrica") < seccion.index("Qué observar después")
    assert "Se puso la chaqueta solo" in seccion[logros:seccion.index("El nivel actual en la rúbrica")]
    assert "Pidió ayuda para ordenar" not in seccion[logros:seccion.index("El nivel actual en la rúbrica")]
    assert "Con evidencia en 1 OA" in seccion


def test_sin_observaciones_lo_logrado_lo_dice_sin_juzgar(client, educadora, nino, nucleos, descriptores):
    from django.urls import reverse

    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[nino.pk])).content.decode()
    assert "Todavía no hay observaciones aceptadas en este núcleo." in html
