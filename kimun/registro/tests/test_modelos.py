from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from registro.models import (
    Captura,
    DescriptorNivel,
    MetaSemestre,
    NivelEducativo,
    NivelValidado,
    Nino,
    ObjetivoAprendizaje,
    Observacion,
    PropuestaNivel,
    Rubrica,
    Semestre,
)


def _falla_integridad(fn):
    with pytest.raises(IntegrityError), transaction.atomic():
        fn()


def _falla_validacion(fn):
    with pytest.raises(ValidationError), transaction.atomic():
        fn()


@pytest.fixture
def nino(curso, nucleos):
    return Nino.objects.create(curso=curso, nombre="Pedro", fecha_ingreso=date(2026, 3, 2))


def test_al_crear_un_nino_queda_en_nivel_1_en_todos_los_nucleos(nino, nucleos):
    niveles = NivelValidado.objects.filter(nino=nino)
    assert niveles.count() == len(nucleos)
    assert set(niveles.values_list("nivel", flat=True)) == {1}
    assert set(niveles.values_list("fecha", flat=True)) == {date(2026, 3, 2)}


def test_guardar_de_nuevo_un_nino_no_duplica_niveles(nino, nucleos):
    nino.alias = ["Pedrito"]
    nino.save()
    assert NivelValidado.objects.filter(nino=nino).count() == len(nucleos)


def test_nivel_actual_es_el_mas_reciente(nino, nucleos, educadora):
    lv = nucleos[1]
    NivelValidado.objects.create(nino=nino, nucleo=lv, nivel=3, fecha=date(2026, 6, 1), validado_por=educadora)
    NivelValidado.objects.create(nino=nino, nucleo=lv, nivel=2, fecha=date(2026, 5, 1), validado_por=educadora)
    assert nino.nivel_actual(lv).nivel == 3
    assert nino.niveles_actuales()["LV"].nivel == 3
    assert nino.niveles_actuales()["IA"].nivel == 1


def test_codigo_seudonimo_unico_y_sin_nombre(curso, nucleos):
    a = Nino.objects.create(curso=curso, nombre="Sofía Rojas", fecha_ingreso=date(2026, 3, 2))
    b = Nino.objects.create(curso=curso, nombre="Sofía Muñoz", fecha_ingreso=date(2026, 3, 2))
    assert a.codigo != b.codigo
    assert "Sof" not in a.codigo


# --- Nivel máximo según la rúbrica ----------------------------------------------


@pytest.mark.parametrize("nivel", [0, 9])
def test_nivel_validado_fuera_de_la_rubrica_de_8(nino, nucleos, nivel):
    _falla_validacion(lambda: NivelValidado.objects.create(
        nino=nino, nucleo=nucleos[0], nivel=nivel, fecha=date(2026, 4, 1)
    ))


def test_con_rubrica_de_9_niveles_se_acepta_el_9(nino, nucleos, rubrica):
    rubrica.cantidad_niveles = 9
    rubrica.save()
    nv = NivelValidado.objects.create(nino=nino, nucleo=nucleos[0], nivel=9, fecha=date(2026, 4, 1))
    assert nino.nivel_actual(nucleos[0]) == nv
    _falla_validacion(lambda: NivelValidado.objects.create(
        nino=nino, nucleo=nucleos[0], nivel=10, fecha=date(2026, 4, 2)
    ))


def test_la_base_de_datos_rechaza_nivel_0_aunque_se_salte_la_validacion(nino, nucleos):
    # bulk_create no pasa por save(); la restricción de la base sigue exigiendo nivel >= 1.
    _falla_integridad(lambda: NivelValidado.objects.bulk_create([
        NivelValidado(nino=nino, nucleo=nucleos[0], nivel=0, fecha=date(2026, 4, 1))
    ]))


def test_el_nivel_maximo_no_es_una_restriccion_de_la_base(nino, nucleos):
    # Pasar de 8 a 9 niveles no debe requerir migración: la base acepta 9.
    NivelValidado.objects.bulk_create([NivelValidado(nino=nino, nucleo=nucleos[0], nivel=9, fecha=date(2026, 4, 1))])


@pytest.mark.parametrize("nivel", [0, 9])
def test_descriptor_y_meta_fuera_de_la_rubrica(curso, nucleos, nivel):
    _falla_validacion(lambda: DescriptorNivel.objects.create(
        nivel_educativo=NivelEducativo.TRANSICION, nucleo=nucleos[0], nivel=nivel, descripcion="x"
    ))
    _falla_validacion(lambda: MetaSemestre.objects.create(curso=curso, semestre_permanencia=1, nivel_esperado=nivel))


def test_propuesta_puede_no_tener_nivel_pero_no_fuera_de_la_rubrica(nino, nucleos):
    PropuestaNivel.objects.create(nino=nino, nucleo=nucleos[0], nivel=None)
    _falla_validacion(lambda: PropuestaNivel.objects.create(nino=nino, nucleo=nucleos[0], nivel=9))


def test_sin_rubrica_no_se_puede_fijar_un_nivel(nucleos):
    # Sala cuna no tiene rúbrica cargada.
    _falla_validacion(lambda: DescriptorNivel.objects.create(
        nivel_educativo=NivelEducativo.SALA_CUNA, nucleo=nucleos[0], nivel=1, descripcion="x"
    ))


def test_full_clean_reporta_el_campo_del_nivel(curso):
    meta = MetaSemestre(curso=curso, semestre_permanencia=1, nivel_esperado=12)
    with pytest.raises(ValidationError) as error:
        meta.full_clean()
    assert "nivel_esperado" in error.value.message_dict


def test_rubrica_unica_por_nivel_educativo_y_con_al_menos_2_niveles(rubrica):
    _falla_integridad(lambda: Rubrica.objects.create(nivel_educativo=NivelEducativo.TRANSICION, cantidad_niveles=9))
    _falla_integridad(lambda: Rubrica.objects.create(nivel_educativo=NivelEducativo.MEDIO, cantidad_niveles=1))


def test_descriptor_admite_pasos_sugeridos(nucleos, rubrica):
    d = DescriptorNivel.objects.create(
        nivel_educativo=NivelEducativo.TRANSICION, nucleo=nucleos[0], nivel=3, descripcion="x",
        pasos_sugeridos="Observar si nombra la emoción en un cuento.",
    )
    assert d.pasos_sugeridos


# --- Otras restricciones --------------------------------------------------------


def test_meta_unica_por_curso_y_semestre(curso):
    MetaSemestre.objects.create(curso=curso, semestre_permanencia=1, nivel_esperado=1)
    _falla_integridad(lambda: MetaSemestre.objects.create(curso=curso, semestre_permanencia=1, nivel_esperado=2))


def test_semestre_debe_terminar_despues_de_empezar(db):
    _falla_integridad(lambda: Semestre.objects.create(nombre="malo", inicio=date(2026, 7, 1), fin=date(2026, 3, 1)))


def test_oa_unico_y_codigo(nucleos):
    oa = ObjetivoAprendizaje.objects.create(
        nivel_educativo=NivelEducativo.TRANSICION, nucleo=nucleos[1], numero=4, texto="x"
    )
    assert oa.codigo == "OA 4 LV"
    _falla_integridad(lambda: ObjetivoAprendizaje.objects.create(
        nivel_educativo=NivelEducativo.TRANSICION, nucleo=nucleos[1], numero=4, texto="y"
    ))


def test_no_se_acepta_observacion_individual_sin_nino(curso, educadora):
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="x")
    base = {"captura": captura, "fecha": date(2026, 10, 1), "cita": "x"}
    Observacion.objects.create(**base)  # pendiente sin niño: permitido
    Observacion.objects.create(**base, grupal=True, estado=Observacion.Estado.ACEPTADA)  # nota grupal
    _falla_integridad(lambda: Observacion.objects.create(**base, estado=Observacion.Estado.ACEPTADA))


def test_una_asistente_puede_ser_autora_de_una_captura(curso, asistente):
    curso.asistentes.add(asistente)
    captura = Captura.objects.create(curso=curso, autora=asistente, tipo=Captura.Tipo.TEXTO, texto_original="x")
    assert captura.autora == asistente
