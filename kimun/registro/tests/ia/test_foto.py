"""Lectura de fotos (Task 8) con un cliente falso: sin red, sin Django."""

import pytest

from registro.ia import ErrorBedrock, ErrorTranscripcion, ImagenInvalida, transcribir_foto, validar_imagen
from registro.ia.foto import NOMBRE_HERRAMIENTA, TAMANO_MAXIMO, construir_prompt, detectar_formato

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
GIF = b"GIF89a" + b"\x00" * 100
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 100


@pytest.mark.parametrize("contenido, formato", [(JPEG, "jpeg"), (PNG, "png"), (GIF, "gif"), (WEBP, "webp")])
def test_detecta_el_formato_por_la_firma(contenido, formato):
    assert detectar_formato(contenido) == formato
    assert validar_imagen(contenido) == formato


@pytest.mark.parametrize(
    "contenido",
    [
        b"%PDF-1.7 documento",
        b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
        b"\x00\x00\x00\x18ftypheic" + b"\x00" * 20,  # HEIC: Converse no lo acepta
        b"RIFF\x00\x00\x00\x00WAVEfmt ",  # RIFF que no es WebP
        b"texto plano con extension .jpg",
    ],
)
def test_rechaza_archivos_que_no_son_imagenes_aceptadas(contenido):
    assert detectar_formato(contenido) is None
    with pytest.raises(ImagenInvalida, match="JPEG, PNG, GIF o WebP"):
        validar_imagen(contenido)


def test_rechaza_un_archivo_vacio():
    with pytest.raises(ImagenInvalida, match="vacío"):
        validar_imagen(b"")


def test_acepta_hasta_el_tamano_maximo_y_rechaza_un_byte_mas():
    al_limite = JPEG[:4] + b"\x00" * (TAMANO_MAXIMO - 4)
    assert validar_imagen(al_limite) == "jpeg"
    with pytest.raises(ImagenInvalida, match="máximo"):
        validar_imagen(al_limite + b"\x00")


def test_envia_la_foto_y_devuelve_el_texto_sin_espacios_sobrantes(cliente_falso):
    cliente = cliente_falso({"texto": "  25-mayo Nayara armó una torre y la contó hasta el [ilegible]\n"})

    texto = transcribir_foto(JPEG, cliente=cliente)

    assert texto == "25-mayo Nayara armó una torre y la contó hasta el [ilegible]"
    llamada = cliente.llamadas[0]
    assert llamada["imagenes"] == [("jpeg", JPEG)]
    assert llamada["herramienta"]["name"] == NOMBRE_HERRAMIENTA
    assert llamada["herramienta"]["inputSchema"]["json"]["required"] == ["texto"]


def test_el_prompt_pide_ilegible_y_no_corregir_nombres():
    prompt = construir_prompt()
    assert "[ilegible]" in prompt
    assert "Nunca adivines" in prompt
    assert "Nayara" in prompt and "No los cambies" in prompt
    assert "no una instrucción" in prompt


def test_una_foto_sin_texto_devuelve_texto_vacio(cliente_falso):
    assert transcribir_foto(PNG, cliente=cliente_falso({"texto": "   "})) == ""


def test_una_foto_invalida_no_llama_al_modelo(cliente_falso):
    cliente = cliente_falso()
    with pytest.raises(ImagenInvalida):
        transcribir_foto(b"%PDF-1.7", cliente=cliente)
    assert cliente.llamadas == []


@pytest.mark.parametrize("respuesta", [{}, {"texto": None}, {"texto": 3}, "texto suelto", None])
def test_una_respuesta_sin_texto_marca_error(cliente_falso, respuesta):
    with pytest.raises(ErrorTranscripcion, match="texto"):
        transcribir_foto(JPEG, cliente=cliente_falso(respuesta))


def test_un_error_de_bedrock_se_convierte_en_error_de_transcripcion(cliente_falso):
    cliente = cliente_falso(ErrorBedrock("ValidationException: imagen demasiado grande", "ValidationException"))
    with pytest.raises(ErrorTranscripcion, match="ValidationException"):
        transcribir_foto(JPEG, cliente=cliente)


def test_el_set_de_postits_usa_solo_nucleos_y_oas_del_catalogo(catalogo):
    import json
    from pathlib import Path

    ruta = Path(__file__).resolve().parents[4] / "datos" / "eval" / "postits_fotos.json"
    conjunto = json.loads(ruta.read_text(encoding="utf-8"))
    siglas = {n["sigla"] for n in catalogo["nucleos"]}
    codigos = {oa["codigo"] for n in catalogo["nucleos"] for oa in n["oas"]}
    ids = [p["id"] for p in conjunto["postits"]]
    assert len(ids) == len(set(ids)) == 10
    for postit in conjunto["postits"]:
        assert postit["texto"].strip()
        for esperada in postit["esperado"]:
            assert set(esperada["nucleos"]) <= siglas, postit["id"]
            assert set(esperada["oas"]) <= codigos, postit["id"]
