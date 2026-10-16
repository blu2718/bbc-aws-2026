"""Aviso ante posibles vulneraciones de derechos (PLAN.md, Task 13), con un cliente de Bedrock falso."""
import logging
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from registro.alertas import EstadoDatos, tabla_del_curso
from registro.cobertura import cobertura_del_nino
from registro.ficha import armar_ficha
from registro.ia import separar_completo
from registro.models import AvisoProteccion, Captura, NivelEducativo, ObjetivoAprendizaje, Observacion, Semestre
from registro.procesamiento import procesar, tomar_siguiente
from registro.propuestas import preparar_evidencia
from registro.revision import contar_pendientes, revision_del_curso
from registro.tests.ia.conftest import ClienteFalso

NOTA = "Pedro llegó con un moretón en el brazo y dijo que su papá le pegó con la correa"
CATALOGO = {
    "nivel_educativo": "transicion",
    "nucleos": [
        {"sigla": "IA", "nombre": "Identidad y Autonomía", "oas": [{"numero": 1, "codigo": "OA 1 IA", "texto": "Comunicar."}]},
        {"sigla": "LV", "nombre": "Lenguaje Verbal", "oas": []},
        {"sigla": "PM", "nombre": "Pensamiento Matemático", "oas": []},
    ],
}
MARCADA = {"observaciones": [], "pregunta": None, "posible_vulneracion": True, "senal": "relato"}


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def hoy():
    return timezone.localdate()


@pytest.fixture
def semestre(hoy):
    return Semestre.objects.create(nombre="actual", inicio=hoy - timedelta(days=200), fin=hoy + timedelta(days=60))


@pytest.fixture
def oa_ia(nucleos):
    return ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=nucleos[0], numero=1, texto="Comunicar.")


def _obs_normal(nombre="Pedro", cita="Pedro contó hasta 10"):
    return {
        "nombre_detectado": nombre, "fecha": None, "cita_literal": cita, "interpretacion": None,
        "nucleos": ["IA"], "oas": ["OA 1 IA"], "apoyo": "autonomo", "efecto": "avance",
        "grupal": False, "todo_el_curso": False,
    }


def _normal(*observaciones):
    return {"observaciones": list(observaciones), "pregunta": None, "posible_vulneracion": False, "senal": None}


def _procesar(curso, autora, respuesta, texto=NOTA):
    Captura.objects.create(curso=curso, autora=autora, tipo=Captura.Tipo.TEXTO, texto_original=texto)
    captura = tomar_siguiente()
    creadas = procesar(captura, cliente=ClienteFalso(respuesta), catalogo=CATALOGO)
    captura.refresh_from_db()
    return captura, creadas


# --- Separación -----------------------------------------------------------------------


def test_si_el_modelo_marca_no_hay_observaciones_ni_pregunta():
    # Aunque el modelo devuelva observaciones y una pregunta, se descartan: no se indaga.
    respuesta = MARCADA | {"observaciones": [_obs_normal()], "pregunta": "¿Quién le pegó?"}
    resultado = separar_completo(NOTA, "2026-10-15", ["Pedro Salinas"], CATALOGO, cliente=ClienteFalso(respuesta))
    assert resultado == ([], None, "relato")


def test_una_senal_desconocida_queda_como_otra():
    resultado = separar_completo(NOTA, "2026-10-15", [], CATALOGO, cliente=ClienteFalso(MARCADA | {"senal": "rara"}))
    assert resultado.senal == "otra"


def test_sin_el_campo_la_nota_se_separa_normal():
    respuesta = {"observaciones": [_obs_normal()], "pregunta": None}
    resultado = separar_completo("Pedro contó hasta 10", "2026-10-15", ["Pedro Salinas"], CATALOGO, cliente=ClienteFalso(respuesta))
    assert resultado.senal is None and len(resultado.observaciones) == 1


def test_la_herramienta_exige_la_marca_y_el_prompt_trae_las_reglas():
    cliente = ClienteFalso(_normal())
    separar_completo("nota", "2026-10-15", [], CATALOGO, cliente=cliente)
    llamada = cliente.llamadas[0]
    esquema = llamada["herramienta"]["inputSchema"]["json"]
    assert {"posible_vulneracion", "senal"} <= set(esquema["required"])
    assert "## Posible vulneración de derechos" in llamada["system"]
    assert "agresiones entre niños" in llamada["system"]


# --- Proceso de fondo -------------------------------------------------------------------


def test_una_nota_marcada_no_genera_observaciones_y_crea_un_aviso(curso, educadora, nino):
    captura, creadas = _procesar(curso, educadora, MARCADA)
    assert creadas == []
    assert captura.estado == Captura.Estado.EN_RESGUARDO and captura.pregunta == ""
    aviso = AvisoProteccion.objects.get(captura=captura)
    assert (aviso.estado, aviso.senal) == (AvisoProteccion.Estado.PENDIENTE, "relato")
    assert not Observacion.todas.filter(captura=captura).exists()


def test_una_pelea_entre_ninos_se_procesa_normal(curso, educadora, nino):
    captura, creadas = _procesar(curso, educadora, _normal(_obs_normal(cita="Pedro empujó a Emilio por un juguete")),
                                 texto="Pedro empujó a Emilio por un juguete")
    assert captura.estado == Captura.Estado.PROCESADA and len(creadas) == 1
    assert not AvisoProteccion.objects.exists()


def test_si_quedaban_observaciones_de_antes_se_descartan(curso, educadora, nino):
    captura, _ = _procesar(curso, educadora, _normal(_obs_normal()), texto="Pedro contó hasta 10")
    Captura.objects.filter(pk=captura.pk).update(estado=Captura.Estado.PENDIENTE)
    procesar(tomar_siguiente(), cliente=ClienteFalso(MARCADA), catalogo=CATALOGO)
    assert set(Observacion.todas.filter(captura=captura).values_list("estado", flat=True)) == {Observacion.Estado.DESCARTADA}


def test_el_texto_de_la_nota_no_aparece_en_los_registros(curso, educadora, nino, caplog):
    with caplog.at_level(logging.DEBUG):
        captura, _ = _procesar(curso, educadora, MARCADA)
    assert "moretón" not in caplog.text and "correa" not in caplog.text
    assert f"Captura {captura.pk}" in caplog.text


# --- Permisos y vistas ------------------------------------------------------------------


@pytest.fixture
def aviso(curso, asistente_del_curso, nino):
    captura, _ = _procesar(curso, asistente_del_curso, MARCADA)
    return captura.aviso_proteccion


@pytest.mark.parametrize("quien", ["educadora", "directora_del_jardin"])
def test_la_educadora_y_la_directora_ven_el_aviso_con_el_texto(client, request, aviso, quien):
    client.force_login(request.getfixturevalue(quien))
    html = client.get(reverse("aviso", args=[aviso.pk])).content.decode()
    assert NOTA in html and "No interrogues al niño" in html
    listado = client.get(reverse("avisos")).content.decode()
    assert reverse("aviso", args=[aviso.pk]) in listado and "moretón" not in listado
    assert "Avisos de protección: <strong>1</strong>" in client.get(reverse("inicio"), follow=True).content.decode()


@pytest.mark.parametrize("quien", ["asistente_del_curso", "otra_educadora"])
def test_la_asistente_y_otra_educadora_reciben_404(client, request, aviso, quien):
    client.force_login(request.getfixturevalue(quien))
    assert client.get(reverse("aviso", args=[aviso.pk])).status_code == 404
    assert client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "protocolo"}).status_code == 404


def test_quien_registro_ve_su_captura_en_resguardo_sin_el_texto(client, aviso, asistente_del_curso):
    client.force_login(asistente_del_curso)
    html = client.get(reverse("captura", args=[aviso.captura_id])).content.decode()
    assert "quedó en resguardo" in html and "moretón" not in html
    assert "moretón" not in client.get(reverse("registrar", args=[aviso.captura.curso_id])).content.decode()


def test_informe_a_la_directora_deja_la_captura_en_resguardo(client, aviso, educadora):
    client.force_login(educadora)
    client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "protocolo"})
    aviso.refresh_from_db()
    assert (aviso.estado, aviso.resuelto_por) == (AvisoProteccion.Estado.PROTOCOLO, educadora)
    assert aviso.resuelto_en is not None
    assert Captura.objects.get(pk=aviso.captura_id).estado == Captura.Estado.EN_RESGUARDO


def test_no_es_una_vulneracion_exige_motivo_y_reprocesa(client, aviso, directora_del_jardin, nino):
    client.force_login(directora_del_jardin)
    sin_motivo = client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "no_es", "motivo": " "})
    assert sin_motivo.status_code == 400
    aviso.refresh_from_db()
    assert aviso.estado == AvisoProteccion.Estado.PENDIENTE

    client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "no_es", "motivo": "Era un juego de roles"})
    aviso.refresh_from_db()
    assert (aviso.estado, aviso.motivo) == (AvisoProteccion.Estado.NO_ES, "Era un juego de roles")
    # Vuelve a la cola y se separa como cualquier otra: el prompt ya no pide marcarla y,
    # aunque el modelo la marque igual, sus observaciones se usan (antes quedaba con 0).
    captura = tomar_siguiente()
    assert captura.pk == aviso.captura_id
    cliente = ClienteFalso(MARCADA | {"observaciones": [_obs_normal()]})
    assert len(procesar(captura, cliente=cliente, catalogo=CATALOGO)) == 1
    prompt = cliente.llamadas[0]["system"]
    assert "## Posible vulneración de derechos" not in prompt and "## Nota ya revisada" in prompt
    assert Captura.objects.get(pk=captura.pk).estado == Captura.Estado.PROCESADA
    aviso.refresh_from_db()
    assert aviso.estado == AvisoProteccion.Estado.NO_ES and aviso.resuelto_por == directora_del_jardin


def test_resolver_un_aviso_ya_resuelto_no_pisa_quien_lo_resolvio(client, aviso, directora_del_jardin, educadora):
    """Dos personas resuelven a la vez: la segunda llega con el aviso todavía pendiente en memoria."""
    from registro import views_proteccion

    client.force_login(directora_del_jardin)
    client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "protocolo"})
    pendiente_en_memoria = AvisoProteccion.objects.get(pk=aviso.pk)
    pendiente_en_memoria.estado = AvisoProteccion.Estado.PENDIENTE
    client.force_login(educadora)
    original = views_proteccion.get_object_or_404
    views_proteccion.get_object_or_404 = lambda *a, **k: pendiente_en_memoria
    try:
        client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "no_es", "motivo": "Era un juego"})
    finally:
        views_proteccion.get_object_or_404 = original
    aviso.refresh_from_db()
    assert (aviso.estado, aviso.resuelto_por) == (AvisoProteccion.Estado.PROTOCOLO, directora_del_jardin)
    assert Captura.objects.get(pk=aviso.captura_id).estado == Captura.Estado.EN_RESGUARDO


def test_a_una_nota_con_aviso_no_se_le_suma_contexto(client, aviso, directora_del_jardin, educadora):
    """Después de "No es una vulneración" la nota ya no se revisa al reordenarla: el contexto va en una nota nueva."""
    client.force_login(directora_del_jardin)
    client.post(reverse("aviso_resolver", args=[aviso.pk]), {"accion": "no_es", "motivo": "Era un juego de roles"})
    procesar(tomar_siguiente(), cliente=ClienteFalso(_normal(_obs_normal()) | {"pregunta": "¿Quién más jugó?"}),
             catalogo=CATALOGO)
    captura = Captura.objects.get(pk=aviso.captura_id)
    assert captura.estado == Captura.Estado.PROCESADA and captura.pregunta
    client.force_login(educadora)
    client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "Dijo que su tío le pega"})
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA and "tío" not in captura.texto_original
    pagina = client.get(reverse("captura", args=[captura.pk])).content.decode()
    assert "regístralo como una nota nueva" in pagina


# --- Exclusión de la evaluación ---------------------------------------------------------


@pytest.fixture
def aceptada_en_resguardo(curso, educadora, nino, nucleos, oa_ia, semestre, hoy):
    """El peor caso: una observación aceptada que quedó en una captura en resguardo."""
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original=NOTA,
                                     estado=Captura.Estado.EN_RESGUARDO)
    obs = Observacion.todas.create(captura=captura, nino=nino, fecha=hoy, cita=NOTA, estado=Observacion.Estado.ACEPTADA)
    obs.nucleos.set([nucleos[0]])
    obs.oas.set([oa_ia])
    pendiente = Observacion.todas.create(captura=captura, nino=nino, fecha=hoy, cita=NOTA)
    pendiente.nucleos.set([nucleos[0]])
    return obs


def test_no_aparece_en_las_consultas_de_observaciones(aceptada_en_resguardo, nino):
    assert not Observacion.objects.filter(pk=aceptada_en_resguardo.pk).exists()
    assert not nino.observaciones.exists()


def test_no_cuenta_en_la_cobertura(aceptada_en_resguardo, nino):
    assert all(c.cantidad == 0 for c in cobertura_del_nino(nino)["IA"])


def test_no_cuenta_en_las_alertas_de_datos(aceptada_en_resguardo, curso, hoy):
    fila, = tabla_del_curso(curso, hoy=hoy).filas
    assert fila.celdas[0].datos == EstadoDatos.SIN_DATOS


def test_no_aparece_en_la_ficha(aceptada_en_resguardo, nino, educadora, hoy):
    ficha = armar_ficha(nino, educadora, hoy=hoy)
    assert ficha.nucleo("IA").observaciones == []


def test_no_aparece_en_la_revision(aceptada_en_resguardo, curso, educadora):
    assert revision_del_curso(curso).grupos == [] and contar_pendientes(educadora) == 0


def test_no_entra_en_la_propuesta_de_nivel(aceptada_en_resguardo, nino, nucleos, rubrica):
    assert preparar_evidencia(nino, nucleos[0]).datos["evidencia"] == []


# --- Medición (Task 10) ------------------------------------------------------------------


def test_evaluar_proteccion_cuenta_positivas_y_negativas(capsys):
    from django.core.management import call_command

    from registro.management.commands.evaluar import RUTA_SET_PROTECCION, _leer

    notas = _leer(RUTA_SET_PROTECCION)["notas"]
    assert len(notas) == 6 and sum(n["marcar"] for n in notas) == 4
    # Marca todo: las 4 positivas bien y las 2 negativas por error.
    cliente = ClienteFalso(*[MARCADA] * len(notas))
    call_command("evaluar", "--proteccion", crear_cliente=lambda modelo: cliente)
    salida = capsys.readouterr().out
    assert "positivas marcadas 4/4" in salida and "negativas marcadas por error 2/2" in salida
    assert "moretones" not in salida  # no escribe el texto de las notas
