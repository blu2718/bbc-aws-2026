"""Fijar el nivel de un niño desde la ficha (Task 3, spec task3-ficha-nino, requisitos 5 y 6)."""
import pytest
from django.urls import reverse
from django.utils import timezone

from registro.models import NivelValidado

HX = {"HTTP_HX_REQUEST": "true"}


def _url(nino, sigla="IA"):
    return reverse("fijar_nivel", args=[nino.pk, sigla])


def test_con_htmx_crea_historial_y_devuelve_la_seccion(client, nino, curso, educadora, descriptores, nucleos):
    client.force_login(educadora)
    datos = {"IA-nivel": "3", "IA-comentario": "Elige su ropa y se viste solo.",
             # Se ignoran: la fecha y la usuaria salen del servidor y de la sesión.
             "fecha": "2020-01-01", "validado_por": "999"}
    respuesta = client.post(_url(nino), datos, **HX)

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert '<section id="nucleo-IA"' in html and "<html" not in html
    assert '<p role="status" class="mensaje-ok">Nivel guardado: 3 · Desarrollando.</p>' in html

    nv = nino.nivel_actual(nucleos[0])
    assert (nv.nivel, nv.comentario, nv.validado_por, nv.fecha) == (
        3, "Elige su ropa y se viste solo.", educadora, timezone.localdate())
    assert NivelValidado.objects.filter(nino=nino, nucleo=nucleos[0]).count() == 2

    # La tabla del curso muestra el nivel nuevo.
    assert "<td>3 · Desarrollando</td>" in client.get(reverse("curso", args=[curso.pk])).content.decode()


def test_fijar_el_mismo_nivel_queda_como_nueva_validacion(client, nino, educadora, nucleos):
    client.force_login(educadora)
    client.post(_url(nino), {"IA-nivel": "1"}, **HX)
    assert NivelValidado.objects.filter(nino=nino, nucleo=nucleos[0]).count() == 2


def test_el_nivel_guardado_es_el_actual_aunque_haya_otro_del_mismo_dia(client, nino, educadora, nucleos):
    NivelValidado.objects.create(nino=nino, nucleo=nucleos[0], nivel=5, fecha=timezone.localdate(),
                                 validado_por=educadora)
    client.force_login(educadora)
    client.post(_url(nino), {"IA-nivel": "2"}, **HX)
    assert nino.nivel_actual(nucleos[0]).nivel == 2


@pytest.mark.parametrize("valor", ["9", "0", "abc", ""])
def test_un_nivel_invalido_no_cambia_el_historial(client, nino, educadora, valor):
    client.force_login(educadora)
    antes = NivelValidado.objects.count()
    respuesta = client.post(_url(nino), {"IA-nivel": valor}, **HX)
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Elige un nivel entre 1 y 8." in html and "<html" not in html
    assert NivelValidado.objects.count() == antes


def test_con_rubrica_de_9_niveles_se_puede_fijar_el_9(client, nino, educadora, rubrica, nucleos):
    rubrica.cantidad_niveles = 9
    rubrica.save()
    client.force_login(educadora)
    client.post(_url(nino), {"IA-nivel": "9"}, **HX)
    assert nino.nivel_actual(nucleos[0]).nivel == 9


def test_sin_htmx_un_nivel_valido_redirige_a_la_ficha(client, nino, educadora, descriptores):
    client.force_login(educadora)
    respuesta = client.post(_url(nino), {"IA-nivel": "4"})
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("ficha", args=[nino.pk]) + "#nucleo-IA"
    assert "Nivel guardado: 4 · Afianzando." in client.get(respuesta["Location"]).content.decode()


def test_sin_htmx_un_nivel_invalido_muestra_la_ficha_con_errores(client, nino, educadora):
    client.force_login(educadora)
    respuesta = client.post(_url(nino), {"IA-nivel": "12"})
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "<html" in html and "Elige un nivel entre 1 y 8." in html


@pytest.mark.parametrize("rol", ["asistente_del_curso", "directora_del_jardin", "otra_educadora"])
def test_solo_la_educadora_fija_niveles(client, nino, request, rol):
    client.force_login(request.getfixturevalue(rol))
    antes = NivelValidado.objects.count()
    assert client.post(_url(nino), {"IA-nivel": "3"}, **HX).status_code == 404
    assert NivelValidado.objects.count() == antes


def test_get_responde_405_y_una_sigla_inexistente_404(client, nino, educadora):
    client.force_login(educadora)
    assert client.get(_url(nino)).status_code == 405
    assert client.post(_url(nino, "XX"), {"XX-nivel": "3"}).status_code == 404


def test_el_formulario_usa_htmx_y_csrf(client, nino, educadora):
    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[nino.pk])).content.decode()
    url = _url(nino)
    assert f'action="{url}"' in html and f'hx-post="{url}"' in html
    assert 'hx-target="#nucleo-IA"' in html and 'hx-swap="outerHTML"' in html
    assert 'hx-disabled-elt="find button"' in html
    assert 'name="csrfmiddlewaretoken"' in html
    assert 'id="IA-nivel-1"' in html and 'name="IA-nivel"' in html
    assert 'value="1" checked' in html  # nivel actual marcado
