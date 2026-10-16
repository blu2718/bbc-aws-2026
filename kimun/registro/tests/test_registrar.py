"""Pantallas I y II de diseno-interfaz.jpg: registrar un suceso y ver cómo quedó ordenado."""
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from registro import procesamiento
from registro.models import Captura, Jardin, NivelValidado, Nino, Observacion
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
def con_bedrock_falso():
    """Bedrock falso para el proceso de fondo; devuelve una función para fijar sus respuestas."""
    cliente = ClienteFalso()

    def responder(*respuestas):
        cliente.respuestas.extend(respuestas)
        return cliente

    responder.cliente = cliente
    return responder


def _registrar(client, curso, **datos):
    return client.post(reverse("registrar", args=[curso.pk]), datos)


def _ordenar(client, captura, bedrock):
    """Lo que hace `procesar_capturas` en segundo plano y, después, la consulta de estado de la página."""
    list(procesamiento.procesar_pendientes(cliente=bedrock.cliente))
    return client.get(reverse("captura_estado", args=[captura.pk]), headers=HTMX)


# --- Pantalla I: registrar ------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["educadora", "asistente_del_curso"])
def test_la_educadora_y_la_asistente_ven_la_pregunta(client, curso, request, rol):
    client.force_login(request.getfixturevalue(rol))
    respuesta = client.get(reverse("registrar", args=[curso.pk]))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "¿Qué quieres registrar?" in html
    assert 'name="texto"' in html and 'name="foto"' in html and 'enctype="multipart/form-data"' in html


def test_la_directora_del_jardin_registra(client, curso, directora_del_jardin):
    """La directora registra en los cursos de su jardín (Task 12), pero no revisa ni valida."""
    client.force_login(directora_del_jardin)
    assert "¿Qué quieres registrar?" in client.get(reverse("registrar", args=[curso.pk])).content.decode()
    respuesta = _registrar(client, curso, texto="Pedro saltó.")
    captura = Captura.objects.get()
    assert respuesta.status_code == 302 and respuesta["Location"] == reverse("captura", args=[captura.pk])
    assert captura.autora == directora_del_jardin


@pytest.mark.parametrize("rol", ["directora_de_otro_jardin", "otra_educadora"])
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
    assert f'hx-get="{reverse("captura_estado", args=[captura.pk])}"' in pagina

    html = _ordenar(client, captura, con_bedrock_falso).content.decode()
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

    html = _ordenar(client, captura, con_bedrock_falso).content.decode()
    assert "Pedro Salinas" in html
    assert "La educadora la revisará antes de que cuente en la ficha." in html
    assert reverse("observacion_aceptar", args=[captura.observaciones.get().pk]) not in html


def test_aceptar_desde_la_tarjeta_del_suceso_devuelve_la_tarjeta(client, curso, educadora, pedro, con_bedrock_falso):
    con_bedrock_falso({"observaciones": [cruda("Pedro")]})
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()
    _ordenar(client, captura, con_bedrock_falso)
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

    html = _ordenar(client, captura, con_bedrock_falso).content.decode()
    # Sin credenciales se explica que falta la conexión con la IA; el detalle técnico queda en el log y en el admin.
    assert "Kimün no está conectado a la IA en este servidor." in html
    assert "Unable to locate credentials" not in html
    assert reverse("captura_reintentar_suceso", args=[captura.pk]) in html

    html = client.post(reverse("captura_reintentar_suceso", args=[captura.pk]), headers=HTMX).content.decode()
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE
    assert f'hx-get="{reverse("captura_estado", args=[captura.pk])}"' in html


def test_permisos_de_la_captura(client, curso, educadora, asistente_del_curso, directora_del_jardin, otra_educadora,
                                django_user_model, con_bedrock_falso):
    con_bedrock_falso({"observaciones": []})
    captura = Captura.objects.create(curso=curso, autora=asistente_del_curso, tipo=Captura.Tipo.TEXTO, texto_original="x")
    url, estado = reverse("captura", args=[captura.pk]), reverse("captura_estado", args=[captura.pk])

    for quien in (educadora, asistente_del_curso, directora_del_jardin):
        client.force_login(quien)
        assert client.get(url).status_code == 200
        assert client.get(estado, headers=HTMX).status_code == 200

    otra_directora = django_user_model.objects.create_user("elena", password="clave-de-prueba-123")
    Jardin.objects.create(nombre="Otro jardín", directora=otra_directora)
    for quien in (otra_educadora, otra_directora):
        client.force_login(quien)
        assert client.get(url).status_code == 404
        assert client.get(estado, headers=HTMX).status_code == 404


def test_la_pagina_consulta_el_estado_sin_llamar_a_bedrock(client, curso, educadora, con_bedrock_falso):
    """La petición web nunca espera a Bedrock: una foto puede tardar más que los timeouts de CloudFront y Gunicorn."""
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()

    html = client.get(reverse("captura_estado", args=[captura.pk]), headers=HTMX).content.decode()
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE and con_bedrock_falso.cliente.llamadas == []
    assert 'hx-trigger="load delay:2s"' in html and "Ordenando el registro" in html
    assert client.post(reverse("captura_estado", args=[captura.pk]), headers=HTMX).status_code == 405
    # Sin HTMX vuelve a la página de la captura.
    assert client.get(reverse("captura_estado", args=[captura.pk]))["Location"] == reverse("captura", args=[captura.pk])



WEBM = b"\x1a\x45\xdf\xa3" + bytes(64)


def test_un_audio_espera_al_proceso_de_fondo_y_la_pagina_se_actualiza_sola(client, curso, educadora, pedro,
                                                                          con_bedrock_falso):
    """La página no transcribe (lo hace `procesar_capturas`), pero sigue preguntando hasta que esté listo."""
    con_bedrock_falso({"observaciones": [cruda("Pedro")]})
    client.force_login(educadora)
    _registrar(client, curso, audio=SimpleUploadedFile("grabacion.webm", WEBM, content_type="audio/webm"))
    captura = Captura.objects.get()
    assert captura.tipo == Captura.Tipo.AUDIO
    url_estado = reverse("captura_estado", args=[captura.pk])

    pagina = client.get(reverse("captura", args=[captura.pk])).content.decode()
    assert "Transcribiendo el audio" in pagina and f'hx-get="{url_estado}"' in pagina
    assert "todavía no está conectada" not in pagina

    # Mientras el proceso de fondo no termina, la respuesta vuelve a preguntar en unos segundos.
    html = client.get(url_estado, headers=HTMX).content.decode()
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE
    assert 'hx-trigger="load delay:3s"' in html and "Transcribiendo el audio" in html

    # Cuando el proceso de fondo la dejó procesada, la siguiente pregunta muestra las tarjetas.
    Captura.objects.filter(pk=captura.pk).update(estado=Captura.Estado.PROCESADA, texto_extraido="Pedro clasificó hojas.")
    Observacion.objects.create(captura=captura, nino=pedro, fecha=timezone.localdate(), cita="Pedro clasificó hojas.")
    html = client.get(url_estado, headers=HTMX).content.decode()
    assert "Pedro Salinas" in html and "hx-trigger" not in html.split('id="estado-captura"')[1].split("</div>")[0]


def test_otro_error_de_bedrock_muestra_el_mensaje_general(client, curso, educadora, con_bedrock_falso):
    con_bedrock_falso("no es json")
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()

    html = _ordenar(client, captura, con_bedrock_falso).content.decode()
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

    html = _ordenar(client, captura, con_bedrock_falso).content.decode()
    assert "Todo el curso" in html and "Queda en la ficha de 2 niños" in html
    assert html.count('class="suceso suceso-curso"') == 1 and "Aceptar para todo el curso" in html
    assert 'name="alcance" value="curso"' in html

    # Una observación individual de la misma nota no se acepta sin revisarla.
    individual = Observacion.objects.create(captura=captura, nino=pedro, fecha=timezone.localdate(), cita="Pedro mordió.")
    respuesta = client.post(reverse("captura_aceptar_todas", args=[captura.pk]), {"vista": "suceso", "alcance": "curso"})
    assert respuesta["Location"] == reverse("captura", args=[captura.pk])
    assert captura.observaciones.filter(estado=Observacion.Estado.ACEPTADA).count() == 2
    individual.refresh_from_db()
    assert individual.estado == Observacion.Estado.PENDIENTE

    # Desde la revisión, "Aceptar todas las de esta captura" sigue aceptando todas.
    client.post(reverse("captura_aceptar_todas", args=[captura.pk]))
    individual.refresh_from_db()
    assert individual.estado == Observacion.Estado.ACEPTADA


def test_responder_la_pregunta_vuelve_a_ordenar_la_nota(client, curso, educadora, pedro, con_bedrock_falso):
    cliente = con_bedrock_falso(
        {"observaciones": [cruda("Pedro", "Pedro se peleó.", efecto="por_reforzar")], "pregunta": "¿Con quién se peleó?"},
        {"observaciones": [cruda("Pedro", "Pedro se peleó con Rubí y después le pidió perdón.", efecto="avance")],
         "pregunta": None},
    )
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro se peleó.")
    captura = Captura.objects.get()
    html = _ordenar(client, captura, con_bedrock_falso).content.decode()
    assert "Kimün necesita un dato más:" in html and "¿Con quién se peleó?" in html

    client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "Con Rubí; después le pidió perdón."})
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE and captura.pregunta == ""
    assert captura.texto_original.endswith("Contexto agregado: Con Rubí; después le pidió perdón.")
    assert not captura.observaciones.exists()

    _ordenar(client, captura, con_bedrock_falso)
    assert "Contexto agregado" in cliente.llamadas[-1]["mensaje"]
    assert captura.observaciones.get().efecto == "avance"


def test_contexto_a_una_foto_sin_texto_legible_vuelve_a_ordenar_la_nota(client, curso, educadora, pedro,
                                                                       con_bedrock_falso):
    """La foto se leyó sin texto y se borró: al responder la pregunta, se ordena con la nota escrita."""
    cliente = con_bedrock_falso(
        {"texto": ""},
        {"observaciones": [cruda("Pedro", "Pedro empujó.")], "pregunta": "¿A quién empujó?"},
        {"observaciones": [cruda("Pedro", "Pedro empujó a Rubí y le pidió perdón.")], "pregunta": None},
    )
    client.force_login(educadora)
    _registrar(client, curso, foto=SimpleUploadedFile("nota.jpg", JPEG, content_type="image/jpeg"), texto="Pedro empujó.")
    captura = Captura.objects.get()
    assert "¿A quién empujó?" in _ordenar(client, captura, con_bedrock_falso).content.decode()
    captura.refresh_from_db()
    assert not captura.archivo and captura.texto_extraido == ""

    client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "A Rubí, y le pidió perdón."})
    _ordenar(client, captura, con_bedrock_falso)
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA, captura.error
    assert "Contexto agregado: A Rubí" in cliente.llamadas[-1]["mensaje"]


def test_no_se_agrega_contexto_si_ya_hay_observaciones_aceptadas(client, curso, educadora, pedro, con_bedrock_falso):
    con_bedrock_falso({"observaciones": [cruda("Pedro")], "pregunta": "¿Dónde fue?"})
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro clasificó hojas.")
    captura = Captura.objects.get()
    _ordenar(client, captura, con_bedrock_falso)
    captura.observaciones.update(estado=Observacion.Estado.ACEPTADA)

    client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "En el patio."})

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA and "Contexto agregado" not in captura.texto_original


# --- Dos personas responden la pregunta a la vez (rama fixes) ----------------------------


@pytest.fixture
def nota_con_pregunta(client, curso, educadora, pedro, con_bedrock_falso):
    con_bedrock_falso({"observaciones": [cruda("Pedro", "Pedro se peleó.")], "pregunta": "¿Con quién se peleó?"})
    client.force_login(educadora)
    _registrar(client, curso, texto="Pedro se peleó.")
    captura = Captura.objects.get()
    _ordenar(client, captura, con_bedrock_falso)
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA and captura.pregunta
    return captura


@pytest.fixture
def ambas_vieron_la_pregunta(monkeypatch):
    """Las dos cargaron la página cuando la nota estaba procesada: la comprobación previa pasa para ambas."""
    from registro import views_registro

    monkeypatch.setattr(views_registro, "puede_agregar_contexto", lambda captura: True)


def test_si_dos_responden_a_la_vez_solo_cuenta_la_primera(client, nota_con_pregunta, asistente_del_curso,
                                                         ambas_vieron_la_pregunta):
    captura = nota_con_pregunta
    client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "Con Rubí."})

    client.force_login(asistente_del_curso)
    respuesta = client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "Con Emilio."}, follow=True)

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE
    assert captura.texto_original.count("Contexto agregado") == 1 and "Con Rubí." in captura.texto_original
    assert "Otra persona acaba de sumar contexto" in respuesta.content.decode()


def test_si_aceptan_una_observacion_mientras_se_responde_no_se_toca_la_nota(client, nota_con_pregunta,
                                                                          ambas_vieron_la_pregunta):
    captura = nota_con_pregunta
    texto_antes = captura.texto_original
    captura.observaciones.update(estado=Observacion.Estado.ACEPTADA)

    respuesta = client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "En el patio."}, follow=True)

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA and captura.pregunta
    assert captura.texto_original == texto_antes
    assert captura.observaciones.filter(estado=Observacion.Estado.ACEPTADA).count() == 1
    assert "ya no se le puede sumar contexto" in respuesta.content.decode()
