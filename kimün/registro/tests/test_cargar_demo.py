import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from registro.models import (
    Curso,
    DescriptorNivel,
    Manifestacion,
    MetaSemestre,
    NivelEducativo,
    NivelValidado,
    Nino,
    Nucleo,
    ObjetivoAprendizaje,
    Rubrica,
    Semestre,
)

MODELOS = [
    Rubrica, Nucleo, ObjetivoAprendizaje, Manifestacion, DescriptorNivel, Semestre, Curso, MetaSemestre, Nino,
    NivelValidado,
]


def _conteos():
    return {m.__name__: m.objects.count() for m in MODELOS} | {
        "User": get_user_model().objects.count(),
        "asistentes": Curso.asistentes.through.objects.count(),
    }


@pytest.fixture
def cargada(db, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "clave-demo-de-prueba")
    call_command("cargar_demo", verbosity=0)


def test_carga_curriculo_y_rubrica(cargada):
    rubrica = Rubrica.objects.get()
    assert (rubrica.nivel_educativo, rubrica.cantidad_niveles, rubrica.provisoria) == (NivelEducativo.TRANSICION, 8, True)
    assert Nucleo.objects.count() == 8
    assert ObjetivoAprendizaje.objects.count() == 85
    assert DescriptorNivel.objects.count() == 8 * 8
    assert not DescriptorNivel.objects.filter(provisorio=False).exists()
    assert Manifestacion.objects.filter(anio="NT1").exists()
    assert Manifestacion.objects.filter(anio="NT2").exists()


def test_cada_nucleo_trae_su_trayectoria(cargada):
    for nucleo in Nucleo.objects.all():
        assert nucleo.esperado_inicio_nt1.startswith("Al iniciar"), nucleo.sigla
        assert nucleo.continuidad_basica.startswith("Durante"), nucleo.sigla


def test_carga_curso_de_15_ninos_con_nivel_inicial(cargada):
    curso = Curso.objects.get()
    assert curso.ninos.count() == 15
    assert NivelValidado.objects.count() == 15 * 8
    assert list(curso.metas.values_list("semestre_permanencia", "nivel_esperado")) == [(1, 1), (2, 3), (3, 5), (4, 7)]
    assert Semestre.objects.count() == 3


def test_carga_educadora_y_asistente(cargada, client):
    curso = Curso.objects.get()
    assert curso.educadora.username == "educadora"
    assert list(curso.asistentes.values_list("username", flat=True)) == ["asistente"]
    assert client.login(username="educadora", password="clave-demo-de-prueba")
    assert client.login(username="asistente", password="clave-demo-de-prueba")


def test_incluye_casos_dificiles_de_nombres(cargada):
    assert Nino.objects.filter(nombre__startswith="Sofía").count() == 2
    assert "Nayara" in Nino.objects.get(nombre__startswith="Naiara").alias
    assert len(set(Nino.objects.values_list("fecha_ingreso", flat=True))) > 1


def test_correr_dos_veces_no_duplica(cargada):
    antes = _conteos()
    call_command("cargar_demo", verbosity=0)
    assert _conteos() == antes


def test_volver_a_cargar_respeta_la_rubrica_editada(cargada):
    """Si alguien pasa la rúbrica a 9 niveles en el panel, cargar_demo no la devuelve a 8."""
    Rubrica.objects.update(cantidad_niveles=9)
    d = DescriptorNivel.objects.filter(nivel=3).first()
    d.descripcion, d.provisorio, d.pasos_sugeridos = "Texto de Integra", False, "Observar X"
    d.save()

    call_command("cargar_demo", verbosity=0)

    assert Rubrica.objects.get().cantidad_niveles == 9
    d.refresh_from_db()
    assert (d.descripcion, d.provisorio, d.pasos_sugeridos) == ("Texto de Integra", False, "Observar X")


def test_sin_demo_password_genera_y_muestra_contrasenas(db, monkeypatch, capsys):
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    call_command("cargar_demo")
    salida = capsys.readouterr().out
    assert "Contraseña de educadora:" in salida
    assert "Contraseña de asistente:" in salida


@pytest.mark.parametrize(
    "modelo", ["rubrica", "curso", "nino", "objetivoaprendizaje", "manifestacion", "descriptornivel", "nivelvalidado", "jardin"]
)
def test_el_admin_muestra_lo_cargado(cargada, admin_client, modelo):
    """Demo de la Task 1: el panel muestra curso, niños, OA y rúbrica."""
    respuesta = admin_client.get(f"/admin/registro/{modelo}/")
    assert respuesta.status_code == 200


def test_el_admin_abre_las_fichas(cargada, admin_client):
    urls = [
        f"/admin/registro/nino/{Nino.objects.first().pk}/change/",
        f"/admin/registro/objetivoaprendizaje/{ObjetivoAprendizaje.objects.first().pk}/change/",
        f"/admin/registro/curso/{Curso.objects.get().pk}/change/",
        f"/admin/registro/rubrica/{Rubrica.objects.get().pk}/change/",
    ]
    for url in urls:
        assert admin_client.get(url).status_code == 200, url
