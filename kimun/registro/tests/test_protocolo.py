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
                                       {"pasos": [{"titulo": "Informar"}], "destinatarios": ["asistente"]}])
def test_un_protocolo_que_no_sirve_usa_los_pasos_minimos(monkeypatch, tmp_path, caplog, contenido):
    _con_protocolo(monkeypatch, tmp_path, contenido)
    with caplog.at_level(logging.ERROR):
        assert leer_protocolo() is PROTOCOLO_MINIMO
    assert "pasos mínimos" in caplog.text


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
