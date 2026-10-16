"""Task 7, punto 1: contrato y vigencia; sin Bedrock ni decisiones desde la web."""
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from registro.models import NivelValidado, Nino, Observacion, PropuestaNivel
from registro.propuestas import comprobar_vigencia, huella_entrada, registrar_entrada


@pytest.fixture
def propuesta(nino, nucleos):
    return PropuestaNivel.objects.create(nino=nino, nucleo=nucleos[0])


def test_solicitud_inicial_no_modifica_niveles(propuesta, nino, nucleos):
    assert propuesta.estado == PropuestaNivel.Estado.SOLICITADA
    assert propuesta.intentos == 0
    assert propuesta.procesamiento_iniciado is None
    assert propuesta.resuelta_por is None and propuesta.resuelta_en is None
    assert propuesta.rubrica_provisoria is None  # Aún no se preparó la entrada.
    assert nino.nivel_actual(nucleos[0]).nivel == 1


def test_registra_referencia_huella_y_procedencia(propuesta, descriptores):
    registrar_entrada(propuesta)
    propuesta.refresh_from_db()
    assert propuesta.nivel_referencia == propuesta.nino.nivel_actual(propuesta.nucleo)
    assert len(propuesta.huella_entrada) == 64
    assert propuesta.rubrica_provisoria is False
    assert propuesta.version_prompt
    assert comprobar_vigencia(propuesta)


def test_sin_descriptores_la_procedencia_es_provisoria(nino, nucleos):
    propuesta = PropuestaNivel.objects.create(nino=nino, nucleo=nucleos[2])
    registrar_entrada(propuesta)
    assert propuesta.rubrica_provisoria is True


@pytest.mark.parametrize("estado", ["solicitada", "procesando"])
def test_solo_una_solicitud_activa_incluso_con_bulk_create(propuesta, estado):
    datos = {"nino": propuesta.nino, "nucleo": propuesta.nucleo, "estado": estado}
    if estado == "procesando":
        datos.update(procesamiento_iniciado=timezone.now(), intentos=1)
    with pytest.raises(IntegrityError), transaction.atomic():
        PropuestaNivel.objects.bulk_create([PropuestaNivel(**datos)])


@pytest.mark.parametrize("estado", ["lista", "rechazada", "obsoleta", "error"])
def test_el_historial_no_impide_una_nueva_solicitud(propuesta, estado):
    # La actualización directa prueba específicamente la restricción de unicidad.
    PropuestaNivel.objects.filter(pk=propuesta.pk).update(estado=estado)
    nueva = PropuestaNivel.objects.create(nino=propuesta.nino, nucleo=propuesta.nucleo)
    assert nueva.pk != propuesta.pk


def test_solicitudes_de_otro_nucleo_o_nino_son_independientes(propuesta, nucleos):
    otro = Nino.objects.create(curso=propuesta.nino.curso, nombre="Otra niña", fecha_ingreso=date(2026, 3, 2))
    PropuestaNivel.objects.create(nino=propuesta.nino, nucleo=nucleos[1])
    PropuestaNivel.objects.create(nino=otro, nucleo=propuesta.nucleo)


@pytest.mark.parametrize("suficiente,nivel", [(False, 3), (True, None)])
def test_nivel_y_suficiencia_deben_ser_coherentes(propuesta, suficiente, nivel):
    propuesta.evidencia_suficiente, propuesta.nivel = suficiente, nivel
    with pytest.raises(ValidationError):
        propuesta.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        PropuestaNivel.objects.filter(pk=propuesta.pk).update(evidencia_suficiente=suficiente, nivel=nivel)


def test_procesando_exige_inicio_e_intento(propuesta):
    propuesta.estado = PropuestaNivel.Estado.PROCESANDO
    with pytest.raises(ValidationError):
        propuesta.save()
    propuesta.procesamiento_iniciado = timezone.now()
    propuesta.intentos = 1
    propuesta.save()
    propuesta.refresh_from_db()
    assert propuesta.procesamiento_iniciado and propuesta.intentos == 1


def test_referencia_debe_corresponder_al_mismo_nino_y_nucleo(propuesta, nucleos):
    propuesta.nivel_referencia = propuesta.nino.nivel_actual(nucleos[1])
    with pytest.raises(ValidationError, match="referencia"):
        propuesta.save()


@pytest.mark.parametrize("estado", ["aceptada", "rechazada"])
def test_resolucion_exige_usuaria_y_fecha(propuesta, estado):
    propuesta.estado = estado
    with pytest.raises(ValidationError, match="resolución"):
        propuesta.save()


def test_aceptacion_exige_nivel_y_entrada_vigente(propuesta, educadora):
    propuesta.estado = PropuestaNivel.Estado.ACEPTADA
    propuesta.resuelta_por, propuesta.resuelta_en = educadora, timezone.now()
    with pytest.raises(ValidationError):
        propuesta.save()
    propuesta.nivel, propuesta.evidencia_suficiente = 3, True
    with pytest.raises(ValidationError, match="vigente"):
        propuesta.save()


def test_guarda_resolucion_y_no_crea_validaciones(propuesta, educadora):
    registrar_entrada(propuesta)
    antes = NivelValidado.objects.count()
    propuesta.estado = PropuestaNivel.Estado.LISTA
    propuesta.nivel, propuesta.evidencia_suficiente = 3, True
    propuesta.save()
    propuesta.estado = PropuestaNivel.Estado.ACEPTADA
    propuesta.resuelta_por, propuesta.resuelta_en = educadora, timezone.now()
    propuesta.save()
    propuesta.refresh_from_db()
    assert propuesta.resuelta_por == educadora and propuesta.resuelta_en
    assert NivelValidado.objects.count() == antes  # La decisión atómica se implementa en el punto 5.


def test_una_solicitud_aun_sin_resultado_no_es_aceptable(propuesta, educadora):
    registrar_entrada(propuesta)
    propuesta.estado = PropuestaNivel.Estado.ACEPTADA
    propuesta.nivel, propuesta.evidencia_suficiente = 3, True
    propuesta.resuelta_por, propuesta.resuelta_en = educadora, timezone.now()
    with pytest.raises(ValidationError, match="lista"):
        propuesta.save()


def test_no_permite_aceptar_evidencia_insuficiente_en_la_base(propuesta):
    with pytest.raises(IntegrityError), transaction.atomic():
        PropuestaNivel.objects.filter(pk=propuesta.pk).update(estado="aceptada")


@pytest.mark.parametrize("cambio", ["evidencia", "nivel", "rubrica", "prompt", "alias"])
def test_cambios_invalidan_una_propuesta_lista(propuesta, observar_en, descriptores, cambio):
    obs = observar_en(propuesta.nino, date(2026, 4, 1), [propuesta.nucleo])
    registrar_entrada(propuesta)
    propuesta.estado = PropuestaNivel.Estado.LISTA
    propuesta.nivel, propuesta.evidencia_suficiente = 3, True
    propuesta.save()
    opciones = {}
    if cambio == "evidencia":
        obs.cita = "Una conducta diferente"
        obs.save()
    elif cambio == "nivel":
        NivelValidado.objects.create(nino=propuesta.nino, nucleo=propuesta.nucleo, nivel=2, fecha=timezone.localdate())
    elif cambio == "rubrica":
        descriptor = propuesta.nucleo.descriptores.first()
        descriptor.conducta = "Conducta actualizada"
        descriptor.save()
    elif cambio == "prompt":
        opciones["version_prompt"] = "otra-version-del-prompt"
    else:
        propuesta.nino.alias = ["Pedrito"]
        propuesta.nino.save()
    assert not comprobar_vigencia(propuesta, **opciones)
    propuesta.refresh_from_db()
    assert propuesta.estado == PropuestaNivel.Estado.OBSOLETA
    assert propuesta.nivel == 3  # Conservar el resultado histórico.
    propuesta.estado = PropuestaNivel.Estado.ACEPTADA
    propuesta.resuelta_por, propuesta.resuelta_en = propuesta.nino.curso.educadora, timezone.now()
    with pytest.raises(ValidationError):
        propuesta.save()


def test_huella_ignora_observaciones_no_utilizables(propuesta, observar_en):
    antes = huella_entrada(propuesta.nino, propuesta.nucleo)
    for estado, grupal in [(Observacion.Estado.PENDIENTE, False), (Observacion.Estado.DESCARTADA, False),
                           (Observacion.Estado.ACEPTADA, True)]:
        observar_en(propuesta.nino, date(2026, 4, 1), [propuesta.nucleo], estado=estado, grupal=grupal)
    assert huella_entrada(propuesta.nino, propuesta.nucleo) == antes


def test_huella_incluye_evidencia_etiquetada_solo_por_oa(propuesta, observar_en):
    from registro.models import ObjetivoAprendizaje

    oa = ObjetivoAprendizaje.objects.create(nucleo=propuesta.nucleo, nivel_educativo=propuesta.nino.curso.nivel_educativo,
                                            numero=1, texto="Objetivo")
    antes = huella_entrada(propuesta.nino, propuesta.nucleo)
    observar_en(propuesta.nino, date(2026, 4, 1), [], oas=[oa])
    assert huella_entrada(propuesta.nino, propuesta.nucleo) != antes


def test_huella_oficial_reserva_el_segundo_ejemplo(propuesta, descriptores):
    antes = huella_entrada(propuesta.nino, propuesta.nucleo)
    descriptor = propuesta.nucleo.descriptores.first()
    descriptor.ejemplos[1] = "Ejemplo reservado actualizado"
    descriptor.save()
    assert huella_entrada(propuesta.nino, propuesta.nucleo) == antes
    descriptor.ejemplos[0] = "Referencia del prompt actualizada"
    descriptor.save()
    assert huella_entrada(propuesta.nino, propuesta.nucleo) != antes


def test_cambiar_maximo_de_rubrica_invalida_la_entrada(propuesta, rubrica):
    registrar_entrada(propuesta)
    rubrica.cantidad_niveles = 9
    rubrica.save()
    assert not comprobar_vigencia(propuesta)


def test_full_clean_aplica_el_contrato(propuesta):
    propuesta.nivel = 3
    with pytest.raises(ValidationError):
        propuesta.full_clean()


def test_no_se_puede_reescribir_la_entrada_de_una_propuesta_lista(propuesta):
    registrar_entrada(propuesta)
    propuesta.estado = PropuestaNivel.Estado.LISTA
    propuesta.save()
    with pytest.raises(ValidationError):
        registrar_entrada(propuesta, version_prompt="otra-version")


def test_la_base_exige_inicio_de_procesamiento_y_resolucion_completa(propuesta, educadora):
    with pytest.raises(IntegrityError), transaction.atomic():
        PropuestaNivel.objects.filter(pk=propuesta.pk).update(estado="procesando")
    with pytest.raises(IntegrityError), transaction.atomic():
        PropuestaNivel.objects.filter(pk=propuesta.pk).update(resuelta_por=educadora)


def test_sin_entrada_registrada_no_es_vigente(propuesta):
    assert not comprobar_vigencia(propuesta)


def test_comprobar_vigencia_no_reescribe_una_resolucion(propuesta, educadora):
    registrar_entrada(propuesta)
    propuesta.estado = PropuestaNivel.Estado.RECHAZADA
    propuesta.resuelta_por, propuesta.resuelta_en = educadora, timezone.now()
    propuesta.save()
    assert not comprobar_vigencia(propuesta, version_prompt="otra-version")
    propuesta.refresh_from_db()
    assert propuesta.estado == PropuestaNivel.Estado.RECHAZADA
