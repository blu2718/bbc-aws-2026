import pytest
from django.contrib.auth import get_user_model

from registro.models import Curso, Jardin, NivelEducativo, Nucleo, Rubrica


def _usuario(nombre):
    return get_user_model().objects.create_user(nombre, password="clave-de-prueba-123")


@pytest.fixture
def rubrica(db):
    return Rubrica.objects.create(nivel_educativo=NivelEducativo.TRANSICION, cantidad_niveles=8)


@pytest.fixture
def nucleos(db):
    datos = [("IA", "Identidad y Autonomía"), ("LV", "Lenguaje Verbal"), ("PM", "Pensamiento Matemático")]
    return [Nucleo.objects.create(sigla=s, nombre=n, orden=i) for i, (s, n) in enumerate(datos)]


@pytest.fixture
def educadora(db):
    return _usuario("ana")


@pytest.fixture
def otra_educadora(db):
    return _usuario("berta")


@pytest.fixture
def asistente(db):
    return _usuario("carla")


@pytest.fixture
def directora(db):
    return _usuario("dora")


@pytest.fixture
def jardin(db):
    return Jardin.objects.create(nombre="Jardín de prueba")


@pytest.fixture
def curso(educadora, jardin, rubrica):
    return Curso.objects.create(
        jardin=jardin, nombre="Transición A", nivel_educativo=NivelEducativo.TRANSICION, educadora=educadora
    )
