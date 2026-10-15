"""La migración conserva el historial anterior, aunque tenga solicitudes duplicadas."""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def _insertar(modelo, **datos):
    # Los modelos históricos conservan ValidaNivelMixin, pero no sus métodos
    # concretos. Insertar directamente representa los registros de la versión antigua.
    return modelo.objects.bulk_create([modelo(**datos)])[0]


@pytest.mark.django_db(transaction=True)
def test_migracion_retira_solicitudes_sin_huella_y_conserva_decisiones(nino, nucleos, educadora):
    anterior = [("registro", "0002_descriptor_rubrica_integra")]
    nueva = [("registro", "0003_propuesta_contrato")]
    executor = MigrationExecutor(connection)
    try:
        executor.migrate(anterior)
        apps = executor.loader.project_state(anterior).apps
        Propuesta = apps.get_model("registro", "PropuestaNivel")
        base = {"nino_id": nino.pk, "nucleo_id": nucleos[0].pk}
        a = _insertar(Propuesta, **base)
        b = _insertar(Propuesta, **base)  # Antes se permitían duplicadas.
        lista = _insertar(Propuesta, **base, estado="lista", nivel=3, evidencia_suficiente=True)
        aceptada = _insertar(Propuesta, **base, estado="aceptada", nivel=2, evidencia_suficiente=True)
        Nivel = apps.get_model("registro", "NivelValidado")
        validado = _insertar(Nivel, **base, nivel=2, fecha="2026-10-15", validado_por_id=educadora.pk,
                             propuesta_id=aceptada.pk)
        executor = MigrationExecutor(connection)
        executor.migrate(nueva)
        Propuesta = executor.loader.project_state(nueva).apps.get_model("registro", "PropuestaNivel")
        assert set(Propuesta.objects.filter(pk__in=[a.pk, b.pk, lista.pk]).values_list("estado", flat=True)) == {"obsoleta"}
        assert Propuesta.objects.get(pk=lista.pk).nivel == 3
        historica = Propuesta.objects.get(pk=aceptada.pk)
        assert historica.estado == "aceptada" and historica.nivel == 2
        assert historica.resuelta_por_id is None  # No atribuir una decisión antigua sin datos.
        assert historica.huella_entrada == "" and historica.rubrica_provisoria is None
        assert Nivel.objects.get(pk=validado.pk).propuesta_id == historica.pk
        assert _insertar(Propuesta, **base).estado == "solicitada"
    finally:
        MigrationExecutor(connection).migrate([("registro", "0005_propuesta_decision")])


@pytest.mark.django_db(transaction=True)
def test_migracion_no_corrige_automaticamente_evidencia_incoherente(nino, nucleos):
    anterior = [("registro", "0002_descriptor_rubrica_integra")]
    nueva = [("registro", "0003_propuesta_contrato")]
    executor = MigrationExecutor(connection)
    executor.migrate(anterior)
    Propuesta = executor.loader.project_state(anterior).apps.get_model("registro", "PropuestaNivel")
    incoherente = _insertar(Propuesta, nino_id=nino.pk, nucleo_id=nucleos[0].pk, nivel=3)
    try:
        with pytest.raises(RuntimeError, match="nivel y evidencia incoherentes"):
            MigrationExecutor(connection).migrate(nueva)
        assert Propuesta.objects.get(pk=incoherente.pk).nivel == 3
    finally:
        Propuesta.objects.filter(pk=incoherente.pk).delete()
        MigrationExecutor(connection).migrate([("registro", "0005_propuesta_decision")])
