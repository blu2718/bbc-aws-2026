"""Rúbrica oficial de Integra (PLAN.md, Task 3, primer paso)."""
import pytest
from django.core.exceptions import ValidationError

from registro.curriculo import cargar_curriculo, leer_curriculo
from registro.models import DescriptorNivel, NivelEducativo, Rubrica, texto_nivel
from registro.rubrica_integra import cargar_rubrica_integra, leer_rubrica_integra

NOMBRES = ["Comenzando", "Explorando", "Desarrollando", "Afianzando", "Integrando", "Ampliando", "Consolidando",
           "Profundizando"]


def _bloque(sigla="IA", nivel_educativo=NivelEducativo.TRANSICION, cantidad=8, orientaciones=None):
    return {
        "nivel_educativo": nivel_educativo,
        "sigla": sigla,
        "niveles": [
            {
                "nivel": i,
                "nombre": NOMBRES[(i - 1) % len(NOMBRES)],
                "descripcion": f"Descripción {i}",
                "conducta": f"Conducta {i}",
                "ejemplos": [f"Ejemplo {i}a", f"Ejemplo {i}b"],
                "orientaciones": orientaciones,
            }
            for i in range(1, cantidad + 1)
        ],
    }


def _ia_transicion():
    return DescriptorNivel.objects.filter(nivel_educativo=NivelEducativo.TRANSICION, nucleo__sigla="IA")


# --- Con el JSON real del repo --------------------------------------------------------


@pytest.fixture
def cargada(db):
    cargar_curriculo(leer_curriculo())
    return cargar_rubrica_integra(leer_rubrica_integra())


def test_ia_de_transicion_queda_con_los_8_descriptores_de_integra(cargada):
    assert cargada == []  # no omitió ningún bloque
    descriptores = _ia_transicion()
    assert descriptores.count() == 8
    assert not descriptores.filter(provisorio=True).exists()
    nivel_3 = descriptores.get(nivel=3)
    assert nivel_3.nombre == "Desarrollando"
    assert nivel_3.conducta and nivel_3.descripcion
    assert len(nivel_3.ejemplos) == 2
    assert list(descriptores.values_list("nombre", flat=True)) == NOMBRES


def test_los_otros_nucleos_siguen_provisorios_con_nombre_nivel_n(cargada):
    otros = DescriptorNivel.objects.filter(nivel_educativo=NivelEducativo.TRANSICION).exclude(nucleo__sigla="IA")
    assert otros.count() == 7 * 8
    assert not otros.filter(provisorio=False).exists()
    assert otros.get(nucleo__sigla="LV", nivel=3).nombre == "Nivel 3"


def test_carga_los_3_niveles_educativos(cargada):
    for nivel_educativo in NivelEducativo.values:
        assert Rubrica.nivel_maximo(nivel_educativo) == 8
        assert DescriptorNivel.objects.filter(
            nivel_educativo=nivel_educativo, nucleo__sigla="IA", provisorio=False
        ).count() == 8


def test_las_orientaciones_vacias_dejan_los_pasos_vacios(cargada):
    assert not _ia_transicion().exclude(pasos_sugeridos="").exists()


def test_volver_a_cargar_el_curriculo_no_pisa_la_rubrica_de_integra(cargada):
    cargar_curriculo(leer_curriculo())
    assert _ia_transicion().get(nivel=3).nombre == "Desarrollando"
    assert not _ia_transicion().filter(provisorio=True).exists()


def test_nombres_por_nucleo_trae_solo_los_oficiales(cargada):
    nombres = DescriptorNivel.nombres_por_nucleo(NivelEducativo.TRANSICION)
    assert list(nombres) == ["IA"]
    assert nombres["IA"][3] == "Desarrollando"
    assert texto_nivel(3, nombres["IA"][3]) == "3 · Desarrollando"
    assert texto_nivel(3, nombres.get("LV", {}).get(3, "")) == "3"


# --- Con datos de prueba ----------------------------------------------------------------


def test_no_duplica_al_correr_dos_veces(rubrica, nucleos):
    datos = {"rubricas": [_bloque()]}
    cargar_rubrica_integra(datos)
    cargar_rubrica_integra(datos)
    assert _ia_transicion().count() == 8


def test_actualiza_un_texto_que_cambio_en_el_json(rubrica, nucleos):
    cargar_rubrica_integra({"rubricas": [_bloque()]})
    cambiado = _bloque()
    cambiado["niveles"][2]["descripcion"] = "Texto corregido por Integra"
    cargar_rubrica_integra({"rubricas": [cambiado]})
    assert _ia_transicion().get(nivel=3).descripcion == "Texto corregido por Integra"


def test_reemplaza_al_descriptor_provisorio(rubrica, nucleos):
    ia = nucleos[0]
    DescriptorNivel.objects.create(
        nivel_educativo=NivelEducativo.TRANSICION, nucleo=ia, nivel=3, nombre="Nivel 3", descripcion="provisorio"
    )
    cargar_rubrica_integra({"rubricas": [_bloque()]})
    d = _ia_transicion().get(nivel=3)
    assert (d.nombre, d.descripcion, d.provisorio) == ("Desarrollando", "Descripción 3", False)


def test_omite_una_sigla_inexistente_y_lo_informa(rubrica, nucleos):
    omitidos = cargar_rubrica_integra({"rubricas": [_bloque(sigla="XX"), _bloque()]})
    assert omitidos == [(NivelEducativo.TRANSICION, "XX")]
    assert _ia_transicion().count() == 8
    assert not DescriptorNivel.objects.filter(nucleo__sigla="XX").exists()


def test_falla_si_la_cantidad_de_niveles_no_calza_y_no_deja_nada_a_medias(rubrica, nucleos):
    # La rúbrica de la app tiene 8; el bloque de LV trae 9. El de IA, que viene antes, tampoco queda.
    with pytest.raises(ValidationError, match="trae 9 niveles y la de la app tiene 8"):
        cargar_rubrica_integra({"rubricas": [_bloque(), _bloque(sigla="LV", cantidad=9)]})
    assert not DescriptorNivel.objects.exists()


def test_falla_si_los_niveles_tienen_saltos(rubrica, nucleos):
    bloque = _bloque()
    bloque["niveles"][7]["nivel"] = 9
    with pytest.raises(ValidationError, match="sin saltos"):
        cargar_rubrica_integra({"rubricas": [bloque]})


def test_falla_con_un_nivel_educativo_desconocido(rubrica, nucleos):
    with pytest.raises(ValidationError, match="nivel educativo desconocido"):
        cargar_rubrica_integra({"rubricas": [_bloque(nivel_educativo="basica")]})


def test_crea_la_rubrica_que_falta_con_la_cantidad_del_bloque(nucleos):
    cargar_rubrica_integra({"rubricas": [_bloque(nivel_educativo=NivelEducativo.MEDIO, cantidad=9)]})
    assert Rubrica.nivel_maximo(NivelEducativo.MEDIO) == 9


def test_las_orientaciones_van_a_pasos_sugeridos(rubrica, nucleos):
    cargar_rubrica_integra({"rubricas": [_bloque(orientaciones=["Proponer X.", "Observar Y."])]})
    assert _ia_transicion().get(nivel=1).pasos_sugeridos == "Proponer X.\nObservar Y."


def test_orientaciones_en_null_no_pisan_los_pasos_del_panel(rubrica, nucleos):
    cargar_rubrica_integra({"rubricas": [_bloque()]})
    _ia_transicion().filter(nivel=1).update(pasos_sugeridos="Cargado en el panel")
    cargar_rubrica_integra({"rubricas": [_bloque(orientaciones=None)]})
    assert _ia_transicion().get(nivel=1).pasos_sugeridos == "Cargado en el panel"
