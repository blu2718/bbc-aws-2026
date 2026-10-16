"""Solicitud y reintento desde la ficha: permisos, POST y doble envío."""
import pytest
from django.urls import reverse

from registro.models import PropuestaNivel


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture(autouse=True)
def _rubrica_completa(rubrica, descriptores):
    """IA con rúbrica completa, como en Transición: sin ella no se encolan propuestas (fallarían siempre)."""


def test_solicitar_dos_veces_reutiliza_y_responde_parcial(client, nino, nucleos, educadora):
    client.force_login(educadora)
    url = reverse("solicitar_propuesta", args=[nino.pk, "IA"])
    for _ in range(2):
        respuesta = client.post(url, HTTP_HX_REQUEST="true")
        assert respuesta.status_code == 200
        html = respuesta.content.decode()
        assert '<section id="nucleo-IA"' in html and "<html" not in html
        assert "Propuesta en cola" in html
    assert PropuestaNivel.objects.count() == 1


def test_sin_htmx_redirige_y_exige_post(client, nino, educadora):
    client.force_login(educadora)
    url = reverse("solicitar_propuesta", args=[nino.pk, "IA"])
    assert client.get(url).status_code == 405
    respuesta = client.post(url)
    assert respuesta.status_code == 302 and respuesta["Location"].endswith("#nucleo-IA")


@pytest.mark.parametrize("rol", ["asistente_del_curso", "directora_del_jardin", "otra_educadora"])
def test_otros_roles_no_pueden_solicitar_ni_reintentar(client, request, nino, nucleos, rol):
    propuesta = PropuestaNivel.objects.create(nino=nino, nucleo=nucleos[0], estado="error")
    client.force_login(request.getfixturevalue(rol))
    assert client.post(reverse("solicitar_propuesta", args=[nino.pk, "IA"])).status_code == 404
    assert client.post(reverse("reintentar_propuesta", args=[propuesta.pk])).status_code == 404
    html = client.get(reverse("ficha", args=[nino.pk])).content.decode()
    assert "Solicitar propuesta</button>" not in html


def test_reintento_explicito_conserva_error_anterior_y_no_duplica(client, nino, nucleos, educadora):
    anterior = PropuestaNivel.objects.create(nino=nino, nucleo=nucleos[0], estado="error", error="Fallo recuperable")
    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[nino.pk])).content.decode()
    assert "Reintentar propuesta" in html and "Fallo recuperable" in html
    url = reverse("reintentar_propuesta", args=[anterior.pk])
    assert client.get(url).status_code == 405
    assert client.post(url).status_code == 302
    assert client.post(url).status_code == 302
    assert PropuestaNivel.objects.filter(estado="solicitada").count() == 1
    anterior.refresh_from_db()
    assert anterior.estado == "error"


def test_el_boton_tiene_csrf_y_solicitud_exige_login(client, nino, educadora):
    url = reverse("solicitar_propuesta", args=[nino.pk, "IA"])
    assert client.post(url).status_code == 302
    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[nino.pk])).content.decode()
    assert f'hx-post="{url}"' in html and 'name="csrfmiddlewaretoken"' in html
    assert client.post(reverse("solicitar_propuesta", args=[nino.pk, "DESCONOCIDO"])).status_code == 404
