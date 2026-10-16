"""Informe para la familia: quién lo ve y que las citas no nombren a otros niños."""
from datetime import date

import pytest
from django.urls import reverse

from registro.informe import NINO_SIN_PRECISAR, OTRO_NINO, Anonimizador
from registro.models import Nino


@pytest.fixture
def companeros(curso, nucleos):
    crear = lambda nombre, alias=(): Nino.objects.create(  # noqa: E731
        curso=curso, nombre=nombre, alias=list(alias), fecha_ingreso=date(2026, 3, 2),
    )
    return {
        "sofia_r": crear("Sofía Rojas", ["Sofi R"]),
        "sofia_m": crear("Sofía Muñoz", ["Sofi M"]),
        "agustin": crear("Agustín Pérez", ["Agus"]),
        "maria": crear("María José Soto"),
    }


def test_las_citas_ocultan_apellidos_y_segundos_nombres_sueltos(companeros):
    anonimizador = Anonimizador(companeros["sofia_r"])
    texto = anonimizador.texto("Sofía jugó con Pérez y con José; después llegó Soto.")
    assert texto == f"Sofía jugó con {OTRO_NINO} y con {OTRO_NINO}; después llegó {OTRO_NINO}."


def test_un_nombre_compartido_se_refiere_al_nino_del_informe(companeros):
    """Hay dos Sofías: en el informe de Sofía Rojas, "Sofía" es ella; la otra, con apellido, no."""
    rojas = Anonimizador(companeros["sofia_r"])
    assert rojas.texto("Sofía y Sofía Muñoz bailaron.") == f"Sofía y {OTRO_NINO} bailaron."
    assert rojas.texto("Sofi M ayudó a Sofi R.") == f"{OTRO_NINO} ayudó a Sofía."
    # En el informe de otro niño, "Sofía" sola sigue sin precisarse.
    assert Anonimizador(companeros["agustin"]).texto("Sofía saludó a Agus.") == f"{NINO_SIN_PRECISAR} saludó a Agustín."


def test_un_alias_mal_cargado_no_rompe_el_informe(companeros):
    Nino.objects.filter(pk=companeros["maria"].pk).update(alias="Majo")
    assert Anonimizador(companeros["agustin"]).texto("Majo y Agustín.") == f"{OTRO_NINO} y Agustín."


def test_solo_la_educadora_del_curso_ve_el_informe(
    client, companeros, educadora, asistente_del_curso, directora_del_jardin, otra_educadora,
):
    url = reverse("informe_familia", args=[companeros["sofia_r"].pk])
    for usuaria in (asistente_del_curso, directora_del_jardin, otra_educadora):
        client.force_login(usuaria)
        assert client.get(url).status_code == 404
    client.force_login(educadora)
    respuesta = client.get(url)
    assert respuesta.status_code == 200
    assert "Sofía Rojas" in respuesta.content.decode()
