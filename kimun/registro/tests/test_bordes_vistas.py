"""Casos borde de revisión, informe, propuestas, instrumentos y protección (16-10-2026).

Complementa `test_bordes_integracion.py`: cada caso fija el comportamiento esperado ante
datos que llegan por el admin, traslados de sala, POST incompletos o carreras entre usuarias.
"""
from datetime import date

import pytest
from django.contrib.messages import get_messages
from django.db import connection
from django.urls import reverse
from django.utils import timezone

from registro.historial import ConflictoHistorial, verificar
from registro.instrumentos import cargar_instrumentos, leer_instrumentos
from registro.models import (
    AvisoProteccion,
    Captura,
    Curso,
    Instrumento,
    NivelEducativo,
    NivelValidado,
    Nino,
    Observacion,
    PropuestaNivel,
    RegistroCambio,
    ResultadoInstrumento,
)
from registro.propuestas import registrar_entrada

HTMX = {"HX-Request": "true"}
PENDIENTE = Observacion.Estado.PENDIENTE
ACEPTADA = Observacion.Estado.ACEPTADA


def _mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def _captura(curso, autora, estado=Captura.Estado.PROCESADA):
    return Captura.objects.create(curso=curso, autora=autora, tipo=Captura.Tipo.TEXTO,
                                  texto_original="Pedro y Emilio armaron una torre", estado=estado)


def _obs(captura, nino, estado=PENDIENTE, nucleos=()):
    obs = Observacion.objects.create(captura=captura, nino=nino, fecha=timezone.localdate(),
                                     cita="Armó una torre.", estado=estado)
    obs.nucleos.set(nucleos)
    return obs


@pytest.fixture
def emilio(curso, nucleos):
    return Nino.objects.create(curso=curso, nombre="Emilio Vargas", fecha_ingreso=date(2026, 3, 2))


@pytest.fixture
def otro_curso(jardin, otra_educadora):
    return Curso.objects.create(jardin=jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION,
                                educadora=otra_educadora)


# --- Revisión ---------------------------------------------------------------------------


def test_aceptar_todas_no_se_cae_si_un_nino_cambio_de_curso(client, curso, educadora, nino, emilio, otro_curso):
    """Traslado de sala con observaciones pendientes: se aceptan las demás y la del trasladado queda pendiente."""
    captura = _captura(curso, educadora)
    de_pedro, de_emilio = _obs(captura, nino), _obs(captura, emilio)
    Nino.objects.filter(pk=nino.pk).update(curso=otro_curso)
    client.force_login(educadora)
    client.raise_request_exception = False

    respuesta = client.post(reverse("captura_aceptar_todas", args=[captura.pk]))

    assert respuesta.status_code == 302
    de_pedro.refresh_from_db()
    de_emilio.refresh_from_db()
    assert (de_pedro.estado, de_emilio.estado) == (PENDIENTE, ACEPTADA)
    assert any("otro curso" in m for m in _mensajes(respuesta))


def test_aceptar_una_de_un_nino_trasladado_muestra_el_motivo(client, curso, educadora, nino, otro_curso):
    obs = _obs(_captura(curso, educadora), nino)
    Nino.objects.filter(pk=nino.pk).update(curso=otro_curso)
    client.force_login(educadora)

    respuesta = client.post(reverse("observacion_aceptar", args=[obs.pk]), headers=HTMX)

    assert respuesta.status_code == 200 and "pertenecer al curso" in respuesta.content.decode()
    obs.refresh_from_db()
    assert obs.estado == PENDIENTE


@pytest.mark.parametrize("htmx, estado", [(False, 400), (True, 200)])
def test_editar_con_post_vacio_muestra_los_errores(client, curso, educadora, nino, htmx, estado):
    """Sin HTMX responde 400; con HTMX, 200, porque HTMX 2 no reemplaza el fragmento ante un 4xx."""
    obs = _obs(_captura(curso, educadora), nino)
    client.force_login(educadora)

    respuesta = client.post(reverse("observacion_editar", args=[obs.pk]), {}, headers=HTMX if htmx else {})

    assert respuesta.status_code == estado
    assert "obligatorio" in respuesta.content.decode()
    obs.refresh_from_db()
    assert obs.cita == "Armó una torre."


@pytest.mark.parametrize("metodo", ["put", "delete", "patch"])
def test_editar_solo_acepta_get_y_post(client, curso, educadora, nino, metodo):
    obs = _obs(_captura(curso, educadora), nino)
    client.force_login(educadora)
    assert getattr(client, metodo)(reverse("observacion_editar", args=[obs.pk])).status_code == 405


def test_aceptar_todas_no_confirma_una_captura_en_resguardo(client, curso, educadora, nino):
    captura = _captura(curso, educadora, estado=Captura.Estado.EN_RESGUARDO)
    client.force_login(educadora)
    assert client.post(reverse("captura_aceptar_todas", args=[captura.pk])).status_code == 404


# --- Informe para la familia ------------------------------------------------------------


@pytest.mark.parametrize("alias", [5, True, 1.5, {"apodo": "Majo"}])
def test_un_alias_que_no_es_lista_en_otro_nino_no_rompe_el_informe(client, curso, educadora, nino, alias):
    """El admin acepta cualquier JSON en `alias`: un número no debe tumbar el informe del curso."""
    otra = Nino.objects.create(curso=curso, nombre="María José", fecha_ingreso=date(2026, 3, 2))
    Nino.objects.filter(pk=otra.pk).update(alias=alias)
    client.force_login(educadora)
    client.raise_request_exception = False

    assert client.get(reverse("informe_familia", args=[nino.pk])).status_code == 200


# --- Propuestas de nivel ----------------------------------------------------------------


@pytest.fixture
def lista(nino, nucleos, descriptores, observar_en):
    obs = observar_en(nino, date(2026, 4, 1), [nucleos[0]], cita="Pedro eligió su ropa.")
    propuesta = PropuestaNivel.objects.create(nino=nino, nucleo=nucleos[0])
    registrar_entrada(propuesta)
    propuesta.estado, propuesta.nivel, propuesta.evidencia_suficiente = "lista", 3, True
    propuesta.justificacion = "Avanza en autonomía."
    propuesta.save()
    propuesta.observaciones_citadas.add(obs)
    return propuesta


def test_ajustar_sin_evidencia_suficiente_explica_por_que_no(client, educadora, lista):
    PropuestaNivel.objects.filter(pk=lista.pk).update(nivel=None, evidencia_suficiente=False)
    client.force_login(educadora)

    respuesta = client.post(reverse("ajustar_propuesta", args=[lista.pk]), {f"propuesta-{lista.pk}-nivel": "4"},
                            headers=HTMX)

    assert respuesta.status_code == 200
    assert "no se puede validar un nivel desde esta propuesta" in respuesta.content.decode()
    assert not NivelValidado.objects.filter(propuesta=lista).exists()


def test_aceptar_dos_veces_crea_un_solo_nivel(client, educadora, lista):
    client.force_login(educadora)
    url = reverse("aceptar_propuesta", args=[lista.pk])
    assert client.post(url).status_code == 302
    segunda = client.post(url)
    assert segunda.status_code == 302 and "La propuesta ya estaba resuelta." in _mensajes(segunda)
    assert NivelValidado.objects.filter(propuesta=lista).count() == 1


@pytest.mark.parametrize("nivel", ["abc", "0", "9", "", "3.5", "-1", "99999999999999999999"])
def test_ajustar_con_nivel_invalido_no_valida(client, educadora, lista, nivel):
    client.force_login(educadora)
    respuesta = client.post(reverse("ajustar_propuesta", args=[lista.pk]), {f"propuesta-{lista.pk}-nivel": nivel},
                            headers=HTMX)
    assert respuesta.status_code == 200
    assert not NivelValidado.objects.filter(propuesta=lista).exists()


def test_propuestas_de_otra_educadora_y_reintento_sin_error_dan_404(client, otra_educadora, educadora, lista):
    client.force_login(otra_educadora)
    assert client.post(reverse("aceptar_propuesta", args=[lista.pk])).status_code == 404
    client.force_login(educadora)
    assert client.post(reverse("reintentar_propuesta", args=[lista.pk])).status_code == 404
    assert client.post(reverse("estado_propuesta", args=[lista.nino_id, "IA"])).status_code == 405
    assert client.get(reverse("estado_propuesta", args=[lista.nino_id, "XX"]), headers=HTMX).status_code == 404


# --- Instrumentos e historial -----------------------------------------------------------


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.STORAGES = {**settings.STORAGES, "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}


@pytest.fixture
def confirmado(client, educadora, nino, media):
    cargar_instrumentos(leer_instrumentos())
    nino.fecha_nacimiento = date(2020, 5, 14)
    nino.save()
    client.force_login(educadora)
    datos = {"fecha_aplicacion": "2023-06-12", "origen": "salud", "aplicado_por": "CESFAM", "campo__T": "35",
             "area__C__PB": "10", "area__C__T": "45", "area__L__PB": "8", "area__L__T": "28",
             "area__M__PB": "6", "area__M__T": "41"}
    assert client.post(reverse("instrumento_manual", args=[nino.pk, "TEPSI"]), datos).status_code == 302
    return ResultadoInstrumento.objects.get()


def _conflicto(*args, **kwargs):
    raise ConflictoHistorial("Otra persona guardó un cambio al mismo tiempo. Vuelve a cargar la página.")


def test_descartar_a_la_vez_que_otra_escritura_no_da_500(client, confirmado, monkeypatch):
    monkeypatch.setattr("registro.resultados.registrar", _conflicto)
    client.raise_request_exception = False

    respuesta = client.post(reverse("resultado_instrumento_descartar", args=[confirmado.pk]), {"motivo": "Duplicado"})

    assert respuesta.status_code == 302
    assert any("al mismo tiempo" in m for m in _mensajes(respuesta))
    confirmado.refresh_from_db()
    assert confirmado.estado == ResultadoInstrumento.Estado.CONFIRMADO


def test_retirar_a_la_vez_que_otra_escritura_no_da_500(client, curso, educadora, nino, nucleos, monkeypatch):
    obs = _obs(_captura(curso, educadora), nino, estado=ACEPTADA, nucleos=[nucleos[0]])
    client.force_login(educadora)
    monkeypatch.setattr("registro.resultados.registrar", _conflicto)
    client.raise_request_exception = False

    respuesta = client.post(reverse("observacion_retirar", args=[obs.pk]), {"motivo": "Era de otro niño"})

    assert respuesta.status_code == 302
    assert any("al mismo tiempo" in m for m in _mensajes(respuesta))
    obs.refresh_from_db()
    assert obs.estado == ACEPTADA


def test_un_codigo_de_categoria_que_ya_no_existe_no_rompe_la_ficha(client, confirmado, nino):
    """Si se renombra una categoría en instrumentos.json, los resultados antiguos se siguen viendo."""
    valores = {**confirmado.valores, "categoria": "inexistente",
               "categorias_area": {**confirmado.valores["categorias_area"], "L": "tampoco"}}
    ResultadoInstrumento.objects.filter(pk=confirmado.pk).update(valores=valores)
    client.raise_request_exception = False

    assert client.get(reverse("resultado_instrumento", args=[confirmado.pk])).status_code == 200
    assert client.get(reverse("ficha", args=[nino.pk])).status_code == 200


def test_descartar_con_un_motivo_enorme_se_rechaza(client, confirmado):
    respuesta = client.post(reverse("resultado_instrumento_descartar", args=[confirmado.pk]), {"motivo": "x" * 100_000})
    assert respuesta.status_code == 302
    confirmado.refresh_from_db()
    assert confirmado.estado == ResultadoInstrumento.Estado.CONFIRMADO
    assert any("500 caracteres" in m for m in _mensajes(respuesta))


def test_reintentar_un_resultado_que_no_fallo_no_dice_que_se_perdio_la_hoja(client, confirmado):
    respuesta = client.post(reverse("resultado_instrumento_reintentar", args=[confirmado.pk]))
    assert respuesta.status_code == 302
    assert not any("ya no está guardada" in m for m in _mensajes(respuesta))


def test_mover_un_resultado_a_otro_nino_por_fuera_se_detecta(confirmado, curso):
    otro = Nino.objects.create(curso=curso, nombre="Rubí Soto", fecha_ingreso=date(2026, 3, 2))
    ResultadoInstrumento.objects.filter(pk=confirmado.pk).update(nino=otro)
    confirmado.refresh_from_db()
    assert not verificar(confirmado).ok


@pytest.mark.skipif(connection.vendor != "sqlite", reason="borra con SQL directo")
def test_un_resultado_sin_historial_no_se_muestra_como_integro(confirmado):
    """La app siempre registra la creación: si no hay ninguna entrada, se borraron por fuera."""
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM registro_registrocambio WHERE objeto_tipo=%s AND objeto_id=%s",
                       [RegistroCambio.Objeto.RESULTADO, confirmado.pk])
    assert not verificar(confirmado).ok


def test_editar_un_resultado_con_instrumento_desconocido_da_404(client, confirmado):
    ResultadoInstrumento.objects.filter(pk=confirmado.pk).update(estado=ResultadoInstrumento.Estado.POR_REVISAR)
    url = reverse("resultado_instrumento_editar", args=[confirmado.pk])
    assert client.get(url, {"instrumento": "NOPE"}).status_code == 404
    assert client.get(reverse("instrumento_manual", args=[confirmado.nino_id, "tepsi"])).status_code == 404
    assert Instrumento.objects.filter(codigo="TEPSI").exists()


# --- Protección -------------------------------------------------------------------------


@pytest.fixture
def aviso(curso, asistente_del_curso):
    captura = _captura(curso, asistente_del_curso, estado=Captura.Estado.EN_RESGUARDO)
    return AvisoProteccion.objects.create(captura=captura, senal="relato")


@pytest.mark.parametrize("datos", [{}, {"accion": "borrar"}, {"accion": "PROTOCOLO"}])
def test_resolver_aviso_con_accion_invalida_responde_400(client, educadora, aviso, datos):
    client.force_login(educadora)
    respuesta = client.post(reverse("aviso_resolver", args=[aviso.pk]), datos)
    assert respuesta.status_code == 400
    aviso.refresh_from_db()
    assert aviso.estado == AvisoProteccion.Estado.PENDIENTE


def test_resolver_aviso_dos_veces_conserva_la_primera_decision(client, educadora, directora_del_jardin, aviso):
    client.force_login(educadora)
    client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "protocolo"})
    client.force_login(directora_del_jardin)
    segunda = client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "no_es", "motivo": "Juego"})
    aviso.refresh_from_db()
    assert aviso.estado == AvisoProteccion.Estado.PROTOCOLO and aviso.resuelto_por == educadora
    assert "Este aviso ya se resolvió." in _mensajes(segunda)
    assert Captura.objects.get(pk=aviso.captura_id).estado == Captura.Estado.EN_RESGUARDO


def test_protocolo_con_post_vacio_responde_400(client, jardin, directora_del_jardin):
    client.force_login(directora_del_jardin)
    respuesta = client.post(reverse("protocolo_jardin", args=[jardin.pk]), {})
    assert respuesta.status_code == 400 and "Escribe al menos un paso." in respuesta.content.decode()


def test_directora_de_otro_jardin_no_edita_el_protocolo(client, jardin, directora_de_otro_jardin):
    client.force_login(directora_de_otro_jardin)
    url = reverse("protocolo_jardin", args=[jardin.pk])
    assert client.get(url).status_code == 404
    assert client.post(url, {"pasos": "Avisar"}).status_code == 404


def test_aviso_de_otro_jardin_da_404(client, directora_de_otro_jardin, aviso):
    client.force_login(directora_de_otro_jardin)
    assert client.get(reverse("aviso", args=[aviso.pk])).status_code == 404
    assert client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "protocolo"}).status_code == 404
