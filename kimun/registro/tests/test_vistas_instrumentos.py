"""Pantallas de instrumentos y correcciones con historial (Task 14): permisos, flujos y ficha."""
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from registro.historial import entradas, verificar
from registro.instrumentos import cargar_instrumentos, leer_instrumentos
from registro.models import Captura, Instrumento, Observacion, RegistroCambio, ResultadoInstrumento
from registro.resultados import ultimo_cambio_id

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.STORAGES = {**settings.STORAGES, "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}


@pytest.fixture
def catalogo(db):
    cargar_instrumentos(leer_instrumentos())


@pytest.fixture
def con_nacimiento(nino):
    nino.fecha_nacimiento = date(2020, 5, 14)
    nino.save()
    return nino


def _manual(client, nino, codigo="TEPSI", **extra):
    datos = {"fecha_aplicacion": "2023-06-12", "origen": "salud", "aplicado_por": "CESFAM",
             "campo__T": "35", "area__C__PB": "10", "area__C__T": "45", "area__L__PB": "8", "area__L__T": "28",
             "area__M__PB": "6", "area__M__T": "41", **extra}
    return client.post(reverse("instrumento_manual", args=[nino.pk, codigo]), datos)


@pytest.fixture
def confirmado(client, educadora, catalogo, con_nacimiento):
    client.force_login(educadora)
    respuesta = _manual(client, con_nacimiento)
    assert respuesta.status_code == 302
    client.logout()
    return ResultadoInstrumento.objects.get()


# --- Permisos ---------------------------------------------------------------------------


def test_asistente_no_ve_instrumentos_ni_en_la_ficha(client, asistente_del_curso, confirmado, nino):
    client.force_login(asistente_del_curso)
    ficha = client.get(reverse("ficha", args=[nino.pk]))
    assert ficha.status_code == 200 and "Evaluaciones estandarizadas" not in ficha.content.decode()
    assert client.get(reverse("resultado_instrumento", args=[confirmado.pk])).status_code == 404
    assert client.get(reverse("instrumento_nuevo", args=[nino.pk])).status_code == 404


def test_directora_ve_pero_no_edita(client, directora_del_jardin, confirmado, nino):
    client.force_login(directora_del_jardin)
    ficha = client.get(reverse("ficha", args=[nino.pk])).content.decode()
    assert "Evaluaciones estandarizadas" in ficha and "Agregar el resultado" not in ficha
    pagina = client.get(reverse("resultado_instrumento", args=[confirmado.pk]))
    assert pagina.status_code == 200 and "Corregir" not in pagina.content.decode()
    assert client.get(reverse("resultado_instrumento_editar", args=[confirmado.pk])).status_code == 404
    assert client.post(reverse("resultado_instrumento_descartar", args=[confirmado.pk]), {"motivo": "x"}).status_code == 404


def test_otra_educadora_recibe_404(client, otra_educadora, confirmado):
    client.force_login(otra_educadora)
    assert client.get(reverse("resultado_instrumento", args=[confirmado.pk])).status_code == 404


# --- Flujos de la educadora ---------------------------------------------------------------


def test_ingreso_manual_calcula_confirma_y_queda_en_la_ficha(client, educadora, confirmado, nino):
    assert confirmado.estado == ResultadoInstrumento.Estado.CONFIRMADO
    assert confirmado.valores["campos"]["PB"] == 24 and confirmado.valores["categoria"] == "riesgo"
    assert confirmado.valores["categorias_area"]["L"] == "retraso"
    assert [e.accion for e in entradas(RegistroCambio.Objeto.RESULTADO, confirmado.pk)] == ["crear"]
    client.force_login(educadora)
    ficha = client.get(reverse("ficha", args=[nino.pk])).content.decode()
    assert "Test de Desarrollo Psicomotor" in ficha
    assert "Con seguimiento del centro de salud" in ficha        # texto de apoyo, no la etiqueta
    assert "Lenguaje: Con apoyo especializado" in ficha
    pagina = client.get(reverse("resultado_instrumento", args=[confirmado.pk])).content.decode()
    assert "Categoría del instrumento: Riesgo" in pagina and "Historial íntegro" in pagina


def test_manual_rechaza_valores_fuera_de_rango_y_fecha_futura(client, educadora, catalogo, con_nacimiento):
    client.force_login(educadora)
    respuesta = _manual(client, con_nacimiento, campo__T="95", fecha_aplicacion="2099-01-01")
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "fuera del rango" in html and "posterior a hoy" in html
    assert not ResultadoInstrumento.objects.exists()


def test_corregir_un_confirmado_exige_motivo_y_queda_en_el_historial(client, educadora, confirmado):
    client.force_login(educadora)
    url = reverse("resultado_instrumento_editar", args=[confirmado.pk])
    version = ultimo_cambio_id(RegistroCambio.Objeto.RESULTADO, confirmado.pk)
    base = {"fecha_aplicacion": "2023-06-12", "origen": "salud", "aplicado_por": "CESFAM", "campo__T": "42",
            "area__C__PB": "10", "area__C__T": "45", "area__L__PB": "8", "area__L__T": "28",
            "area__M__PB": "6", "area__M__T": "41", "version": version, "instrumento": "TEPSI"}
    sin_motivo = client.post(url, base)
    assert sin_motivo.status_code == 200 and "obligatorio" in sin_motivo.content.decode()
    assert client.post(url, {**base, "motivo": "El T total era 42"}).status_code == 302
    confirmado.refresh_from_db()
    assert confirmado.valores["campos"]["T"] == 42
    ultima = entradas(RegistroCambio.Objeto.RESULTADO, confirmado.pk).last()
    assert ultima.accion == "editar" and ultima.motivo == "El T total era 42"
    assert ultima.antes["valores"]["campos"]["T"] == 35
    assert verificar(confirmado).ok
    pagina = client.get(reverse("resultado_instrumento", args=[confirmado.pk])).content.decode()
    assert "El T total era 42" in pagina


def test_dos_ediciones_a_la_vez_no_se_pisan(client, educadora, confirmado):
    client.force_login(educadora)
    url = reverse("resultado_instrumento_editar", args=[confirmado.pk])
    base = {"fecha_aplicacion": "2023-06-12", "origen": "salud", "campo__T": "42", "motivo": "x", "instrumento": "TEPSI",
            "version": ultimo_cambio_id(RegistroCambio.Objeto.RESULTADO, confirmado.pk)}
    assert client.post(url, base).status_code == 302
    segunda = client.post(url, {**base, "campo__T": "50"})          # la misma versión vieja
    assert segunda.status_code == 200 and "mientras editabas" in segunda.content.decode()
    confirmado.refresh_from_db()
    assert confirmado.valores["campos"]["T"] == 42


def test_descartar_exige_motivo_y_lo_saca_de_la_ficha(client, educadora, confirmado, nino):
    client.force_login(educadora)
    url = reverse("resultado_instrumento_descartar", args=[confirmado.pk])
    client.post(url, {"motivo": ""})
    confirmado.refresh_from_db()
    assert confirmado.estado == ResultadoInstrumento.Estado.CONFIRMADO
    client.post(url, {"motivo": "Era la hoja de otro niño"})
    confirmado.refresh_from_db()
    assert confirmado.estado == ResultadoInstrumento.Estado.DESCARTADO
    assert "Test de Desarrollo Psicomotor" not in client.get(reverse("ficha", args=[nino.pk])).content.decode()
    assert entradas(RegistroCambio.Objeto.RESULTADO, confirmado.pk).last().motivo == "Era la hoja de otro niño"


def test_subir_hoja_queda_por_leer_y_la_pagina_consulta_el_estado(client, educadora, catalogo, nino):
    client.force_login(educadora)
    respuesta = client.post(reverse("instrumento_nuevo", args=[nino.pk]), {
        "instrumento": "", "origen": "salud", "hoja": SimpleUploadedFile("pedro-tepsi.jpg", JPEG, "image/jpeg"),
    })
    r = ResultadoInstrumento.objects.get()
    assert respuesta.status_code == 302 and r.estado == ResultadoInstrumento.Estado.POR_LEER
    assert "pedro" not in r.archivo.name and r.archivo.name.startswith("originales/hojas/")
    pagina = client.get(reverse("resultado_instrumento", args=[r.pk])).content.decode()
    assert "Leyendo la hoja" in pagina
    estado = client.get(reverse("resultado_instrumento_estado", args=[r.pk]), HTTP_HX_REQUEST="true")
    assert estado.status_code == 200 and "HX-Refresh" not in estado


def test_subir_algo_que_no_es_foto_ni_pdf_se_rechaza(client, educadora, catalogo, nino):
    client.force_login(educadora)
    respuesta = client.post(reverse("instrumento_nuevo", args=[nino.pk]), {
        "origen": "salud", "hoja": SimpleUploadedFile("hoja.txt", b"hola", "text/plain"),
    })
    assert respuesta.status_code == 200 and not ResultadoInstrumento.objects.exists()


def test_revisar_y_confirmar_lo_leido_y_cambiar_de_instrumento(client, educadora, catalogo, con_nacimiento):
    r = ResultadoInstrumento.objects.create(
        nino=con_nacimiento, instrumento=Instrumento.objects.get(codigo="OTRO"), estado=ResultadoInstrumento.Estado.POR_REVISAR,
        registrado_por=educadora, valores={"campos": {"nombre_instrumento": "Pauta"}},
    )
    client.force_login(educadora)
    url = reverse("resultado_instrumento_editar", args=[r.pk])
    assert "Coeficiente de desarrollo" in client.get(url, {"instrumento": "EEDP"}).content.decode()
    respuesta = client.post(url, {"instrumento": "EEDP", "fecha_aplicacion": "2021-01-14", "origen": "salud",
                                  "campo__CD": "92", "version": 0, "confirmar": "1"})
    assert respuesta.status_code == 302
    r.refresh_from_db()
    assert r.instrumento.codigo == "EEDP" and r.estado == "confirmado" and r.valores["categoria"] == "normal"
    assert r.confirmado_por == educadora
    assert entradas(RegistroCambio.Objeto.RESULTADO, r.pk).last().accion == "confirmar"


# --- Correcciones de observaciones aceptadas -----------------------------------------------


@pytest.fixture
def aceptada(curso, educadora, nino, nucleos):
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo="texto", texto_original="Pedro ordenó")
    obs = Observacion.objects.create(captura=captura, nino=nino, fecha=date(2026, 5, 4), cita="ordenó los bloques",
                                     estado=Observacion.Estado.ACEPTADA)
    obs.nucleos.set([nucleos[0]])
    return obs


def _datos_obs(obs, **cambios):
    p = f"obs{obs.pk}-"
    datos = {f"{p}nino": obs.nino_id, f"{p}fecha": "2026-05-04", f"{p}cita": obs.cita, f"{p}interpretacion": "",
             f"{p}nucleos": [n.pk for n in obs.nucleos.all()], f"{p}apoyo": "sin_dato", f"{p}efecto": "sin_dato",
             f"{p}version": ultimo_cambio_id(RegistroCambio.Objeto.OBSERVACION, obs.pk)}
    datos.update({f"{p}{k}": v for k, v in cambios.items()})
    return datos


def test_corregir_una_observacion_aceptada_con_motivo(client, educadora, aceptada, nino):
    client.force_login(educadora)
    url = reverse("observacion_corregir", args=[aceptada.pk])
    assert client.post(url, _datos_obs(aceptada, cita="ordenó los bloques por color")).status_code == 200  # falta motivo
    assert client.post(url, _datos_obs(aceptada, cita="ordenó los bloques por color", motivo="Faltaba el criterio")).status_code == 302
    aceptada.refresh_from_db()
    assert aceptada.cita == "ordenó los bloques por color" and aceptada.estado == "aceptada"
    entrada = entradas(RegistroCambio.Objeto.OBSERVACION, aceptada.pk).get()
    assert entrada.antes["cita"] == "ordenó los bloques" and entrada.motivo == "Faltaba el criterio"
    # El suceso es de mayo: queda fuera de la última semana y se ve en el historial completo.
    ficha = client.get(reverse("ficha", args=[nino.pk]), {"historial": "todo"}).content.decode()
    assert reverse("observacion_historial", args=[aceptada.pk]) in ficha
    historial = client.get(reverse("observacion_historial", args=[aceptada.pk])).content.decode()
    assert "Faltaba el criterio" in historial and "Historial íntegro" in historial


def test_retirar_una_observacion_aceptada(client, educadora, aceptada, nino):
    client.force_login(educadora)
    client.post(reverse("observacion_retirar", args=[aceptada.pk]), {"motivo": "Era de Emilio"})
    aceptada.refresh_from_db()
    assert aceptada.estado == Observacion.Estado.DESCARTADA
    assert entradas(RegistroCambio.Objeto.OBSERVACION, aceptada.pk).get().accion == "descartar"


def test_solo_la_educadora_corrige_observaciones(client, asistente_del_curso, directora_del_jardin, aceptada):
    for usuaria in (asistente_del_curso, directora_del_jardin):
        client.force_login(usuaria)
        assert client.get(reverse("observacion_corregir", args=[aceptada.pk])).status_code == 404
        assert client.post(reverse("observacion_retirar", args=[aceptada.pk]), {"motivo": "x"}).status_code == 404
        assert client.get(reverse("observacion_historial", args=[aceptada.pk])).status_code == 200


def test_un_formulario_con_errores_no_da_un_falso_aviso_de_adulteracion(client, educadora, aceptada):
    """`is_valid()` copia los cambios a la instancia: el historial se verifica contra lo guardado."""
    client.force_login(educadora)
    url = reverse("observacion_corregir", args=[aceptada.pk])
    client.post(url, _datos_obs(aceptada, cita="ordenó los bloques por color", motivo="Faltaba el criterio"))
    aceptada.refresh_from_db()
    pagina = client.post(url, _datos_obs(aceptada, cita="otra cita"))  # sin motivo: vuelve con errores
    assert pagina.status_code == 200
    html = pagina.content.decode()
    assert "Historial íntegro" in html and "no calza" not in html


def test_corregir_o_retirar_pide_una_propuesta_nueva(client, educadora, aceptada, descriptores, nino):
    from registro.models import PropuestaNivel

    client.force_login(educadora)
    client.post(reverse("observacion_retirar", args=[aceptada.pk]), {"motivo": "Era de Emilio"})
    assert PropuestaNivel.objects.filter(nino=nino, nucleo__sigla="IA", estado=PropuestaNivel.Estado.SOLICITADA).exists()


def test_un_resultado_que_no_se_pudo_leer_se_puede_descartar_y_borra_la_hoja(
    client, educadora, catalogo, nino, django_capture_on_commit_callbacks,
):
    from django.core.files.base import ContentFile

    r = ResultadoInstrumento(nino=nino, estado=ResultadoInstrumento.Estado.ERROR, registrado_por=educadora,
                             error="No se pudo leer la hoja.")
    r.archivo.save("hoja.jpg", ContentFile(JPEG), save=False)
    r.save()
    nombre = r.archivo.name
    client.force_login(educadora)
    pagina = client.get(reverse("resultado_instrumento", args=[r.pk])).content.decode()
    assert "Descartar este intento y borrar la hoja" in pagina
    with django_capture_on_commit_callbacks(execute=True):
        client.post(reverse("resultado_instrumento_descartar", args=[r.pk]), {"motivo": "La ingresé a mano"})
    r.refresh_from_db()
    assert r.estado == ResultadoInstrumento.Estado.DESCARTADO and not r.archivo
    assert not r.archivo.storage.exists(nombre)
