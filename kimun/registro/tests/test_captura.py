"""Formulario para registrar notas escritas y lista de las últimas capturas (PLAN.md, Task 5)."""
from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from registro.models import Captura, Curso, NivelEducativo, Observacion

HTMX = {"HX-Request": "true"}
POLLING = 'hx-trigger="every '
MENSAJE_ERROR = "No se pudo procesar la nota. Puedes reintentar."


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def otro_curso(jardin, otra_educadora):
    return Curso.objects.create(jardin=jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora)


def _url(nombre, obj):
    return reverse(nombre, args=[obj.pk])


def _captura(curso, autora, texto="Pedro contó hasta 10", **campos):
    return Captura.objects.create(curso=curso, autora=autora, tipo=Captura.Tipo.TEXTO, texto_original=texto, **campos)


# --- Registrar -----------------------------------------------------------------------------


@pytest.mark.parametrize("quien", ["educadora", "asistente_del_curso"])
def test_la_educadora_y_la_asistente_registran_en_su_curso(client, request, curso, quien):
    usuaria = request.getfixturevalue(quien)
    client.force_login(usuaria)
    assert client.get(_url("capturar", curso)).status_code == 200

    respuesta = client.post(_url("capturar", curso), {"texto": "Pedro y Emilio clasificaron hojas por color"}, follow=True)

    assert "Nota guardada." in respuesta.content.decode()
    captura = Captura.objects.get()
    assert (captura.curso, captura.autora, captura.tipo, captura.estado) == (curso, usuaria, Captura.Tipo.TEXTO, Captura.Estado.PENDIENTE)
    assert captura.texto_original == "Pedro y Emilio clasificaron hojas por color"


@pytest.mark.parametrize("quien", ["otra_educadora", "directora_del_jardin", "asistente"])
def test_no_se_puede_registrar_en_un_curso_ajeno(client, request, curso, quien):
    """La directora ve el curso pero no registra; la otra educadora y una asistente de otro curso, tampoco."""
    client.force_login(request.getfixturevalue(quien))
    assert client.get(_url("capturar", curso)).status_code == 404
    assert client.post(_url("capturar", curso), {"texto": "Nota en un curso ajeno"}).status_code == 404
    assert not Captura.objects.exists()


def test_registrar_pide_login(client, curso):
    respuesta = client.post(_url("capturar", curso), {"texto": "Nota"})
    assert respuesta.status_code == 302 and reverse("login") in respuesta["Location"]
    assert not Captura.objects.exists()


def test_una_nota_vacia_no_se_guarda(client, curso, educadora):
    client.force_login(educadora)
    respuesta = client.post(_url("capturar", curso), {"texto": "   "})
    assert respuesta.status_code == 200 and "Este campo es obligatorio." in respuesta.content.decode()
    assert not Captura.objects.exists()


def test_la_tabla_del_curso_enlaza_al_formulario_solo_a_quien_registra(client, curso, asistente_del_curso, directora_del_jardin):
    # El enlace lleva a "¿Qué quieres registrar?" (diseno-interfaz.jpg), que también acepta fotos y audios.
    enlace = f'href="{_url("registrar", curso)}"'
    client.force_login(asistente_del_curso)
    assert enlace in client.get(_url("curso", curso)).content.decode()
    client.force_login(directora_del_jardin)
    assert enlace not in client.get(_url("curso", curso)).content.decode()


# --- Lista de las últimas capturas ----------------------------------------------------------


def test_la_lista_muestra_solo_las_capturas_propias_del_curso(client, curso, otro_curso, educadora, asistente_del_curso):
    _captura(curso, educadora, "Nota propia del curso")
    _captura(curso, asistente_del_curso, "Nota de la asistente")
    otro_curso.asistentes.add(educadora)  # también registra en el otro curso
    _captura(otro_curso, educadora, "Nota propia de otro curso")
    client.force_login(educadora)

    for url in (_url("capturar", curso), _url("capturas_recientes", curso)):
        html = client.get(url).content.decode()
        assert "Nota propia del curso" in html, url
        assert "Nota de la asistente" not in html, url
        assert "Nota propia de otro curso" not in html, url


def test_la_lista_muestra_estado_observaciones_y_error(client, curso, educadora):
    procesada = _captura(curso, educadora, "Nota procesada", estado=Captura.Estado.PROCESADA)
    for cita in ("Uno", "Dos"):
        Observacion.objects.create(captura=procesada, fecha=procesada.creada.date(), cita=cita)
    _captura(curso, educadora, "Nota con error", estado=Captura.Estado.ERROR, error="Bedrock no respondió")
    client.force_login(educadora)

    html = client.get(_url("capturas_recientes", curso)).content.decode()

    assert "<strong>Procesada</strong>" in html and "2 observaciones" in html
    assert "<strong>Error</strong>" in html and MENSAJE_ERROR in html
    assert html.count(">Reintentar</button>") == 1


def test_el_detalle_del_error_no_se_muestra_a_quien_registro(client, admin_client, curso, educadora):
    """El error crudo de AWS puede traer el ARN del rol o la cuenta: solo va al admin (y al log)."""
    detalle = "Bedrock rechazó la llamada: AccessDeniedException arn:aws:sts::123456789012:assumed-role/kimun"
    captura = _captura(curso, educadora, "Nota con error", estado=Captura.Estado.ERROR, error=detalle)
    client.force_login(educadora)

    for url in (_url("capturar", curso), _url("capturas_recientes", curso)):
        html = client.get(url).content.decode()
        assert MENSAJE_ERROR in html, url
        assert "123456789012" not in html and "AccessDenied" not in html, url

    admin = admin_client.get(reverse("admin:registro_captura_change", args=[captura.pk])).content.decode()
    assert "arn:aws:sts::123456789012:assumed-role/kimun" in admin


def test_el_parcial_se_refresca_solo_mientras_hay_capturas_en_curso(client, curso, educadora):
    captura = _captura(curso, educadora, estado=Captura.Estado.PENDIENTE)
    client.force_login(educadora)

    for estado in (Captura.Estado.PENDIENTE, Captura.Estado.PROCESANDO):
        Captura.objects.filter(pk=captura.pk).update(estado=estado)
        html = client.get(_url("capturas_recientes", curso), headers=HTMX).content.decode()
        assert POLLING in html and f'hx-get="{_url("capturas_recientes", curso)}"' in html, estado
        assert POLLING in client.get(_url("capturar", curso)).content.decode(), estado

    for estado in (Captura.Estado.PROCESADA, Captura.Estado.ERROR):
        Captura.objects.filter(pk=captura.pk).update(estado=estado)
        assert POLLING not in client.get(_url("capturas_recientes", curso), headers=HTMX).content.decode(), estado


def test_no_hay_polling_si_solo_quedan_capturas_atascadas(client, curso, educadora):
    """Una captura con más de 5 minutos en procesando no va a cambiar sola: no se sigue consultando."""
    atascada = _captura(curso, educadora, "Nota atascada", estado=Captura.Estado.PROCESANDO)
    Captura.objects.filter(pk=atascada.pk).update(actualizada=timezone.now() - timedelta(minutes=6))
    client.force_login(educadora)

    html = client.get(_url("capturas_recientes", curso), headers=HTMX).content.decode()
    assert "Nota atascada" in html and POLLING not in html
    assert POLLING not in client.get(_url("capturar", curso)).content.decode()

    _captura(curso, educadora, "Nota nueva", estado=Captura.Estado.PENDIENTE)
    assert POLLING in client.get(_url("capturas_recientes", curso), headers=HTMX).content.decode()


def test_sin_capturas_no_hay_polling(client, curso, educadora):
    client.force_login(educadora)
    assert POLLING not in client.get(_url("capturar", curso)).content.decode()


def test_el_parcial_es_solo_para_quien_registra_en_el_curso(client, curso, otra_educadora):
    client.force_login(otra_educadora)
    assert client.get(_url("capturas_recientes", curso)).status_code == 404


# --- Reintentar ----------------------------------------------------------------------------


def test_reintentar_una_captura_con_error_la_vuelve_a_pendiente(client, curso, educadora):
    captura = _captura(curso, educadora, estado=Captura.Estado.ERROR, error="Bedrock no respondió", intentos=1)
    client.force_login(educadora)

    html = client.post(_url("captura_reintentar", captura), headers=HTMX).content.decode()

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE and captura.intentos == 1
    assert "<strong>Pendiente</strong>" in html and POLLING in html


def test_reintentar_sin_javascript_redirige_al_formulario(client, curso, educadora):
    captura = _captura(curso, educadora, estado=Captura.Estado.ERROR)
    client.force_login(educadora)
    respuesta = client.post(_url("captura_reintentar", captura), follow=True)
    assert respuesta.redirect_chain[-1][0] == _url("capturar", curso)
    assert "volvió a la cola" in respuesta.content.decode()
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE


@pytest.mark.parametrize("estado", [Captura.Estado.PENDIENTE, Captura.Estado.PROCESANDO, Captura.Estado.PROCESADA])
def test_reintentar_no_cambia_capturas_que_no_estan_en_error(client, curso, educadora, estado):
    captura = _captura(curso, educadora, estado=estado)
    antes = captura.actualizada
    client.force_login(educadora)

    html = client.post(_url("captura_reintentar", captura), headers=HTMX).content.decode()

    assert "Solo se pueden reintentar las notas que quedaron con error." in html
    captura.refresh_from_db()
    assert (captura.estado, captura.actualizada) == (estado, antes)


@pytest.mark.parametrize("quien", ["asistente_del_curso", "otra_educadora", "directora_del_jardin"])
def test_no_se_puede_reintentar_una_captura_ajena(client, request, curso, educadora, quien):
    """Solo la autora reintenta, aunque otra usuaria registre en el mismo curso."""
    captura = _captura(curso, educadora, estado=Captura.Estado.ERROR)
    client.force_login(request.getfixturevalue(quien))

    assert client.post(_url("captura_reintentar", captura), headers=HTMX).status_code == 404
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR


def test_reintentar_pide_post(client, curso, educadora):
    captura = _captura(curso, educadora, estado=Captura.Estado.ERROR)
    client.force_login(educadora)
    assert client.get(_url("captura_reintentar", captura)).status_code == 405
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR


def test_reintentar_exige_csrf(curso, educadora):
    captura = _captura(curso, educadora, estado=Captura.Estado.ERROR)
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(educadora)
    assert cliente.post(_url("captura_reintentar", captura)).status_code == 403
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR
