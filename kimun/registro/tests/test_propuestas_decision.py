"""Decisiones de la educadora: vigencia, historial e interfaz de la Task 7."""
from datetime import date
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from registro.models import NivelValidado, Observacion, PropuestaNivel
from registro.propuestas import registrar_entrada, resolver_propuesta


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def lista(nino, nucleos, descriptores, observar_en):
    obs = observar_en(nino, date(2026, 4, 1), [nucleos[0]], cita="Pedro eligió su ropa.")
    propuesta = PropuestaNivel.objects.create(nino=nino, nucleo=nucleos[0])
    registrar_entrada(propuesta)
    propuesta.estado, propuesta.nivel, propuesta.evidencia_suficiente = "lista", 3, True
    propuesta.justificacion = "Avanza en autonomía."
    propuesta.conductas_observadas = ["Elige su ropa"]
    propuesta.save()
    propuesta.observaciones_citadas.add(obs)
    return propuesta


def test_aceptar_es_atomico_idempotente_y_registra_usuaria_y_fecha(lista, educadora):
    antes = NivelValidado.objects.count()
    primera = resolver_propuesta(lista, educadora, accion="aceptar")
    segunda = resolver_propuesta(lista, educadora, accion="aceptar")
    lista.refresh_from_db()
    assert primera.realizada and not segunda.realizada
    assert primera.validacion.pk == segunda.validacion.pk
    assert lista.estado == "aceptada" and lista.resuelta_por == educadora and lista.resuelta_en
    nv = primera.validacion
    assert (nv.nivel, nv.validado_por, nv.fecha, nv.propuesta_id) == (3, educadora, timezone.localdate(), lista.pk)
    assert NivelValidado.objects.count() == antes + 1


def test_fijar_otro_nivel_conserva_la_sugerencia_original(lista, educadora):
    resultado = resolver_propuesta(lista, educadora, accion="ajustar", nivel=4, comentario="Observé mayor autonomía.")
    lista.refresh_from_db()
    assert lista.estado == "ajustada" and lista.nivel == 3
    assert resultado.validacion.nivel == 4 and resultado.validacion.propuesta == lista
    assert resultado.validacion.comentario == "Observé mayor autonomía."
    assert not resolver_propuesta(lista, educadora, accion="ajustar", nivel=4).realizada
    with pytest.raises(ValidationError):
        resolver_propuesta(lista, educadora, accion="ajustar", nivel=5)


def test_rechazar_no_crea_nivel_y_no_permite_otra_decision(lista, educadora):
    antes = NivelValidado.objects.count()
    assert resolver_propuesta(lista, educadora, accion="rechazar").validacion is None
    assert not resolver_propuesta(lista, educadora, accion="rechazar").realizada
    lista.refresh_from_db()
    assert lista.estado == "rechazada" and lista.resuelta_por == educadora
    with pytest.raises(ValidationError):
        resolver_propuesta(lista, educadora, accion="aceptar")
    assert NivelValidado.objects.count() == antes


@pytest.mark.parametrize("accion", ["aceptar", "ajustar"])
def test_no_valida_evidencia_insuficiente(lista, educadora, accion):
    PropuestaNivel.objects.filter(pk=lista.pk).update(nivel=None, evidencia_suficiente=False)
    with pytest.raises(ValidationError):
        resolver_propuesta(lista, educadora, accion=accion, nivel=4)
    assert not NivelValidado.objects.filter(propuesta=lista).exists()


@pytest.mark.parametrize("cambio", ["evidencia", "nivel", "rubrica", "citas"])
def test_datos_desactualizados_quedan_obsoletos_y_no_crean_nivel(lista, educadora, cambio):
    if cambio == "evidencia":
        Observacion.objects.filter(pk=lista.observaciones_citadas.first().pk).update(cita="Otra conducta")
    elif cambio == "nivel":
        NivelValidado.objects.create(nino=lista.nino, nucleo=lista.nucleo, nivel=2, fecha=timezone.localdate())
    elif cambio == "rubrica":
        lista.nucleo.descriptores.filter(nivel=3).update(conducta="Texto actualizado")
    else:
        lista.observaciones_citadas.clear()
    with pytest.raises(ValidationError):
        resolver_propuesta(lista, educadora, accion="aceptar")
    lista.refresh_from_db()
    assert lista.estado == "obsoleta" and not NivelValidado.objects.filter(propuesta=lista).exists()


def test_fallo_al_crear_historial_revierte_la_decision(lista, educadora):
    with patch("registro.propuestas.NivelValidado.objects.create", side_effect=RuntimeError("Fallo simulado")):
        with pytest.raises(RuntimeError):
            resolver_propuesta(lista, educadora, accion="aceptar")
    lista.refresh_from_db()
    assert lista.estado == "lista" and lista.resuelta_por_id is None and lista.resuelta_en is None


def test_la_base_impide_dos_validaciones_de_la_misma_propuesta(lista, educadora):
    nv = resolver_propuesta(lista, educadora, accion="aceptar").validacion
    with pytest.raises(IntegrityError), transaction.atomic():
        NivelValidado.objects.bulk_create([NivelValidado(nino=lista.nino, nucleo=lista.nucleo, nivel=3,
                                                        fecha=nv.fecha, propuesta=lista)])


def test_servicio_impide_decisiones_de_otra_educadora(lista, otra_educadora):
    with pytest.raises(ValidationError):
        resolver_propuesta(lista, otra_educadora, accion="aceptar")


def test_ficha_muestra_nivel_justificacion_conductas_y_enlaces(client, lista, educadora):
    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[lista.nino_id])).content.decode()
    obs = lista.observaciones_citadas.first()
    assert "Nivel propuesto:" in html and "3 · Desarrollando" in html
    assert "Avanza en autonomía." in html and "Elige su ropa" in html
    assert f'href="#observacion-IA-{obs.pk}"' in html and f'id="observacion-IA-{obs.pk}"' in html
    assert "Aceptar propuesta" in html and "Rechazar propuesta" in html and "Fijar otro nivel" in html


def test_aceptar_post_htmx_actualiza_historial_y_tabla(client, lista, educadora):
    client.force_login(educadora)
    url = reverse("aceptar_propuesta", args=[lista.pk])
    assert client.get(url).status_code == 405
    respuesta = client.post(url, {"nivel": 8, "fecha": "2000-01-01", "validado_por": 999}, HTTP_HX_REQUEST="true")
    assert respuesta.status_code == 200 and "<html" not in respuesta.content.decode()
    assert "Propuesta aceptada" in respuesta.content.decode()
    assert lista.nino.nivel_actual(lista.nucleo).nivel == 3
    assert "3 · Desarrollando" in client.get(reverse("curso", args=[lista.nino.curso_id])).content.decode()


def test_sin_htmx_redirige_y_rechaza(client, lista, educadora):
    client.force_login(educadora)
    respuesta = client.post(reverse("rechazar_propuesta", args=[lista.pk]))
    assert respuesta.status_code == 302 and respuesta["Location"].endswith("#nucleo-IA")
    assert "Propuesta rechazada" in client.get(respuesta["Location"]).content.decode()
    assert not NivelValidado.objects.filter(propuesta=lista).exists()


@pytest.mark.parametrize("hx", [False, True])
def test_ajuste_reutiliza_formulario_y_conserva_errores(client, lista, educadora, hx):
    client.force_login(educadora)
    url = reverse("ajustar_propuesta", args=[lista.pk])
    cabeceras = {"HTTP_HX_REQUEST": "true"} if hx else {}
    respuesta = client.post(url, {f"propuesta-{lista.pk}-nivel": "9"}, **cabeceras)
    assert respuesta.status_code == 200 and "Elige un nivel entre 1 y 8." in respuesta.content.decode()
    assert not NivelValidado.objects.filter(propuesta=lista).exists()
    respuesta = client.post(url, {f"propuesta-{lista.pk}-nivel": "4", f"propuesta-{lista.pk}-comentario": "Lo observé."}, **cabeceras)
    assert respuesta.status_code == (200 if hx else 302)
    assert NivelValidado.objects.get(propuesta=lista).nivel == 4


@pytest.mark.parametrize("rol", ["asistente_del_curso", "directora_del_jardin", "otra_educadora"])
@pytest.mark.parametrize("accion", ["aceptar_propuesta", "ajustar_propuesta", "rechazar_propuesta"])
def test_solo_la_educadora_puede_decidir(client, request, lista, rol, accion):
    client.force_login(request.getfixturevalue(rol))
    assert client.post(reverse(accion, args=[lista.pk])).status_code == 404


def test_el_nivel_manual_invalida_la_sugerencia(client, lista, educadora):
    client.force_login(educadora)
    respuesta = client.post(reverse("fijar_nivel", args=[lista.nino_id, "IA"]), {"IA-nivel": "4"})
    assert respuesta.status_code == 302
    lista.refresh_from_db()
    assert lista.estado == "obsoleta"
    assert lista.nino.nivel_actual(lista.nucleo).propuesta_id is None


def test_sondeo_solo_mientras_hay_trabajo_y_actualiza_solo_panel(client, lista, educadora):
    client.force_login(educadora)
    PropuestaNivel.objects.filter(pk=lista.pk).update(estado="solicitada")
    url = reverse("estado_propuesta", args=[lista.nino_id, "IA"])
    pendiente = client.get(url, HTTP_HX_REQUEST="true").content.decode()
    assert 'hx-trigger="every 3s"' in pendiente and 'id="propuesta-IA"' in pendiente
    assert '<section id="nucleo-IA"' not in pendiente
    PropuestaNivel.objects.filter(pk=lista.pk).update(estado="lista")
    lista_html = client.get(url, HTTP_HX_REQUEST="true").content.decode()
    assert 'hx-trigger="every 3s"' not in lista_html and "Aceptar propuesta" in lista_html
    assert client.get(url).status_code == 302


@pytest.mark.parametrize("estado", ["solicitada", "procesando", "error", "obsoleta"])
def test_no_decide_una_propuesta_que_no_esta_lista(lista, educadora, estado):
    PropuestaNivel.objects.filter(pk=lista.pk).update(estado=estado, procesamiento_iniciado=timezone.now(), intentos=1)
    with pytest.raises(ValidationError):
        resolver_propuesta(lista, educadora, accion="aceptar")
    assert not NivelValidado.objects.filter(propuesta=lista).exists()


def test_cita_de_otro_nucleo_invalida_la_propuesta(lista, educadora, nucleos, observar_en):
    ajena = observar_en(lista.nino, date(2026, 4, 1), [nucleos[1]])
    lista.observaciones_citadas.add(ajena)
    with pytest.raises(ValidationError):
        resolver_propuesta(lista, educadora, accion="aceptar")
    lista.refresh_from_db()
    assert lista.estado == "obsoleta"


def test_ficha_respeta_procedencia_guardada_y_escapa_textos(client, lista, educadora):
    from registro.ficha import armar_ficha

    PropuestaNivel.objects.filter(pk=lista.pk).update(rubrica_provisoria=True,
        justificacion="<script>alert(1)</script>", conductas_observadas=['<img src=x onerror="alert(1)">'])
    nf = armar_ficha(lista.nino, educadora).nucleo("IA")
    assert nf.provisorio is False and nf.propuesta.rubrica_provisoria is True
    assert nf.texto_propuesto == "3"
    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[lista.nino_id])).content.decode()
    assert "Propuesta basada en una rúbrica provisoria" in html
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html
    assert "<img src=x" not in html and "&lt;img" in html


def test_consultas_de_propuestas_no_crecen_por_nucleo_o_historial(lista, educadora, nucleos):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from registro.ficha import armar_ficha
    from registro.models import Nino

    def consultas():
        nino = Nino.objects.select_related("curso").get(pk=lista.nino_id)
        with CaptureQueriesContext(connection) as contexto:
            armar_ficha(nino, educadora)
        return len(contexto)
    antes = consultas()
    for nucleo in nucleos:
        for _ in range(3):
            PropuestaNivel.objects.create(nino=lista.nino, nucleo=nucleo, estado="error")
    assert consultas() == antes


def test_anclas_son_unicas_cuando_la_observacion_tiene_varios_nucleos(client, lista, educadora, nucleos):
    obs = lista.observaciones_citadas.first()
    obs.nucleos.add(nucleos[1])
    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[lista.nino_id])).content.decode()
    assert html.count(f'id="observacion-IA-{obs.pk}"') == 1
    assert html.count(f'id="observacion-LV-{obs.pk}"') == 1


def test_insuficiente_muestra_motivo_sin_aceptar_ni_ajustar(client, lista, educadora):
    PropuestaNivel.objects.filter(pk=lista.pk).update(nivel=None, evidencia_suficiente=False, justificacion="Falta observar vestuario.")
    client.force_login(educadora)
    html = client.get(reverse("ficha", args=[lista.nino_id])).content.decode()
    assert "Faltan observaciones" in html and "Falta observar vestuario." in html
    assert "Aceptar propuesta</button>" not in html and "Fijar otro nivel</summary>" not in html


def test_ajustar_al_mismo_nivel_pide_elegir_otro(client, lista, educadora):
    client.force_login(educadora)
    respuesta = client.post(reverse("ajustar_propuesta", args=[lista.pk]), {f"propuesta-{lista.pk}-nivel": "3"})
    assert "Elige un nivel diferente" in respuesta.content.decode()
    assert not NivelValidado.objects.filter(propuesta=lista).exists()


def test_ajuste_admite_el_noveno_nivel(client, lista, educadora, rubrica):
    from registro.models import DescriptorNivel

    rubrica.cantidad_niveles = 9
    rubrica.save()
    DescriptorNivel.objects.create(nucleo=lista.nucleo, nivel_educativo=lista.nino.curso.nivel_educativo,
                                    nivel=9, nombre="Nuevo nivel", descripcion="Descripción", conducta="Conducta", provisorio=False)
    lista.estado = "solicitada"
    lista.save()
    registrar_entrada(lista)
    lista.estado = "lista"
    lista.save()
    client.force_login(educadora)
    respuesta = client.post(reverse("ajustar_propuesta", args=[lista.pk]), {f"propuesta-{lista.pk}-nivel": "9"})
    assert respuesta.status_code == 302 and NivelValidado.objects.get(propuesta=lista).nivel == 9


def test_post_obsoleto_conserva_error_y_estado_en_la_respuesta(client, lista, educadora):
    lista.nucleo.descriptores.filter(nivel=3).update(conducta="Rúbrica modificada")
    client.force_login(educadora)
    respuesta = client.post(reverse("aceptar_propuesta", args=[lista.pk]), HTTP_HX_REQUEST="true")
    assert respuesta.status_code == 200 and "desactualizada" in respuesta.content.decode()
    assert "Aceptar propuesta</button>" not in respuesta.content.decode()
    lista.refresh_from_db()
    assert lista.estado == "obsoleta"


def test_acciones_exigen_post_login_y_csrf(lista, educadora):
    from django.test import Client

    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(educadora)
    for accion in ["aceptar_propuesta", "ajustar_propuesta", "rechazar_propuesta"]:
        url = reverse(accion, args=[lista.pk])
        assert cliente.get(url).status_code == 405
        assert cliente.post(url).status_code == 403
    cliente.get(reverse("ficha", args=[lista.nino_id]))
    token = cliente.cookies["csrftoken"].value
    assert cliente.post(reverse("aceptar_propuesta", args=[lista.pk]), HTTP_X_CSRFTOKEN=token).status_code == 302


def test_estado_no_expone_propuestas_a_otros_roles(client, lista, asistente_del_curso):
    client.force_login(asistente_del_curso)
    assert client.get(reverse("estado_propuesta", args=[lista.nino_id, "IA"]), HTTP_HX_REQUEST="true").status_code == 404


def test_flujo_completo_aceptar_observaciones_procesar_y_validar(client, nino, nucleos, descriptores, observar_en, educadora):
    import json
    from registro.propuestas import procesar_siguiente
    from registro.revision import aceptar_todas

    observaciones = [observar_en(nino, date(2026, 4, dia), [nucleos[0]], cita=f"Pedro eligió su ropa, día {dia}.",
                                 estado="pendiente") for dia in (1, 2, 3)]
    assert aceptar_todas(observaciones[0].captura) == (3, 0)
    class ClienteFalso:
        modelo = "falso"
        def invocar_herramienta(self, system, mensaje, herramienta):
            assert "Pedro" not in mensaje
            return {"nivel": 3, "evidencia_suficiente": True,
                    "observaciones_citadas": [o["id"] for o in json.loads(mensaje)["observaciones"]],
                    "conductas_observadas": ["Se viste de forma autónoma"], "justificacion": "Avanza."}
    propuesta = procesar_siguiente(cliente=ClienteFalso())
    assert propuesta.estado == "lista"
    client.force_login(educadora)
    assert client.post(reverse("aceptar_propuesta", args=[propuesta.pk])).status_code == 302
    actual = nino.nivel_actual(nucleos[0])
    assert actual.nivel == 3 and actual.propuesta_id == propuesta.pk
    assert "3 · Desarrollando" in client.get(reverse("curso", args=[nino.curso_id])).content.decode()


@pytest.mark.django_db(transaction=True)
def test_decisiones_concurrentes_no_duplican_el_historial(lista, educadora):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connections, OperationalError

    barrera = Barrier(2)
    def decidir():
        try:
            barrera.wait(timeout=5)
            return resolver_propuesta(lista, educadora, accion="aceptar")
        except OperationalError as error:
            # SQLite en memoria no espera ante SQLITE_LOCKED como la base en disco.
            if "locked" not in str(error).lower():
                raise
            return None
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(lambda _: decidir(), range(2)))
    assert sum(bool(r and r.realizada) for r in resultados) == 1
    assert NivelValidado.objects.filter(propuesta=lista).count() == 1
    assert not resolver_propuesta(lista, educadora, accion="aceptar").realizada


@pytest.mark.django_db(transaction=True)
def test_migracion_no_borra_validaciones_duplicadas(lista):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    anterior = [("registro", "0004_propuesta_procesamiento")]
    nueva = [("registro", "0005_propuesta_decision")]
    executor = MigrationExecutor(connection)
    executor.migrate(anterior)
    Nivel = executor.loader.project_state(anterior).apps.get_model("registro", "NivelValidado")
    creados = Nivel.objects.bulk_create([Nivel(nino_id=lista.nino_id, nucleo_id=lista.nucleo_id,
                                              nivel=3, fecha=date(2026, 4, 1), propuesta_id=lista.pk) for _ in range(2)])
    try:
        with pytest.raises(RuntimeError, match="varias validaciones"):
            MigrationExecutor(connection).migrate(nueva)
        assert Nivel.objects.filter(pk__in=[v.pk for v in creados]).count() == 2
    finally:
        Nivel.objects.filter(pk__in=[v.pk for v in creados]).delete()
        MigrationExecutor(connection).migrate(nueva)
