from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from registro.models import (
    Captura,
    Curso,
    DescriptorNivel,
    Jardin,
    NivelEducativo,
    Nino,
    Nucleo,
    Observacion,
    Rubrica,
)


@pytest.fixture(scope="session", autouse=True)
def _passwords_de_prueba(django_test_environment):
    """Las contraseñas ficticias no necesitan el costo del hasher de producción."""
    with override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]):
        yield


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


# --- Fixtures de la ficha (Task 3) ------------------------------------------------

NOMBRES_INTEGRA = [
    "Comenzando", "Explorando", "Desarrollando", "Afianzando",
    "Integrando", "Ampliando", "Consolidando", "Profundizando",
]


@pytest.fixture
def nino(curso, nucleos):
    """Se crea después de los núcleos, así que parte en nivel 1 en IA, LV y PM."""
    return Nino.objects.create(curso=curso, nombre="Pedro Salinas", fecha_ingreso=date(2026, 3, 2))


@pytest.fixture
def descriptores(nucleos):
    """IA con rúbrica oficial de 8 niveles; LV provisoria; PM sin descriptores."""
    ia, lv, _pm = nucleos
    for nivel, nombre in enumerate(NOMBRES_INTEGRA, start=1):
        DescriptorNivel.objects.create(
            nivel_educativo=NivelEducativo.TRANSICION, nucleo=ia, nivel=nivel, nombre=nombre,
            descripcion=f"Descripción IA {nivel}", conducta=f"Conducta IA {nivel}",
            ejemplos=[f"Ejemplo IA {nivel} a", f"Ejemplo IA {nivel} b"], provisorio=False,
        )
        DescriptorNivel.objects.create(
            nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, nivel=nivel, nombre=f"Nivel {nivel}",
            descripcion=f"Descripción LV {nivel}",
        )


@pytest.fixture
def asistente_del_curso(curso, asistente):
    curso.asistentes.add(asistente)
    return asistente


@pytest.fixture
def directora_del_jardin(jardin, directora):
    jardin.directora = directora
    jardin.save()
    return directora


@pytest.fixture
def directora_de_otro_jardin(directora):
    """Dirige otro jardín: no ve ni registra en los cursos del jardín de prueba."""
    Jardin.objects.create(nombre="Otro jardín", directora=directora)
    return directora


@pytest.fixture
def observar_en(curso, educadora):
    """Crea observaciones del niño etiquetadas con núcleos (y OA, si se pasan)."""
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="x")

    def crear(nino, fecha, nucleos, cita="Cita", estado=Observacion.Estado.ACEPTADA, grupal=False, oas=()):
        obs = Observacion.objects.create(
            captura=captura, nino=nino, fecha=fecha, cita=cita, estado=estado, grupal=grupal
        )
        obs.nucleos.set(nucleos)
        obs.oas.set(oas)
        return obs

    return crear
