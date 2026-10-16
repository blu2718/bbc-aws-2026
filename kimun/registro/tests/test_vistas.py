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


def test_con_un_solo_curso_va_directo_a_registrar(client, curso, educadora, asistente):
    """La pestaña de inicio es "¿Qué quieres registrar?" (diseno-interfaz.jpg, pantalla I)."""
    curso.asistentes.add(asistente)
    for usuaria in (educadora, asistente):
        client.force_login(usuaria)
        respuesta = client.get(reverse("inicio"))
        assert respuesta.status_code == 302
        assert respuesta["Location"] == reverse("registrar", args=[curso.pk])


def test_la_directora_con_un_solo_curso_va_al_resumen_de_su_jardin(client, curso, directora, jardin):
    """Aunque registra en ese curso (Task 12), la directora parte en el resumen de su jardín."""
    jardin.directora = directora
    jardin.save()
    client.force_login(directora)
    respuesta = client.get(reverse("inicio"))
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("jardin", args=[jardin.pk])


def test_el_html_va_comprimido_si_el_navegador_lo_acepta(client, curso, educadora, nucleos):
    """CloudFront no comprime con CachingDisabled: la ficha y la tabla viajan comprimidas desde Django."""
    client.force_login(educadora)
    url = reverse("curso", args=[curso.pk])
    comprimida = client.get(url, HTTP_ACCEPT_ENCODING="gzip, br")
    assert comprimida.status_code == 200
    assert comprimida["Content-Encoding"] == "gzip" and "Accept-Encoding" in comprimida["Vary"]
    assert "Content-Encoding" not in client.get(url)  # sin Accept-Encoding, va tal cual


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


# --- Vista del curso con alertas y quincena (PLAN.md, Task 2) ---------------------------

from datetime import timedelta  # noqa: E402

import pytest  # noqa: E402
from django.utils import timezone  # noqa: E402

from registro.cobertura import quincena_de  # noqa: E402
from registro.models import (  # noqa: E402
    Captura,
    Curso,
    MetaSemestre,
    NivelEducativo,
    NivelValidado,
    Nucleo,
    Observacion,
    Rubrica,
    Semestre,
)


@pytest.fixture
def semestres_alrededor_de_hoy(db):
    """Un semestre que empezó hace un año y sigue abierto: todos están en su semestre 1."""
    hoy = timezone.localdate()
    Semestre.objects.create(nombre="actual", inicio=hoy - timedelta(days=365), fin=hoy + timedelta(days=60))


@pytest.fixture
def curso_con_ninos(curso, nucleos, semestres_alrededor_de_hoy):
    MetaSemestre.objects.create(curso=curso, semestre_permanencia=1, nivel_esperado=5)
    hoy = timezone.localdate()
    ninos = [
        Nino.objects.create(curso=curso, nombre=n, fecha_ingreso=hoy - timedelta(days=300))
        for n in ["Pedro Salinas", "Emilio Vargas", "Rubí Contreras", "Matías Lagos"]
    ]
    for nino in ninos:
        for nucleo in nucleos:
            nivel = 2 if (nino.nombre == "Matías Lagos" and nucleo.sigla == "LV") else 5
            NivelValidado.objects.create(nino=nino, nucleo=nucleo, nivel=nivel, fecha=hoy - timedelta(days=10))
    return ninos


def _observar(curso, autora, nino, fecha, nucleos):
    captura = Captura.objects.create(curso=curso, autora=autora, tipo=Captura.Tipo.TEXTO, texto_original="x")
    obs = Observacion.objects.create(
        captura=captura, nino=nino, fecha=fecha, cita="x", estado=Observacion.Estado.ACEPTADA
    )
    obs.nucleos.set(nucleos)
    return obs


def _html(client, curso, **params):
    respuesta = client.get(reverse("curso", args=[curso.pk]), params)
    assert respuesta.status_code == 200
    return respuesta.content.decode()


def test_la_tabla_muestra_la_alerta_como_texto_de_sugerencia(client, curso, educadora, curso_con_ninos):
    client.force_login(educadora)
    html = _html(client, curso)
    assert "Revisar: 3 niveles bajo la mediana del curso" in html
    assert "Revisar: 3 niveles bajo lo esperado" in html
    assert 'class="senal senal-alerta"' in html
    assert "Semestre 1 · se espera 5" in html
    # Nadie tiene observaciones todavía.
    assert "Sin datos" in html


def test_la_tabla_muestra_la_distribucion_con_las_columnas_de_la_rubrica(client, curso, educadora, curso_con_ninos):
    client.force_login(educadora)
    html = _html(client, curso)
    assert "Nivel 8</th>" in html and "Nivel 9</th>" not in html

    Rubrica.objects.filter(nivel_educativo=NivelEducativo.TRANSICION).update(cantidad_niveles=9)
    assert "Nivel 9</th>" in _html(client, curso)


def test_el_resumen_de_la_quincena_destaca_los_nucleos_sin_observaciones(client, curso, educadora, curso_con_ninos, nucleos):
    ia, lv, pm = nucleos
    hoy = timezone.localdate()
    _observar(curso, educadora, curso_con_ninos[0], hoy, [lv])
    client.force_login(educadora)

    html = _html(client, curso)

    assert "2 de 3 núcleos sin observaciones en esta quincena" in html
    assert html.count('class="sin-observaciones"') == 2
    assert "(actual)" in html


def test_se_puede_volver_a_una_quincena_anterior(client, curso, educadora, curso_con_ninos, nucleos):
    ia, lv, pm = nucleos
    anterior = quincena_de(timezone.localdate()).anterior()
    _observar(curso, educadora, curso_con_ninos[0], anterior.inicio, [ia, lv, pm])
    client.force_login(educadora)

    html = _html(client, curso, quincena=anterior.inicio.isoformat())

    assert "Todos los núcleos tienen observaciones en esta quincena." in html
    assert "(actual)" not in html
    assert "Volver a la quincena actual" in html
    # En la quincena actual esa observación no cuenta.
    assert "3 de 3 núcleos sin observaciones" in _html(client, curso)


@pytest.mark.parametrize("valor", ["no-es-fecha", "2999-01-01", ""])
def test_una_quincena_invalida_o_futura_muestra_la_actual(client, curso, educadora, curso_con_ninos, valor):
    client.force_login(educadora)
    assert "(actual)" in _html(client, curso, quincena=valor)


def test_la_vista_funciona_con_10_nucleos_y_9_niveles(client, db, educadora, jardin, semestres_alrededor_de_hoy):
    Rubrica.objects.create(nivel_educativo=NivelEducativo.MEDIO, cantidad_niveles=9)
    for i in range(10):
        Nucleo.objects.create(sigla=f"K{i}", nombre=f"Núcleo {i}", orden=i)
    curso = Curso.objects.create(jardin=jardin, nombre="Medio A", nivel_educativo=NivelEducativo.MEDIO, educadora=educadora)
    Nino.objects.create(curso=curso, nombre="Pedro", fecha_ingreso=timezone.localdate())
    client.force_login(educadora)

    html = _html(client, curso)

    assert "K9</abbr>" in html
    assert "Nivel 9</th>" in html
    assert "10 de 10 núcleos sin observaciones" in html
