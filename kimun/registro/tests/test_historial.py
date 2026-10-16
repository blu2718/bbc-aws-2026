"""Historial de cambios a prueba de adulteración (Task 14).

Cada cambio queda con antes, después, quién, cuándo y por qué; la base de datos rechaza los
UPDATE del historial y la verificación detecta entradas borradas o alteradas y cambios del
dato hechos por fuera de la app.
"""
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.utils import DatabaseError

from registro import historial
from registro.instrumentos import cargar_instrumentos, leer_instrumentos
from registro.models import Captura, Instrumento, Observacion, RegistroCambio, ResultadoInstrumento


@pytest.fixture
def resultado(db, nino, educadora):
    cargar_instrumentos(leer_instrumentos())
    r = ResultadoInstrumento.objects.create(
        nino=nino, instrumento=Instrumento.objects.get(codigo="TEPSI"), fecha_aplicacion=date(2023, 6, 12),
        valores={"campos": {"T": 45}}, estado=ResultadoInstrumento.Estado.POR_REVISAR, registrado_por=educadora,
    )
    historial.registrar(r, RegistroCambio.Accion.CREAR, usuario=educadora)
    return r


def _editar(r, usuario, motivo, **cambios):
    antes = historial.instantanea(r)
    for campo, valor in cambios.items():
        setattr(r, campo, valor)
    r.save()
    return historial.registrar(r, RegistroCambio.Accion.EDITAR, usuario=usuario, motivo=motivo, antes=antes)


def test_cada_cambio_guarda_antes_despues_quien_y_motivo(resultado, educadora):
    e = _editar(resultado, educadora, "El T estaba mal copiado", valores={"campos": {"T": 38}})
    assert e.antes["valores"] == {"campos": {"T": 45}} and e.despues["valores"] == {"campos": {"T": 38}}
    assert e.usuario == educadora and e.motivo == "El T estaba mal copiado"
    assert e.hash_anterior == historial.entradas(RegistroCambio.Objeto.RESULTADO, resultado.pk).first().hash
    legible = historial.historial_legible(resultado)
    assert legible[-1].cambios == [("valores.campos.T", "45", "38")]
    assert historial.verificar(resultado).ok


def test_la_app_no_permite_modificar_ni_borrar_el_historial(resultado):
    e = historial.entradas(RegistroCambio.Objeto.RESULTADO, resultado.pk).first()
    e.motivo = "otro"
    with pytest.raises(ValidationError):
        e.save()
    with pytest.raises(ValidationError):
        e.delete()
    with pytest.raises(ValidationError):
        RegistroCambio.objects.filter(pk=e.pk).update(motivo="otro")
    with pytest.raises(ValidationError):
        RegistroCambio.objects.all().delete()


def test_la_base_de_datos_rechaza_un_update_directo(resultado):
    if connection.vendor != "sqlite":
        pytest.skip("El trigger se crea en SQLite.")
    e = historial.entradas(RegistroCambio.Objeto.RESULTADO, resultado.pk).first()
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("UPDATE registro_registrocambio SET motivo = 'adulterado' WHERE id = %s", [e.pk])


def test_verificar_detecta_un_cambio_hecho_por_fuera_de_la_app(resultado):
    ResultadoInstrumento.objects.filter(pk=resultado.pk).update(valores={"campos": {"T": 60}})
    resultado.refresh_from_db()
    integridad = historial.verificar(resultado)
    assert not integridad.ok and "por fuera de la app" in integridad.texto


def test_verificar_detecta_una_entrada_borrada(resultado, educadora):
    _editar(resultado, educadora, "uno", valores={"campos": {"T": 40}})
    _editar(resultado, educadora, "dos", valores={"campos": {"T": 41}})
    medio = list(historial.entradas(RegistroCambio.Objeto.RESULTADO, resultado.pk))[1]
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM registro_registrocambio WHERE id = %s", [medio.pk])
    integridad = historial.verificar(resultado)
    assert not integridad.ok and "Falta una entrada" in integridad.texto


def test_verificar_detecta_una_entrada_alterada(resultado):
    if connection.vendor != "sqlite":
        pytest.skip("Depende del trigger de SQLite.")
    e = historial.entradas(RegistroCambio.Objeto.RESULTADO, resultado.pk).first()
    # Simula a alguien que se salta el trigger: borra y vuelve a insertar la entrada con otro contenido.
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM registro_registrocambio WHERE id = %s", [e.pk])
    alterada = RegistroCambio(**{f.attname: getattr(e, f.attname) for f in RegistroCambio._meta.concrete_fields})
    alterada.despues = {**e.despues, "valores": {"campos": {"T": 99}}}
    alterada._state.adding = True
    alterada.save(force_insert=True)
    ResultadoInstrumento.objects.filter(pk=resultado.pk).update(valores={"campos": {"T": 99}})
    resultado.refresh_from_db()
    integridad = historial.verificar(resultado)
    assert not integridad.ok and "fue alterado" in integridad.texto


def test_la_cadena_no_se_bifurca(resultado, educadora):
    primera = historial.entradas(RegistroCambio.Objeto.RESULTADO, resultado.pk).first()
    with pytest.raises(IntegrityError), transaction.atomic():
        RegistroCambio.objects.create(
            objeto_tipo=primera.objeto_tipo, objeto_id=primera.objeto_id, curso_id=primera.curso_id,
            accion="editar", despues={}, creado=primera.creado, hash_anterior=primera.hash_anterior, hash="x" * 64,
        )


def test_renombrar_al_nino_no_es_adulterar(db, nino, educadora, curso):
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo="texto", texto_original="Pedro ayudó")
    obs = Observacion.objects.create(captura=captura, nino=nino, fecha=date(2026, 5, 1), cita="ayudó",
                                     estado=Observacion.Estado.ACEPTADA)
    antes = historial.instantanea(obs)
    obs.cita = "ayudó a ordenar"
    obs.save()
    historial.registrar(obs, RegistroCambio.Accion.EDITAR, usuario=educadora, motivo="faltaba", antes=antes)
    nino.nombre = "Pedro Salinas Rojas"
    nino.save()
    obs.refresh_from_db()
    assert historial.verificar(obs).ok
