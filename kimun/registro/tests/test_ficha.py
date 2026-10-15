"""Ficha del niño (Task 3, spec task3-ficha-nino): acceso, rúbrica, evidencia y situación del curso.

La situación (esperado, mediana y señales) viene de `alertas.py`, de la Task 2.
Se prueba que la ficha funciona sin ese módulo y que, con un doble que cumple
la interfaz de la spec, la muestra.
"""
import builtins
import sys
from datetime import date
from types import ModuleType, SimpleNamespace

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from registro.ficha import _situaciones, armar_ficha
from registro.models import DescriptorNivel, NivelEducativo, NivelValidado, Nino, ObjetivoAprendizaje, Observacion
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


def test_la_cantidad_de_consultas_no_crece(nino, educadora, nucleos, observar_en, sin_alertas):
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


def test_sin_alertas_la_ficha_omite_esperado_mediana_y_senales(client, nino, educadora, sin_alertas):
    client.force_login(educadora)
    respuesta = _ficha(client, nino)
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Nivel esperado" not in html and "Mediana del curso" not in html and "senal-" not in html
    assert all(nf.situacion is None for nf in armar_ficha(nino, educadora).nucleos)


def _doble_alertas(nino_id):
    """Módulo con la interfaz de la spec (sección 2): situacion_del_curso, SituacionNucleo y Senal."""
    alerta = SimpleNamespace(tipo="esperado", brecha=4, gravedad=SimpleNamespace(value="alerta"),
                             texto="Revisar: 4 niveles bajo lo esperado")
    aviso = SimpleNamespace(tipo="pares", brecha=2, gravedad=SimpleNamespace(value="aviso"),
                            texto="Revisar: 2 niveles bajo sus pares")
    ia = SimpleNamespace(nivel=1, esperado=5, mediana_curso=3.5, senales=[alerta, aviso],
                         datos=SimpleNamespace(value="desactualizados"))
    lv = SimpleNamespace(nivel=1, esperado=5, mediana_curso=1, senales=[], datos=SimpleNamespace(value="sin_datos"))
    llamadas = []

    def situacion_del_curso(curso, hoy=None):
        llamadas.append(curso)
        return {nino_id: {"IA": ia, "LV": lv}}

    modulo = ModuleType("registro.alertas")
    modulo.situacion_del_curso = situacion_del_curso
    return modulo, llamadas


def test_con_alertas_la_ficha_muestra_la_situacion(client, nino, educadora, monkeypatch):
    doble, llamadas = _doble_alertas(nino.pk)
    monkeypatch.setitem(sys.modules, "registro.alertas", doble)
    client.force_login(educadora)
    html = _ficha(client, nino).content.decode()
    assert len(llamadas) == 1

    ia = _seccion(html, "IA", "LV")
    assert "Nivel esperado: 5" in ia and "Mediana del curso: 3,5" in ia
    assert 'class="senal senal-alerta">Revisar: 4 niveles bajo lo esperado' in ia
    assert 'class="senal senal-aviso">Revisar: 2 niveles bajo sus pares' in ia
    assert "Sin observaciones aceptadas en los últimos 14 días" in ia
    assert "Sin observaciones aceptadas en este núcleo" in _seccion(html, "LV", "PM")
    # PM no viene en el resultado: sin bloque de situación.
    assert "Nivel esperado" not in _seccion(html, "PM")


def test_un_error_dentro_de_alertas_no_se_oculta(curso, monkeypatch):
    monkeypatch.delitem(sys.modules, "registro.alertas", raising=False)
    importar = builtins.__import__

    def importar_con_falla(nombre, *args, **kwargs):
        if nombre == "alertas" and args and args[-1] == 1:
            raise ModuleNotFoundError("No module named 'boto3'", name="boto3")
        return importar(nombre, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importar_con_falla)
    with pytest.raises(ModuleNotFoundError):
        _situaciones(curso, date(2026, 10, 15))
