"""Protocolo de protección como dato (`datos/protocolo_proteccion.json`, Task 13)."""
import json
import logging

import pytest
from django.urls import reverse

from registro import protocolo
from registro.models import AvisoProteccion, Captura
from registro.protocolo import PROTOCOLO_MINIMO, leer_protocolo, validar


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def aviso(curso, asistente_del_curso):
    captura = Captura.objects.create(curso=curso, autora=asistente_del_curso, tipo=Captura.Tipo.TEXTO,
                                     texto_original="Nota de prueba", estado=Captura.Estado.EN_RESGUARDO)
    return AvisoProteccion.objects.create(captura=captura, senal="relato")


def _con_protocolo(monkeypatch, tmp_path, datos):
    ruta = tmp_path / "protocolo.json"
    ruta.write_text(json.dumps(datos) if not isinstance(datos, str) else datos, encoding="utf-8")
    monkeypatch.setattr(protocolo, "RUTA_PROTOCOLO", ruta)


def test_el_protocolo_del_repo_es_valido_y_lo_ven_educadora_y_directora():
    p = leer_protocolo()
    assert p is not PROTOCOLO_MINIMO and len(p.pasos) >= 2
    assert set(p.destinatarios) == {"educadora", "directora"}
    assert any("interrogues" in paso.titulo for paso in p.pasos)


@pytest.mark.parametrize("contenido", ["{no es json", {"pasos": []}, {"pasos": [{"texto": "sin título"}]},
                                       {"pasos": [{"titulo": "Informar"}], "destinatarios": ["asistente"]},
                                       # Tipos raros: antes daban 500 en todas las páginas (context processor).
                                       {"pasos": [{"titulo": None}], "destinatarios": ["directora"]},
                                       {"pasos": 5, "destinatarios": ["directora"]},
                                       {"pasos": [{"titulo": "Informar"}], "destinatarios": 5}])
def test_un_protocolo_que_no_sirve_usa_los_pasos_minimos(monkeypatch, tmp_path, caplog, contenido):
    _con_protocolo(monkeypatch, tmp_path, contenido)
    with caplog.at_level(logging.ERROR):
        assert leer_protocolo() is PROTOCOLO_MINIMO
    assert "pasos mínimos" in caplog.text


def test_validar_tolera_texto_nulo_y_solo_un_false_explicito_lo_deja_definitivo():
    p = validar({"pasos": [{"titulo": "Informar", "texto": None}], "destinatarios": ["directora"], "provisorio": "false"})
    assert p.pasos[0].texto == "" and p.provisorio is True
    assert validar({"pasos": [{"titulo": "Informar"}], "destinatarios": ["directora"], "provisorio": False}).provisorio is False


def test_los_pasos_del_jardin_no_dejan_lineas_vacias_ni_se_comen_numeros():
    assert ProtocoloJardin(pasos="1.\n-\n* \n2. Avisar\n1.5 horas para informar").lista_de_pasos() == [
        "Avisar", "1.5 horas para informar",
    ]
    assert ProtocoloJardin(pasos="1.\n2)").lista_de_pasos() == []


def test_validar_ignora_destinatarios_desconocidos():
    p = validar({"pasos": [{"titulo": "Informar"}], "destinatarios": ["directora", "asistente"]})
    assert p.destinatarios == ("directora",)


def test_la_pagina_del_aviso_muestra_los_pasos_del_archivo(client, monkeypatch, tmp_path, aviso, educadora):
    _con_protocolo(monkeypatch, tmp_path, {
        "provisorio": False, "destinatarios": ["educadora", "directora"],
        "pasos": [{"titulo": "Llama a la encargada de buen trato", "texto": "Al anexo 123."}],
    })
    client.force_login(educadora)
    html = client.get(reverse("aviso", args=[aviso.pk])).content.decode()
    assert "Llama a la encargada de buen trato." in html and "Al anexo 123." in html
    assert "Pasos provisorios" not in html


def test_si_el_protocolo_dice_solo_directora_la_educadora_no_ve_el_aviso(
    client, monkeypatch, tmp_path, aviso, educadora, directora_del_jardin
):
    _con_protocolo(monkeypatch, tmp_path, {"pasos": [{"titulo": "Informar"}], "destinatarios": ["directora"]})
    client.force_login(educadora)
    assert client.get(reverse("aviso", args=[aviso.pk])).status_code == 404
    client.force_login(directora_del_jardin)
    assert client.get(reverse("aviso", args=[aviso.pk])).status_code == 200


# --- Protocolo del jardín, que carga la directora ---------------------------------------

from registro.models import ProtocoloJardin  # noqa: E402

PASOS_JARDIN = "1. Avisar a la directora, Ana Pérez, al anexo 123\n\n- No interrogar al niño\n• Registrar en la ficha de buen trato"


def test_la_directora_carga_el_protocolo_de_su_jardin(client, jardin, directora_del_jardin):
    client.force_login(directora_del_jardin)
    url = reverse("protocolo_jardin", args=[jardin.pk])
    assert "todavía no carga su protocolo" in client.get(url).content.decode()
    respuesta = client.post(url, {"nombre_documento": "Protocolo 2026", "pasos": PASOS_JARDIN}, follow=True)
    assert "Protocolo guardado." in respuesta.content.decode()
    p = ProtocoloJardin.objects.get(jardin=jardin)
    assert p.actualizado_por == directora_del_jardin
    assert p.lista_de_pasos() == ["Avisar a la directora, Ana Pérez, al anexo 123", "No interrogar al niño", "Registrar en la ficha de buen trato"]
    # Se puede actualizar; sigue habiendo uno solo.
    client.post(url, {"nombre_documento": "Protocolo 2027", "pasos": "Un paso"})
    assert ProtocoloJardin.objects.get(jardin=jardin).nombre_documento == "Protocolo 2027"


@pytest.mark.parametrize("quien", ["educadora", "asistente_del_curso", "otra_educadora"])
def test_solo_la_directora_carga_el_protocolo(client, request, jardin, curso, directora_del_jardin, quien):
    client.force_login(request.getfixturevalue(quien))
    url = reverse("protocolo_jardin", args=[jardin.pk])
    assert client.get(url).status_code == 404
    assert client.post(url, {"pasos": "Un paso"}).status_code == 404
    assert not ProtocoloJardin.objects.exists()


@pytest.mark.parametrize("pasos, error", [("  \n \n", "al menos un paso"), ("\n".join(f"Paso {i}" for i in range(21)), "20 pasos")])
def test_el_protocolo_del_jardin_se_valida(client, jardin, directora_del_jardin, pasos, error):
    client.force_login(directora_del_jardin)
    respuesta = client.post(reverse("protocolo_jardin", args=[jardin.pk]), {"pasos": pasos})
    assert respuesta.status_code == 400 and error in respuesta.content.decode()


def test_el_aviso_sigue_el_protocolo_del_jardin_y_deja_los_provisorios_como_referencia(
    client, aviso, jardin, educadora, directora_del_jardin
):
    ProtocoloJardin.objects.create(jardin=jardin, nombre_documento="Protocolo 2026", pasos=PASOS_JARDIN,
                                   actualizado_por=directora_del_jardin)
    client.force_login(educadora)
    html = client.get(reverse("aviso", args=[aviso.pk])).content.decode()
    assert "Según Protocolo 2026" in html and "Avisar a la directora, Ana Pérez, al anexo 123" in html
    assert html.index("Avisar a la directora, Ana Pérez") < html.index("Pasos de referencia (provisorios, JUNJI)")
    assert "el jardín todavía no carga su protocolo" not in html


def test_sin_protocolo_del_jardin_el_aviso_usa_los_provisorios_y_la_directora_ve_como_cargarlo(
    client, aviso, jardin, educadora, directora_del_jardin
):
    client.force_login(educadora)
    html = client.get(reverse("aviso", args=[aviso.pk])).content.decode()
    assert "el jardín todavía no carga su protocolo" in html and "No interrogues al niño o niña" in html
    assert reverse("protocolo_jardin", args=[jardin.pk]) not in html
    client.force_login(directora_del_jardin)
    assert reverse("protocolo_jardin", args=[jardin.pk]) in client.get(reverse("aviso", args=[aviso.pk])).content.decode()


def test_el_resumen_del_jardin_enlaza_al_protocolo(client, jardin, directora_del_jardin):
    client.force_login(directora_del_jardin)
    html = client.get(reverse("jardin", args=[jardin.pk])).content.decode()
    assert reverse("protocolo_jardin", args=[jardin.pk]) in html and "(por cargar)" in html
