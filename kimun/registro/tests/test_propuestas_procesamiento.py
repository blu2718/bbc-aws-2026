"""Cola de propuestas: persistencia, exclusión de trabajos y recuperación."""
import json
import logging
from datetime import date, timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command, CommandError
from django.db import connection, transaction
from django.utils import timezone

from registro.ia.bedrock import ErrorBedrock
from registro.models import NivelValidado, Observacion, PropuestaNivel
from registro.propuestas import (
    procesar_siguiente, recuperar_interrumpidas, solicitar_propuesta, tomar_siguiente,
)
from registro.revision import aceptar, aceptar_todas


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


class ClienteFalso:
    modelo = "modelo-falso"
    ultimo_uso = {"tokens_entrada": 45, "tokens_salida": 12}

    def __init__(self, durante=None, fallo=None):
        self.llamadas = []
        self.durante, self.fallo = durante, fallo

    def invocar_herramienta(self, system, mensaje, herramienta):
        self.llamadas.append((mensaje, connection.in_atomic_block))
        if self.durante:
            self.durante()
        if self.fallo:
            raise self.fallo
        ids = [o["id"] for o in json.loads(mensaje)["observaciones"]]
        return {"nivel": 3, "evidencia_suficiente": True, "observaciones_citadas": ids,
                "conductas_observadas": ["Actúa con autonomía"], "justificacion": "Evidencia de avance."}


@pytest.fixture
def obs(nino, nucleos, observar_en):
    return observar_en(nino, date(2026, 4, 1), [nucleos[0]], estado=Observacion.Estado.PENDIENTE)


def test_aceptar_encola_una_sola_vez_y_es_atomico(obs):
    aceptar(obs)
    aceptar(obs)
    assert PropuestaNivel.objects.filter(nino=obs.nino, nucleo=obs.nucleos.first()).count() == 1
    PropuestaNivel.objects.all().delete()
    obs.estado = "pendiente"
    obs.save()
    with pytest.raises(RuntimeError), transaction.atomic():
        aceptar(obs)
        raise RuntimeError("Cancelar aceptación")
    obs.refresh_from_db()
    assert obs.estado == "pendiente" and not PropuestaNivel.objects.exists()


def test_aceptar_sin_destino_o_grupal_no_encola(obs):
    obs.nucleos.clear()
    aceptar(obs)
    assert not PropuestaNivel.objects.exists()
    obs.estado, obs.grupal, obs.nino = "pendiente", True, None
    obs.save()
    aceptar(obs)
    assert not PropuestaNivel.objects.exists()


def test_aceptar_todas_agrupa_por_nino_y_nucleo(obs, observar_en):
    observar_en(obs.nino, obs.fecha, list(obs.nucleos.all()), estado="pendiente")
    assert aceptar_todas(obs.captura) == (2, 0)
    assert PropuestaNivel.objects.count() == 1


def test_aceptar_incluye_destinos_por_oa_y_omite_otro_nivel(obs, nucleos):
    from registro.models import ObjetivoAprendizaje

    obs.nucleos.clear()
    for nucleo, educativo in [(nucleos[1], "transicion"), (nucleos[2], "medio")]:
        oa = ObjetivoAprendizaje.objects.create(nucleo=nucleo, nivel_educativo=educativo, numero=1, texto="Objetivo")
        obs.oas.add(oa)
    aceptar(obs)
    assert list(PropuestaNivel.objects.values_list("nucleo_id", flat=True)) == [nucleos[1].pk]


def test_encolar_fallido_revierte_la_aceptacion(obs):
    with patch("registro.revision.solicitar_propuesta", side_effect=RuntimeError("Fallo de escritura")):
        with pytest.raises(RuntimeError):
            aceptar(obs)
    obs.refresh_from_db()
    assert obs.estado == "pendiente" and not PropuestaNivel.objects.exists()


def test_solicitud_repetida_reutiliza_trabajo_pendiente(obs):
    a, creada = solicitar_propuesta(obs.nino, obs.nucleos.first())
    b, repetida = solicitar_propuesta(obs.nino, obs.nucleos.first())
    assert creada and not repetida and a.pk == b.pk


def test_tomar_siguiente_es_exclusivo_y_registra_intento(obs):
    aceptar(obs)
    trabajo = tomar_siguiente()
    assert trabajo.estado == "procesando" and trabajo.intentos == 1
    assert trabajo.token_procesamiento and trabajo.procesamiento_iniciado
    assert tomar_siguiente() is None


@pytest.mark.django_db(transaction=True)
def test_guarda_resultado_evidencia_y_modelo_sin_bloquear_red(obs, descriptores):
    aceptar(obs)
    antes = NivelValidado.objects.count()
    cliente = ClienteFalso()
    propuesta = procesar_siguiente(cliente=cliente)
    assert propuesta.estado == "lista" and propuesta.nivel == 3
    assert propuesta.evidencia_suficiente and propuesta.modelo == cliente.modelo
    assert propuesta.uso_modelo == cliente.ultimo_uso
    assert list(propuesta.observaciones_citadas.all()) == [obs]
    assert propuesta.huella_entrada and propuesta.nivel_referencia_id
    assert propuesta.token_procesamiento is None
    assert cliente.llamadas[0][1] is False
    assert NivelValidado.objects.count() == antes
    assert solicitar_propuesta(obs.nino, propuesta.nucleo)[0].pk == propuesta.pk


def test_sin_evidencia_queda_lista_sin_nivel_y_sin_llamar(obs):
    solicitar_propuesta(obs.nino, obs.nucleos.first())
    cliente = ClienteFalso()
    propuesta = procesar_siguiente(cliente=cliente)
    assert propuesta.estado == "lista" and propuesta.nivel is None
    assert not propuesta.evidencia_suficiente and cliente.llamadas == []


@pytest.mark.parametrize("fallo", [ErrorBedrock("Pedro: cita privada"), RuntimeError("Pedro: secreto")])
def test_error_se_persiste_sin_datos_sensibles_y_reintento_es_explicito(obs, descriptores, fallo):
    aceptar(obs)
    propuesta = procesar_siguiente(cliente=ClienteFalso(fallo=fallo))
    assert propuesta.estado == "error" and "Pedro" not in propuesta.error
    assert tomar_siguiente() is None
    repetida, creada = solicitar_propuesta(obs.nino, propuesta.nucleo)
    assert not creada and repetida.pk == propuesta.pk
    nueva, creada = solicitar_propuesta(obs.nino, propuesta.nucleo, reintentar=True)
    assert creada and nueva.pk != propuesta.pk
    assert PropuestaNivel.objects.get(pk=propuesta.pk).estado == "error"
    assert procesar_siguiente(cliente=ClienteFalso()).estado == "lista"


@pytest.mark.parametrize("fallo,diagnostico", [
    (ErrorBedrock("Pedro: cita privada", "AccessDeniedException"), "Bedrock: AccessDeniedException"),
    (RuntimeError("Pedro: secreto"), "error inesperado: RuntimeError"),
])
def test_error_deja_diagnostico_en_el_log_sin_textos(obs, descriptores, caplog, fallo, diagnostico):
    aceptar(obs)
    with caplog.at_level(logging.WARNING, logger="registro.propuestas"):
        propuesta = procesar_siguiente(cliente=ClienteFalso(fallo=fallo))
    assert propuesta.estado == "error"
    assert f"La propuesta #{propuesta.pk} quedó en error ({diagnostico})." in caplog.text
    assert "Pedro" not in caplog.text and "cita" not in caplog.text and "secreto" not in caplog.text


def test_configuracion_incompleta_se_guarda_como_error(obs):
    aceptar(obs)
    propuesta = procesar_siguiente(cliente=ClienteFalso())
    assert propuesta.estado == "error" and "rúbrica" in propuesta.error


def test_si_cambia_evidencia_no_publica_resultado_y_encola_nuevo(obs, descriptores):
    aceptar(obs)
    def cambiar():
        Observacion.objects.filter(pk=obs.pk).update(cita="Una conducta diferente")
    propuesta = procesar_siguiente(cliente=ClienteFalso(durante=cambiar))
    assert propuesta.estado == "obsoleta" and propuesta.nivel is None
    assert not propuesta.observaciones_citadas.exists()
    nueva = PropuestaNivel.objects.get(estado="solicitada")
    assert nueva.pk != propuesta.pk
    assert procesar_siguiente(cliente=ClienteFalso()).estado == "lista"


def test_dos_procesadores_no_invocan_el_mismo_trabajo(obs, descriptores):
    aceptar(obs)
    segundo = ClienteFalso()
    primero = ClienteFalso(durante=lambda: procesar_siguiente(cliente=segundo))
    assert procesar_siguiente(cliente=primero).estado == "lista"
    assert len(primero.llamadas) == 1 and segundo.llamadas == []


@pytest.mark.django_db(transaction=True)
def test_dos_hilos_compiten_por_la_misma_solicitud(obs):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connections

    aceptar(obs)
    barrera = Barrier(2)
    def tomar():
        try:
            barrera.wait(timeout=5)
            trabajo = tomar_siguiente()
            return trabajo.pk if trabajo else None
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(lambda _: tomar(), range(2)))
    assert sum(pk is not None for pk in resultados) == 1
    propuesta = PropuestaNivel.objects.get()
    assert propuesta.estado == "procesando" and propuesta.intentos == 1


def test_recuperacion_acotada_y_token_anterior_no_sobrescribe(obs, descriptores):
    aceptar(obs)
    def recuperar_y_completar():
        PropuestaNivel.objects.filter(estado="procesando").update(
            procesamiento_iniciado=timezone.now() - timedelta(seconds=400))
        assert recuperar_interrumpidas() == 1
        assert procesar_siguiente(cliente=ClienteFalso()).estado == "lista"
    propuesta = procesar_siguiente(cliente=ClienteFalso(durante=recuperar_y_completar))
    assert propuesta.estado == "lista" and propuesta.intentos == 2
    assert propuesta.nivel == 3 and PropuestaNivel.objects.count() == 1


def test_agotar_intentos_no_deja_un_trabajo_activo(obs):
    aceptar(obs)
    for i in range(3):
        trabajo = tomar_siguiente()
        assert trabajo.intentos == i + 1
        PropuestaNivel.objects.filter(pk=trabajo.pk).update(procesamiento_iniciado=timezone.now() - timedelta(seconds=400))
        assert recuperar_interrumpidas() == 1
    trabajo.refresh_from_db()
    assert trabajo.estado == "error" and tomar_siguiente() is None


def test_no_recupera_trabajos_recientes_y_respeta_limite(obs):
    aceptar(obs)
    tomar_siguiente()
    assert recuperar_interrumpidas() == 0


def test_recuperacion_respeta_el_limite_de_lote(obs, nucleos):
    solicitar_propuesta(obs.nino, nucleos[0])
    solicitar_propuesta(obs.nino, nucleos[1])
    for _ in range(2):
        trabajo = tomar_siguiente()
        PropuestaNivel.objects.filter(pk=trabajo.pk).update(procesamiento_iniciado=timezone.now() - timedelta(seconds=400))
    assert recuperar_interrumpidas(limite=1) == 1
    assert PropuestaNivel.objects.filter(estado="procesando").count() == 1


def test_lista_pierde_vigencia_y_se_solicita_otra(obs, descriptores):
    aceptar(obs)
    anterior = procesar_siguiente(cliente=ClienteFalso())
    Observacion.objects.filter(pk=obs.pk).update(cita="Otra evidencia")
    nueva, creada = solicitar_propuesta(obs.nino, anterior.nucleo)
    anterior.refresh_from_db()
    assert creada and nueva.estado == "solicitada" and anterior.estado == "obsoleta"


def test_comando_once_no_duerme_y_procesa_solo_un_trabajo(obs):
    salida = StringIO()
    with patch("registro.management.commands.procesar_propuestas.procesar_siguiente", return_value=None) as procesar:
        call_command("procesar_propuestas", once=True, stdout=salida)
    assert procesar.call_count == 1


def test_comando_continuo_espera_sin_trabajos_y_termina_al_interrumpir(obs):
    salida = StringIO()
    with patch("registro.management.commands.procesar_propuestas.procesar_siguiente", return_value=None), \
         patch("registro.management.commands.procesar_propuestas.time.sleep", side_effect=KeyboardInterrupt) as dormir:
        call_command("procesar_propuestas", intervalo=1, stdout=salida)
    dormir.assert_called_once_with(1)
    assert "Procesamiento detenido" in salida.getvalue()


@pytest.mark.parametrize("opciones", [{"intervalo": 0}, {"caducidad": 1}])
def test_comando_rechaza_configuracion_invalida(opciones):
    with pytest.raises(CommandError):
        call_command("procesar_propuestas", once=True, **opciones)
