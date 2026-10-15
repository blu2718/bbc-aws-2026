"""Pantallas I y II de diseno-interfaz.jpg: registrar un suceso y ver cómo quedó ordenado."""
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from registro import views_registro
from registro.models import Captura, NivelValidado, Nino, Observacion
from registro.pantallas import texto_edad
from registro.tests.test_capturas import JPEG, ClienteFalso, cruda

HTMX = {"HX-Request": "true"}


@pytest.fixture(autouse=True)
def _media_temporal(settings, tmp_path):
    """Los archivos subidos van a una carpeta temporal, no a kimun/media."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def pedro(curso, nucleos):
    return Nino.objects.create(curso=curso, nombre="Pedro Salinas", fecha_ingreso=date(2026, 3, 2),
                               fecha_nacimiento=date(2020, 5, 14))


@pytest.fixture
def con_bedrock_falso(monkeypatch):
    """Reemplaza a Bedrock en las vistas; devuelve una función para fijar sus respuestas."""
    cliente = ClienteFalso()
    monkeypatch.setattr(views_registro, "crear_cliente", lambda: cliente)

    def responder(*respuestas):
        cliente.respuestas.extend(respuestas)
        return cliente

    return responder


def _registrar(client, curso, **datos):
    return client.post(reverse("registrar", args=[curso.pk]), datos)


# --- Pantalla I: registrar ------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["educadora", "asistente_del_curso"])
def test_la_educadora_y_la_asistente_ven_la_pregunta(client, curso, request, rol):
    client.force_login(request.getfixturevalue(rol))
    respuesta = client.get(reverse("registrar", args=[curso.pk]))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "¿Qué quieres registrar?" in html
    assert 'name="texto"' in html and 'name="foto"' in html and 'enctype="multipart/form-data"' in html


@pytest.mark.parametrize("rol", ["directora_del_jardin", "otra_educadora"])
def test_quien_no_registra_en_el_curso_recibe_404(client, curso, request, rol):
    client.force_login(request.getfixturevalue(rol))
    assert client.get(reverse("registrar", args=[curso.pk])).status_code == 404
    assert _registrar(client, curso, texto="Pedro saltó.").status_code == 404
    assert not Captura.objects.exists()


def test_un_texto_crea_una_captura_pendiente_y_lleva_a_su_pagina(client, curso, asistente_del_curso):
    client.force_login(asistente_del_curso)
    respuesta = _registrar(client, curso, texto="  Pedro clasificó hojas por color.  ")

    captura = Captura.objects.get()
    assert respuesta.status_code == 302 and respuesta["Location"] == reverse("captura", args=[captura.pk])
    assert captura.tipo == Captura.Tipo.TEXTO and captura.autora == asistente_del_curso
    assert captura.texto_original == "Pedro clasificó hojas por color."
    assert captura.estado == Captura.Estado.PENDIENTE


def test_sin_texto_ni_archivo_muestra_el_error(client, curso, educadora):
    client.force_login(educadora)
    respuesta = _registrar(client, curso, texto="   ")
    assert respuesta.status_code == 400
    assert "Escribe lo que pasó, adjunta una foto o graba un audio." in respuesta.content.decode()
    assert not Captura.objects.exists()


def test_una_foto_se_guarda_con_un_nombre_al_azar(client, curso, educadora):
    client.force_login(educadora)
    foto = SimpleUploadedFile("Pedro Salinas postit.jpg", JPEG, content_type="image/jpeg")
    _registrar(client, curso, foto=foto, texto="En el patio")

    captura = Captura.objects.get()
    assert captura.tipo == Captura.Tipo.FOTO and captura.texto_original == "En el patio"
    assert captura.archivo.name.endswith(".jpg") and "Pedro" not in captura.archivo.name


def test_un_archivo_que_no_es_imagen_se_rechaza(client, curso, educadora):
    client.force_login(educadora)
    falso = SimpleUploadedFile("foto.jpg", b"<html>no soy una foto</html>", content_type="image/jpeg")
    respuesta = _registrar(client, curso, foto=falso)
    assert respuesta.status_code == 400
    assert "La foto debe ser JPEG, PNG, GIF o WebP." in respuesta.content.decode()
    assert not Captura.objects.exists()


# --- Pantalla II: el suceso ---------------------------------------------------------------------


def test_la_pagina_procesa_la_captura_y_muestra_una_tarjeta_por_nino(client, curso, educadora, pedro, nucleos,
                                                                     con_bedrock_falso):
    _ia, _lv, pm = nucleos
    NivelValidado.objects.create(nino=pedro, nucleo=pm, nivel=3, fecha=date(2026, 9, 30), validado_por=educadora)
    con_bedrock_falso({"observaciones": [
        cruda("Pedro", "Pedro clasificó hojas por color.", nucleos=["PM"], efecto="avance"),
        cruda("Mateo", "Mateo lo ayudó."),
    ]})
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas por color y Mateo lo ayudó.")
    captura = Captura.objects.get()

    pagina = client.get(reverse("captura", args=[captura.pk])).content.decode()
    assert "Pedro clasificó hojas por color y Mateo lo ayudó." in pagina  # la burbuja
    assert f'hx-post="{reverse("captura_procesar", args=[captura.pk])}"' in pagina

    html = client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX).content.decode()
    assert "Pedro Salinas" in html
    assert f"Edad: {texto_edad(pedro.fecha_nacimiento, timezone.localdate())}" in html
    assert "Pensamiento Matemático</strong>: nivel 3" in html
    assert "Muestra avance" in html
    assert "en la nota dice «Mateo»" in html and "¿A quién corresponde?" in html
    assert 'name="vista" value="suceso"' in html  # las acciones vuelven a esta tarjeta
    assert '<li id="contador-pendientes" hx-swap-oob="true">' in html
    assert Observacion.objects.filter(captura=captura, estado=Observacion.Estado.PENDIENTE).count() == 2


def test_la_asistente_ve_el_resultado_sin_acciones(client, curso, asistente_del_curso, pedro, con_bedrock_falso):
    con_bedrock_falso({"observaciones": [cruda("Pedro")]})
    client.force_login(asistente_del_curso)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()

    html = client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX).content.decode()
    assert "Pedro Salinas" in html
    assert "La educadora la revisará antes de que cuente en la ficha." in html
    assert reverse("observacion_aceptar", args=[captura.observaciones.get().pk]) not in html


def test_aceptar_desde_la_tarjeta_del_suceso_devuelve_la_tarjeta(client, curso, educadora, pedro, con_bedrock_falso):
    con_bedrock_falso({"observaciones": [cruda("Pedro")]})
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()
    client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX)
    obs = captura.observaciones.get()

    html = client.post(reverse("observacion_aceptar", args=[obs.pk]), {"vista": "suceso"}, headers=HTMX).content.decode()
    assert 'class="suceso suceso-resuelto"' in html and "Aceptada:" in html and "Ver su perfil" in html
    obs.refresh_from_db()
    assert obs.estado == Observacion.Estado.ACEPTADA

    # Sin HTMX vuelve a la página de la captura, no a la revisión.
    otra = Observacion.objects.create(captura=captura, nino=pedro, fecha=timezone.localdate(), cita="Otra.")
    respuesta = client.post(reverse("observacion_descartar", args=[otra.pk]), {"vista": "suceso"})
    assert respuesta["Location"] == f'{reverse("captura", args=[captura.pk])}#obs-{otra.pk}'


def test_un_error_de_bedrock_se_muestra_con_reintentar(client, curso, educadora, con_bedrock_falso):
    from registro.ia import ErrorBedrock

    con_bedrock_falso(ErrorBedrock("Unable to locate credentials"))
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()

    html = client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX).content.decode()
    # Sin credenciales se explica que falta la conexión con la IA; el detalle técnico queda en el log y en el admin.
    assert "Kimün no está conectado a la IA en este servidor." in html
    assert "Unable to locate credentials" not in html
    assert reverse("captura_reintentar_suceso", args=[captura.pk]) in html

    html = client.post(reverse("captura_reintentar_suceso", args=[captura.pk]), headers=HTMX).content.decode()
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE
    assert f'hx-post="{reverse("captura_procesar", args=[captura.pk])}"' in html


def test_permisos_de_la_captura(client, curso, educadora, asistente_del_curso, directora_del_jardin, otra_educadora):
    captura = Captura.objects.create(curso=curso, autora=asistente_del_curso, tipo=Captura.Tipo.TEXTO, texto_original="x")
    url, procesar = reverse("captura", args=[captura.pk]), reverse("captura_procesar", args=[captura.pk])

    for quien in (educadora, asistente_del_curso, directora_del_jardin):
        client.force_login(quien)
        assert client.get(url).status_code == 200
    # La directora ve el curso, pero no registra: no dispara el procesamiento.
    assert client.post(procesar, headers=HTMX).status_code == 404

    client.force_login(otra_educadora)
    assert client.get(url).status_code == 404
    assert client.post(procesar, headers=HTMX).status_code == 404



def test_otro_error_de_bedrock_muestra_el_mensaje_general(client, curso, educadora, con_bedrock_falso):
    con_bedrock_falso("no es json")
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()

    html = client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX).content.decode()
    assert "No se pudo ordenar el registro." in html and "no está conectado a la IA" not in html


# --- Todo el curso y la pregunta de contexto ---------------------------------------------------------


def test_todo_el_curso_se_muestra_en_una_tarjeta_y_se_acepta_de_una_vez(client, curso, educadora, pedro, nucleos,
                                                                       con_bedrock_falso):
    Nino.objects.create(curso=curso, nombre="Rubí Contreras", fecha_ingreso=date(2026, 3, 2))
    con_bedrock_falso({"observaciones": [cruda(None, "Todos bailaron.", nucleos=["PM"], todo_el_curso=True)],
                       "pregunta": None})
    client.force_login(educadora)
    _registrar(client, curso, texto="Todos bailaron.")
    captura = Captura.objects.get()

    html = client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX).content.decode()
    assert "Todo el curso" in html and "Queda en la ficha de 2 niños" in html
    assert html.count('class="suceso suceso-curso"') == 1 and "Aceptar para todo el curso" in html

    respuesta = client.post(reverse("captura_aceptar_todas", args=[captura.pk]), {"vista": "suceso"})
    assert respuesta["Location"] == reverse("captura", args=[captura.pk])
    assert captura.observaciones.filter(estado=Observacion.Estado.ACEPTADA).count() == 2


def test_responder_la_pregunta_vuelve_a_ordenar_la_nota(client, curso, educadora, pedro, con_bedrock_falso):
    cliente = con_bedrock_falso(
        {"observaciones": [cruda("Pedro", "Pedro se peleó.", efecto="por_reforzar")], "pregunta": "¿Con quién se peleó?"},
        {"observaciones": [cruda("Pedro", "Pedro se peleó con Rubí y después le pidió perdón.", efecto="avance")],
         "pregunta": None},
    )
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro se peleó.")
    captura = Captura.objects.get()
    html = client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX).content.decode()
    assert "Kimün necesita un dato más:" in html and "¿Con quién se peleó?" in html

    client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "Con Rubí; después le pidió perdón."})
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE and captura.pregunta == ""
    assert captura.texto_original.endswith("Contexto agregado: Con Rubí; después le pidió perdón.")
    assert not captura.observaciones.exists()

    client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX)
    assert "Contexto agregado" in cliente.llamadas[-1]["mensaje"]
    assert captura.observaciones.get().efecto == "avance"


def test_no_se_agrega_contexto_si_ya_hay_observaciones_aceptadas(client, curso, educadora, pedro, con_bedrock_falso):
    con_bedrock_falso({"observaciones": [cruda("Pedro")], "pregunta": "¿Dónde fue?"})
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()
    client.post(reverse("captura_procesar", args=[captura.pk]), headers=HTMX)
    captura.observaciones.update(estado=Observacion.Estado.ACEPTADA)

    client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "En el patio."})

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA and "Contexto agregado" not in captura.texto_original
