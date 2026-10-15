from datetime import date

from django.urls import reverse

from registro.models import Nino


def test_login_se_muestra(client, db):
    respuesta = client.get(reverse("login"))
    assert respuesta.status_code == 200


def test_inicio_pide_login(client, db):
    respuesta = client.get(reverse("inicio"))
    assert respuesta.status_code == 302
    assert reverse("login") in respuesta["Location"]


def test_con_un_solo_curso_va_directo_a_el(client, curso, educadora):
    client.force_login(educadora)
    respuesta = client.get(reverse("inicio"))
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("curso", args=[curso.pk])


def test_curso_muestra_ninos_y_niveles(client, curso, educadora, nucleos):
    Nino.objects.create(curso=curso, nombre="Pedro Salinas", fecha_ingreso=date(2026, 3, 2))
    client.force_login(educadora)
    respuesta = client.get(reverse("curso", args=[curso.pk]))
    assert respuesta.status_code == 200
    assert "Pedro Salinas" in respuesta.content.decode()


def test_otra_educadora_recibe_404(client, curso, otra_educadora):
    client.force_login(otra_educadora)
    assert client.get(reverse("curso", args=[curso.pk])).status_code == 404


def test_admin_solo_para_staff(client, educadora):
    client.force_login(educadora)
    respuesta = client.get("/admin/")
    assert respuesta.status_code == 302


def test_la_asistente_ve_su_curso(client, curso, asistente):
    curso.asistentes.add(asistente)
    client.force_login(asistente)
    assert client.get(reverse("curso", args=[curso.pk])).status_code == 200


def test_la_directora_ve_los_cursos_de_su_jardin(client, curso, directora, jardin):
    jardin.directora = directora
    jardin.save()
    client.force_login(directora)
    assert client.get(reverse("curso", args=[curso.pk])).status_code == 200


def test_una_directora_de_otro_jardin_recibe_404(client, curso, directora):
    from registro.models import Jardin

    Jardin.objects.create(nombre="Otro jardín", directora=directora)
    client.force_login(directora)
    assert client.get(reverse("curso", args=[curso.pk])).status_code == 404
