"""Varias salas por jardín: la directora las crea, les asigna el equipo y las monitorea; la educadora
y las asistentes ven solo las suyas; la lista de niños la mantienen la directora y la educadora."""
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from registro.models import (
    AvisoProteccion, Captura, Curso, Jardin, MetaSemestre, NivelEducativo, NivelValidado, Nino, Observacion,
)
from registro.permisos import cursos_de
from registro.salas import equipo_disponible, panel_del_jardin


def _usuario(nombre, **extra):
    return get_user_model().objects.create_user(nombre, password="clave-de-prueba-123", **extra)


@pytest.fixture
def equipo(db):
    return {n: _usuario(n, first_name=n.capitalize()) for n in ("elena", "fabiola", "gloria", "nueva")}


@pytest.fixture
def directora_ajena(db):
    """Dirige otro jardín. (`directora_de_otro_jardin` de conftest es la misma usuaria que `directora_del_jardin`.)"""
    usuaria = _usuario("irene")
    Jardin.objects.create(nombre="Jardín ajeno", directora=usuaria)
    return usuaria


@pytest.fixture
def dos_salas(curso, directora_del_jardin, asistente_del_curso, equipo, nucleos):
    """Transición A (de `curso`, educadora ana y asistente carla) y Transición B (educadora elena, asistente fabiola)."""
    b = Curso.objects.create(jardin=curso.jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION,
                             educadora=equipo["elena"])
    b.asistentes.add(equipo["fabiola"])
    Nino.objects.create(curso=curso, nombre="Pedro Salinas", fecha_ingreso=date(2026, 3, 2))
    Nino.objects.create(curso=b, nombre="Rosa Vera", fecha_ingreso=date(2026, 3, 2))
    return curso, b


# --- Quién ve qué ---------------------------------------------------------------------


def test_cada_una_ve_sus_salas_y_la_directora_todas(dos_salas, educadora, asistente_del_curso, directora_del_jardin, equipo):
    a, b = dos_salas
    assert set(cursos_de(directora_del_jardin)) == {a, b}
    assert set(cursos_de(educadora)) == {a}
    assert set(cursos_de(asistente_del_curso)) == {a}
    assert set(cursos_de(equipo["elena"])) == {b}
    assert set(cursos_de(equipo["fabiola"])) == {b}


def test_una_asistente_en_dos_salas_cambia_de_sala_desde_el_menu(client, dos_salas, asistente_del_curso):
    a, b = dos_salas
    b.asistentes.add(asistente_del_curso)
    client.force_login(asistente_del_curso)
    html = client.get(reverse("curso", args=[a.pk])).content.decode()
    assert "Cambiar de sala" in html and reverse("curso", args=[b.pk]) in html
    assert client.get(reverse("curso", args=[b.pk])).status_code == 200


def test_quien_esta_en_una_sola_sala_no_ve_las_otras(client, dos_salas, educadora):
    a, b = dos_salas
    client.force_login(educadora)
    html = client.get(reverse("curso", args=[a.pk])).content.decode()
    assert "Cambiar de sala" not in html and "Transición B" not in html
    assert client.get(reverse("curso", args=[b.pk])).status_code == 404


# --- Panel de la directora --------------------------------------------------------------


def test_el_panel_muestra_cada_sala_con_su_equipo_y_lo_pendiente(client, dos_salas, directora_del_jardin, educadora):
    a, b = dos_salas
    captura = Captura.objects.create(curso=a, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="x")
    Observacion.objects.create(captura=captura, nino=a.ninos.get(), fecha=timezone.localdate(), cita="ordenó",
                               estado=Observacion.Estado.PENDIENTE)
    resguardo = Captura.objects.create(curso=b, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="nota sensible",
                                       estado=Captura.Estado.EN_RESGUARDO)
    AvisoProteccion.objects.create(captura=resguardo)
    panel = panel_del_jardin(a.jardin)
    estados = {s.curso.nombre: s for s in panel.salas}
    assert estados["Transición A"].por_revisar == 1 and estados["Transición A"].asistentes == ["carla"]
    assert estados["Transición B"].avisos == 1 and estados["Transición B"].educadora == "Elena"
    assert panel.total_ninos == 2

    client.force_login(directora_del_jardin)
    html = client.get(reverse("jardin", args=[a.jardin_id])).content.decode()
    assert "Salas del jardín (2)" in html
    assert "1 observación por revisar" in html and "1 aviso de protección por atender" in html
    assert "nota sensible" not in html  # el panel cuenta los avisos; el texto queda solo en el aviso


def test_solo_la_directora_ve_el_panel(client, dos_salas, educadora, directora_ajena):
    a, _ = dos_salas
    for usuaria in (educadora, directora_ajena):
        client.force_login(usuaria)
        assert client.get(reverse("jardin", args=[a.jardin_id])).status_code == 404


def test_un_jardin_sin_salas_invita_a_crear_la_primera(client, directora):
    jardin = Jardin.objects.create(nombre="Nuevo", directora=directora)
    client.force_login(directora)
    html = client.get(reverse("jardin", args=[jardin.pk])).content.decode()
    assert "todavía no tiene salas" in html and reverse("sala_nueva", args=[jardin.pk]) in html


# --- Crear y editar salas -----------------------------------------------------------------


def test_la_directora_crea_una_sala_con_su_equipo_y_metas_por_defecto(client, dos_salas, directora_del_jardin, equipo):
    a, _ = dos_salas
    client.force_login(directora_del_jardin)
    respuesta = client.post(reverse("sala_nueva", args=[a.jardin_id]), {
        "nombre": "  Medio   Menor A ", "nivel_educativo": NivelEducativo.MEDIO,
        "educadora": equipo["gloria"].pk, "asistentes": [equipo["nueva"].pk],
    })
    sala = Curso.objects.get(nombre="Medio Menor A")
    assert respuesta.status_code == 302 and respuesta.url == reverse("ninos_sala", args=[sala.pk])
    assert sala.jardin == a.jardin and sala.educadora == equipo["gloria"]
    assert list(sala.asistentes.all()) == [equipo["nueva"]]
    assert dict(sala.metas.values_list("semestre_permanencia", "nivel_esperado")) == {1: 1, 2: 3, 3: 5, 4: 7}
    # Desde ya, la nueva educadora y su asistente ven la sala.
    assert set(cursos_de(equipo["gloria"])) == {sala}
    assert set(cursos_de(equipo["nueva"])) == {sala}


@pytest.mark.parametrize("cambios, error", [
    ({"nombre": "transición b"}, "Ya hay una sala con ese nombre"),
    ({"asistentes": "educadora"}, "ya es la educadora de la sala"),
    ({"educadora": ""}, "obligatorio"),
])
def test_la_sala_se_valida(client, dos_salas, directora_del_jardin, equipo, cambios, error):
    a, _ = dos_salas
    datos = {"nombre": "Transición C", "nivel_educativo": NivelEducativo.TRANSICION, "educadora": equipo["gloria"].pk}
    datos.update(cambios)
    if datos.get("asistentes") == "educadora":
        datos["asistentes"] = [equipo["gloria"].pk]
    client.force_login(directora_del_jardin)
    respuesta = client.post(reverse("sala_nueva", args=[a.jardin_id]), datos)
    assert respuesta.status_code == 400 and error in respuesta.content.decode()
    assert not Curso.objects.filter(nombre="Transición C").exists()


def test_el_equipo_disponible_no_muestra_personal_de_otros_jardines(dos_salas, equipo, otra_educadora, directora_del_jardin):
    a, _ = dos_salas
    otro = Jardin.objects.create(nombre="Otro jardín")
    Curso.objects.create(jardin=otro, nombre="Sala ajena", nivel_educativo=NivelEducativo.MEDIO, educadora=otra_educadora)
    _usuario("admin", is_superuser=True)
    disponibles = set(equipo_disponible(a.jardin).values_list("username", flat=True))
    assert {"ana", "carla", "elena", "fabiola", "gloria", "nueva", "dora"} <= disponibles
    assert "berta" not in disponibles and "admin" not in disponibles


def test_no_se_puede_elegir_a_alguien_de_otro_jardin(client, dos_salas, directora_del_jardin, otra_educadora):
    a, _ = dos_salas
    otro = Jardin.objects.create(nombre="Otro jardín")
    Curso.objects.create(jardin=otro, nombre="Sala ajena", nivel_educativo=NivelEducativo.MEDIO, educadora=otra_educadora)
    client.force_login(directora_del_jardin)
    respuesta = client.post(reverse("sala_nueva", args=[a.jardin_id]), {
        "nombre": "Transición C", "nivel_educativo": NivelEducativo.TRANSICION, "educadora": otra_educadora.pk,
    })
    assert respuesta.status_code == 400


def test_cambiar_la_educadora_le_pasa_la_sala(client, dos_salas, directora_del_jardin, educadora, equipo):
    a, _ = dos_salas
    client.force_login(directora_del_jardin)
    respuesta = client.post(reverse("sala_editar", args=[a.pk]), {
        "nombre": a.nombre, "educadora": equipo["gloria"].pk, "asistentes": [],
    }, follow=True)
    assert "Ahora Gloria revisa sus observaciones" in respuesta.content.decode()
    a.refresh_from_db()
    assert a.educadora == equipo["gloria"] and not a.asistentes.exists()
    assert a.nivel_educativo == NivelEducativo.TRANSICION  # con niños, el nivel educativo no cambia
    assert not cursos_de(educadora).exists()


def test_una_sala_con_ninos_no_cambia_de_nivel_educativo(client, dos_salas, directora_del_jardin, educadora):
    a, _ = dos_salas
    client.force_login(directora_del_jardin)
    client.post(reverse("sala_editar", args=[a.pk]), {
        "nombre": a.nombre, "nivel_educativo": NivelEducativo.SALA_CUNA, "educadora": educadora.pk,
    })
    a.refresh_from_db()
    assert a.nivel_educativo == NivelEducativo.TRANSICION


@pytest.mark.parametrize("quien", ["educadora", "asistente_del_curso", "directora_ajena"])
def test_solo_la_directora_crea_y_edita_salas(client, request, dos_salas, quien):
    a, _ = dos_salas
    client.force_login(request.getfixturevalue(quien))
    assert client.get(reverse("sala_nueva", args=[a.jardin_id])).status_code == 404
    assert client.get(reverse("sala_editar", args=[a.pk])).status_code == 404


# --- Niños de la sala ---------------------------------------------------------------------


def test_la_educadora_agrega_un_nino_que_parte_en_nivel_1(client, dos_salas, educadora, nucleos):
    a, _ = dos_salas
    client.force_login(educadora)
    respuesta = client.post(reverse("nino_nuevo", args=[a.pk]), {
        "nombre": " Naiara  Fuentes ", "alias": "Nayara, naia, Nayara", "fecha_ingreso": "2026-08-03",
        "fecha_nacimiento": "2020-07-01",
    })
    assert respuesta.status_code == 302
    nino = Nino.objects.get(nombre="Naiara Fuentes")
    assert nino.curso == a and nino.alias == ["Nayara", "naia"]
    assert set(NivelValidado.objects.filter(nino=nino).values_list("nivel", flat=True)) == {1}
    assert NivelValidado.objects.filter(nino=nino).count() == len(nucleos)


@pytest.mark.parametrize("datos, error", [
    ({"nombre": "pedro salinas"}, "Ya hay un niño o niña con ese nombre"),
    ({"fecha_ingreso": "2099-01-01"}, "no puede ser futura"),
    ({"fecha_nacimiento": "2026-05-01"}, "posterior al ingreso"),
    ({"alias": "x" * 41}, "hasta 40 caracteres"),
])
def test_los_datos_del_nino_se_validan(client, dos_salas, educadora, datos, error):
    a, _ = dos_salas
    client.force_login(educadora)
    respuesta = client.post(reverse("nino_nuevo", args=[a.pk]), {"nombre": "Nuevo Niño", "fecha_ingreso": "2026-03-02", **datos})
    assert respuesta.status_code == 400 and error in respuesta.content.decode()


def test_la_directora_edita_los_datos_sin_cambiar_la_fecha_de_ingreso(client, dos_salas, directora_del_jardin):
    _, b = dos_salas
    rosa = b.ninos.get()
    client.force_login(directora_del_jardin)
    client.post(reverse("nino_editar", args=[rosa.pk]), {
        "nombre": "Rosa Vera Soto", "alias": "Rosi", "fecha_ingreso": "2020-01-01", "fecha_nacimiento": "",
    })
    rosa.refresh_from_db()
    assert (rosa.nombre, rosa.alias, rosa.fecha_ingreso) == ("Rosa Vera Soto", ["Rosi"], date(2026, 3, 2))


@pytest.mark.parametrize("quien", ["asistente_del_curso", "directora_ajena", "otra_educadora"])
def test_las_demas_no_editan_la_lista(client, request, dos_salas, quien):
    a, _ = dos_salas
    pedro = a.ninos.get()
    client.force_login(request.getfixturevalue(quien))
    assert client.get(reverse("ninos_sala", args=[a.pk])).status_code == 404
    assert client.post(reverse("nino_nuevo", args=[a.pk]), {"nombre": "X", "fecha_ingreso": "2026-03-02"}).status_code == 404
    assert client.post(reverse("nino_editar", args=[pedro.pk]), {"nombre": "X"}).status_code == 404
    assert Nino.objects.filter(curso=a).count() == 1


def test_la_educadora_de_otra_sala_del_jardin_no_edita_esta(client, dos_salas, equipo):
    a, _ = dos_salas
    client.force_login(equipo["elena"])
    assert client.get(reverse("ninos_sala", args=[a.pk])).status_code == 404


def test_una_sala_nueva_sin_ninos_funciona_en_todas_sus_vistas(client, dos_salas, directora_del_jardin, equipo):
    a, _ = dos_salas
    client.force_login(directora_del_jardin)
    client.post(reverse("sala_nueva", args=[a.jardin_id]), {
        "nombre": "Sala Cuna Mayor", "nivel_educativo": NivelEducativo.SALA_CUNA, "educadora": equipo["gloria"].pk,
    })
    sala = Curso.objects.get(nombre="Sala Cuna Mayor")
    assert MetaSemestre.objects.filter(curso=sala).count() == 4
    for url in (reverse("jardin", args=[a.jardin_id]), reverse("curso", args=[sala.pk]), reverse("ninos_sala", args=[sala.pk])):
        assert client.get(url).status_code == 200
    client.force_login(equipo["gloria"])
    assert client.get(reverse("registrar", args=[sala.pk])).status_code == 200
    assert client.get(reverse("revision", args=[sala.pk])).status_code == 200
