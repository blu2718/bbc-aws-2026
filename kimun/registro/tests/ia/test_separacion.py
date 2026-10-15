"""Separación de notas en observaciones, con un cliente falso en vez de Bedrock."""

import logging
from datetime import date, datetime, timezone

import pytest

from registro.ia import ErrorBedrock, ErrorSeparacion, separar
from registro.ia import separacion
from registro.ia.separacion import (
    ESCALA_APOYO,
    ESCALA_EFECTO,
    construir_herramienta,
    construir_prompt,
    indexar_catalogo,
    normalizar_codigo_oa,
)

CAMPOS = ["nombre_detectado", "fecha", "cita_literal", "interpretacion", "nucleos", "oas", "apoyo", "efecto", "grupal"]


def _separar(respuesta, catalogo, cliente_falso, fecha="2026-05-25", nombres=("Pedro Salinas",), texto="nota"):
    cliente = cliente_falso(respuesta)
    return separar(texto, fecha, list(nombres), catalogo, cliente=cliente), cliente


def test_json_valido_produce_observaciones_normalizadas(catalogo, cliente_falso, obs):
    respuesta = {"observaciones": [obs(nombre_detectado=" Pedro ", interpretacion="Se nota más seguro", efecto="avance")]}
    resultado, cliente = _separar(respuesta, catalogo, cliente_falso)
    assert resultado == [
        {
            "nombre_detectado": "Pedro",
            "fecha": "2026-05-25",
            "cita_literal": "Pedro clasificó las hojas por tamaño",
            "interpretacion": "Se nota más seguro",
            "nucleos": ["PM"],
            "oas": ["OA 2 PM"],
            "apoyo": "autonomo",
            "efecto": "avance",
            "grupal": False,
        }
    ]
    assert list(resultado[0]) == CAMPOS
    assert len(cliente.llamadas) == 1
    assert "<nota>\nnota\n</nota>" in cliente.llamadas[0]["mensaje"]


def test_texto_vacio_no_llama_al_modelo(catalogo, cliente_falso):
    cliente = cliente_falso()
    assert separar("   \n", date(2026, 5, 25), [], catalogo, cliente=cliente) == []
    assert separar("", date(2026, 5, 25), [], catalogo, cliente=cliente) == []
    assert cliente.llamadas == []


def test_acepta_respuesta_serializada_como_texto(catalogo, cliente_falso):
    respuesta = '{"observaciones": "[{\\"nombre_detectado\\": \\"Pedro\\", \\"cita_literal\\": \\"contó hasta 10\\"}]"}'
    resultado, _ = _separar(respuesta, catalogo, cliente_falso)
    assert [o["nombre_detectado"] for o in resultado] == ["Pedro"]


@pytest.mark.parametrize(
    "respuesta",
    [
        "esto no es JSON {",
        None,
        ["observaciones"],
        {"otra_cosa": []},
        {"observaciones": {"nombre_detectado": "Pedro"}},
        {"observaciones": "[no es json"},
    ],
)
def test_respuesta_invalida_lanza_error_separacion(respuesta, catalogo, cliente_falso):
    with pytest.raises(ErrorSeparacion):
        _separar(respuesta, catalogo, cliente_falso)


def test_error_del_cliente_sin_tool_use_se_convierte_en_error_separacion(catalogo, cliente_falso):
    with pytest.raises(ErrorSeparacion, match="herramienta"):
        _separar(ErrorBedrock("La respuesta no trae el uso de la herramienta"), catalogo, cliente_falso)


def test_lista_vacia_es_valida(catalogo, cliente_falso):
    assert _separar({"observaciones": []}, catalogo, cliente_falso)[0] == []


def test_observacion_incompleta_se_descarta_y_sigue_el_resto(catalogo, cliente_falso, obs, caplog):
    respuesta = {"observaciones": [obs(cita_literal=None), "basura", obs(nombre_detectado="Emilio")]}
    with caplog.at_level(logging.WARNING, logger="registro.ia.separacion"):
        resultado, _ = _separar(respuesta, catalogo, cliente_falso)
    assert [o["nombre_detectado"] for o in resultado] == ["Emilio"]
    assert "cita_literal" in caplog.text


def test_oa_y_nucleo_inexistentes_se_descartan_con_log(catalogo, cliente_falso, obs, caplog):
    respuesta = {"observaciones": [obs(nucleos=["PM", "XX"], oas=["OA 2 PM", "OA 99 PM", "OA 1 ZZ", "hojas"])]}
    with caplog.at_level(logging.WARNING, logger="registro.ia.separacion"):
        resultado, _ = _separar(respuesta, catalogo, cliente_falso)
    assert resultado[0]["nucleos"] == ["PM"]
    assert resultado[0]["oas"] == ["OA 2 PM"]
    for descartado in ("XX", "OA 99 PM", "OA 1 ZZ", "hojas"):
        assert descartado in caplog.text


@pytest.mark.parametrize("codigo", ["OA 4 LV", "OA4 LV", "oa 4 lv", "OA 04 LV", "  OA  4  LV ", "OA-4-LV", "OA4LV"])
def test_normaliza_codigo_de_oa(codigo):
    assert normalizar_codigo_oa(codigo) == "OA 4 LV"


@pytest.mark.parametrize("codigo", ["", "LV 4", "OA LV", "cuatro", None, 4])
def test_codigo_sin_forma_de_oa_da_none(codigo):
    assert normalizar_codigo_oa(codigo) is None


def test_oa_con_formato_distinto_se_acepta_normalizado(catalogo, cliente_falso, obs):
    respuesta = {"observaciones": [obs(nucleos=["lv"], oas=["oa 04 lv", "OA4 LV"])]}
    resultado, _ = _separar(respuesta, catalogo, cliente_falso)
    assert resultado[0]["oas"] == ["OA 4 LV"]
    assert resultado[0]["nucleos"] == ["LV"]


def test_oa_valido_agrega_su_nucleo(catalogo, cliente_falso, obs):
    respuesta = {"observaciones": [obs(nucleos=["PM"], oas=["OA 2 PM", "OA 7 CM"])]}
    resultado, _ = _separar(respuesta, catalogo, cliente_falso)
    assert resultado[0]["nucleos"] == ["PM", "CM"]


def test_nota_de_3_ninos_da_3_observaciones(catalogo, cliente_falso, obs):
    respuesta = {
        "observaciones": [
            obs(nombre_detectado="Pedro", cita_literal="Pedro las ordenó por tamaño"),
            obs(nombre_detectado="Emilio", cita_literal="Emilio por color y tamaño"),
            obs(nombre_detectado="Rubi", cita_literal="la Rubi necesitó que le mostrara", apoyo="con_ayuda"),
        ]
    }
    resultado, _ = _separar(respuesta, catalogo, cliente_falso)
    assert [o["nombre_detectado"] for o in resultado] == ["Pedro", "Emilio", "Rubi"]
    assert [o["apoyo"] for o in resultado] == ["autonomo", "autonomo", "con_ayuda"]


def test_nombre_detectado_queda_tal_como_viene(catalogo, cliente_falso, obs, nombres_curso):
    respuesta = {"observaciones": [obs(nombre_detectado="Nayara"), obs(nombre_detectado="Sofía"), obs(nombre_detectado="Abel")]}
    resultado, _ = _separar(respuesta, catalogo, cliente_falso, nombres=nombres_curso)
    assert [o["nombre_detectado"] for o in resultado] == ["Nayara", "Sofía", "Abel"]


def test_nota_grupal_queda_como_contexto(catalogo, cliente_falso, obs):
    respuesta = {
        "observaciones": [
            obs(nombre_detectado="el curso", cita_literal="hoy bajó la asistencia", nucleos=["IA"], oas=["OA 9 IA"],
                apoyo="autonomo", grupal=True)
        ]
    }
    resultado, _ = _separar(respuesta, catalogo, cliente_falso)
    assert resultado == [
        {
            "nombre_detectado": None,
            "fecha": "2026-05-25",
            "cita_literal": "hoy bajó la asistencia",
            "interpretacion": None,
            "nucleos": ["IA"],
            "oas": [],
            "apoyo": "sin_dato",
            "efecto": "sin_dato",
            "grupal": True,
        }
    ]


@pytest.mark.parametrize(
    "fecha, esperada",
    [
        ("2026-05-20", "2026-05-20"),
        ("2026-05-26", "2026-05-25"),
        ("25-mayo", "2026-05-25"),
        ("2026-02-30", "2026-05-25"),
        ("", "2026-05-25"),
        (None, "2026-05-25"),
    ],
)
def test_fecha_invalida_futura_o_ausente_usa_la_de_captura(fecha, esperada, catalogo, cliente_falso, obs):
    resultado, _ = _separar({"observaciones": [obs(fecha=fecha)]}, catalogo, cliente_falso, fecha=date(2026, 5, 25))
    assert resultado[0]["fecha"] == esperada


@pytest.mark.parametrize("fecha, esperada", [("2026-05-20", "2026-05-20"), ("2026-05-26", "2026-05-25"), (None, "2026-05-25")])
def test_fecha_captura_como_datetime_usa_solo_la_fecha(fecha, esperada, catalogo, cliente_falso, obs):
    # Captura.creada es un DateTimeField: el backend puede pasar un datetime con zona.
    creada = datetime(2026, 5, 25, 23, 30, tzinfo=timezone.utc)
    resultado, cliente = _separar({"observaciones": [obs(fecha=fecha)]}, catalogo, cliente_falso, fecha=creada)
    assert resultado[0]["fecha"] == esperada
    assert "Fecha de captura: 2026-05-25\n" in cliente.llamadas[0]["system"]


def test_fecha_ausente_del_todo_usa_la_de_captura(catalogo, cliente_falso, obs):
    cruda = obs()
    del cruda["fecha"]
    resultado, _ = _separar({"observaciones": [cruda]}, catalogo, cliente_falso, fecha="2026-04-21")
    assert resultado[0]["fecha"] == "2026-04-21"


@pytest.mark.parametrize(
    "apoyo, esperado",
    [("solo", "sin_dato"), (None, "sin_dato"), (3, "sin_dato"), ("con ayuda", "con_ayuda"), ("Autónomo", "autonomo")],
)
def test_apoyo_fuera_de_escala_queda_sin_dato(apoyo, esperado, catalogo, cliente_falso, obs):
    resultado, _ = _separar({"observaciones": [obs(apoyo=apoyo)]}, catalogo, cliente_falso)
    assert resultado[0]["apoyo"] == esperado


def test_catalogo_con_10_nucleos_funciona_sin_cambios(catalogo_10_nucleos, cliente_falso, obs):
    respuesta = {"observaciones": [obs(nucleos=["N10"], oas=["OA 2 N10", "OA 1 N3", "OA 2 PM"])]}
    resultado, cliente = _separar(respuesta, catalogo_10_nucleos, cliente_falso)
    assert resultado[0]["nucleos"] == ["N10", "N3"]
    assert resultado[0]["oas"] == ["OA 2 N10", "OA 1 N3"]
    llamada = cliente.llamadas[0]
    esquema = llamada["herramienta"]["inputSchema"]["json"]
    siglas = esquema["properties"]["observaciones"]["items"]["properties"]["nucleos"]["items"]["enum"]
    assert siglas == [f"N{i}" for i in range(1, 11)]
    assert "OA 2 N10: Objetivo 2 del núcleo 10" in llamada["system"]
    assert "se ignora" not in llamada["system"]


def test_oa_con_codigo_de_otro_formato_se_valida_por_su_codigo_literal(cliente_falso, obs, caplog):
    catalogo = {
        "nucleos": [
            {"sigla": "E-EN", "nombre": "Exploración", "oas": [{"numero": 1, "codigo": "OA 1 E-EN", "texto": "Explorar"}]},
            {"sigla": "IA", "nombre": "Identidad", "oas": [{"numero": 1, "codigo": "IA-OA1", "texto": "Reconocerse"}]},
        ]
    }
    respuesta = {"observaciones": [obs(nucleos=[], oas=["oa 1 e-en", "IA-OA1", "IA-OA9"])]}
    with caplog.at_level(logging.INFO, logger="registro.ia.separacion"):
        resultado, cliente = _separar(respuesta, catalogo, cliente_falso)
    assert resultado[0]["oas"] == ["OA 1 E-EN", "IA-OA1"]
    assert resultado[0]["nucleos"] == ["E-EN", "IA"]
    assert "- OA 1 E-EN: Explorar" in cliente.llamadas[0]["system"]
    assert "- IA-OA1: Reconocerse" in cliente.llamadas[0]["system"]
    assert "IA-OA9" in caplog.text
    assert "código literal" in caplog.text


@pytest.fixture
def catalogo_codigos_repetidos():
    """Dos núcleos que usan el mismo código "OA 1"; "OA 2" solo existe en LV."""
    return {
        "nucleos": [
            {"sigla": "IA", "nombre": "Identidad", "oas": [{"numero": 1, "codigo": "OA 1", "texto": "Reconocer emociones"}]},
            {
                "sigla": "LV",
                "nombre": "Lenguaje",
                "oas": [
                    {"numero": 1, "codigo": "OA 1", "texto": "Expresarse oralmente"},
                    {"numero": 2, "codigo": "OA 2", "texto": "Comprender textos"},
                ],
            },
        ]
    }


def test_codigo_repetido_en_dos_nucleos_queda_indexado_en_cada_uno(catalogo_codigos_repetidos):
    _, oas = indexar_catalogo(catalogo_codigos_repetidos)
    assert oas[("IA", "OA 1")] == ("OA 1 IA", "IA")
    assert oas[("LV", "OA 1")] == ("OA 1 LV", "LV")
    assert oas[("LV", "OA 2")] == ("OA 2", "LV")


def test_codigo_repetido_en_dos_nucleos_cada_oa_queda_en_su_nucleo(catalogo_codigos_repetidos, cliente_falso, obs, caplog):
    respuesta = {
        "observaciones": [
            obs(nucleos=[], oas=["OA 1 IA"]),
            obs(nucleos=[], oas=["OA 1 LV"]),
            obs(nucleos=["LV"], oas=["OA 1"]),
            obs(nucleos=["IA"], oas=["oa 1"]),
            obs(nucleos=[], oas=["OA 1 IA", "OA 1 LV"]),
            obs(nucleos=[], oas=["OA 2"]),
            obs(nucleos=[], oas=["OA 1"]),
        ]
    }
    with caplog.at_level(logging.WARNING, logger="registro.ia.separacion"):
        resultado, cliente = _separar(respuesta, catalogo_codigos_repetidos, cliente_falso)
    asignados = [(r["oas"], r["nucleos"]) for r in resultado]
    assert asignados == [
        (["OA 1 IA"], ["IA"]),
        (["OA 1 LV"], ["LV"]),
        (["OA 1 LV"], ["LV"]),
        (["OA 1 IA"], ["IA"]),
        (["OA 1 IA", "OA 1 LV"], ["IA", "LV"]),
        (["OA 2"], ["LV"]),
        # "OA 1" sin sigla ni núcleo en la observación: no se puede saber cuál es.
        ([], []),
    ]
    assert "varios núcleos" in caplog.text
    # El modelo ve los códigos repetidos con su sigla, para que los devuelva sin ambigüedad.
    system = cliente.llamadas[0]["system"]
    assert "- OA 1 IA: Reconocer emociones" in system
    assert "- OA 1 LV: Expresarse oralmente" in system
    assert "- OA 2: Comprender textos" in system


def test_prompt_no_trae_los_casos_del_set_de_evaluacion(catalogo, nombres_curso):
    prompt = construir_prompt(date(2026, 5, 25), [], catalogo)
    for frase in ("Nayara", "Sofía", "25-mayo", "20/04", "20-04", "asistencia", "creo que"):
        assert frase not in prompt


def test_prompt_incluye_todos_los_oa_y_no_las_conductas(catalogo, nombres_curso):
    prompt = construir_prompt(date(2026, 5, 25), nombres_curso, catalogo)
    for nucleo in catalogo["nucleos"]:
        assert f"- {nucleo['sigla']}: {nucleo['nombre']}" in prompt
        for oa in nucleo["oas"]:
            assert f"- {oa['codigo']}: {oa['texto']}" in prompt
            for conducta in oa["conductas"]["NT1"] + oa["conductas"]["NT2"]:
                assert conducta not in prompt
    assert "2026-05-25" in prompt
    assert "  - Naiara Fuentes" in prompt
    assert "{{" not in prompt


def test_herramienta_usa_la_escala_de_apoyo_y_las_siglas_del_catalogo(catalogo):
    herramienta = construir_herramienta(catalogo)
    items = herramienta["inputSchema"]["json"]["properties"]["observaciones"]["items"]
    assert herramienta["name"] == "registrar_observaciones"
    assert items["properties"]["apoyo"]["enum"] == list(ESCALA_APOYO)
    assert items["properties"]["nucleos"]["items"]["enum"] == [n["sigla"] for n in catalogo["nucleos"]]
    assert "enum" not in items["properties"]["oas"]["items"]


def test_sin_cliente_usa_cliente_bedrock(catalogo, cliente_falso, obs, monkeypatch):
    falso = cliente_falso({"observaciones": [obs()]})
    monkeypatch.setattr(separacion, "ClienteBedrock", lambda: falso)
    assert len(separar("Pedro clasificó hojas", "2026-05-25", [], catalogo)) == 1
    assert len(falso.llamadas) == 1


# --- Efecto del suceso en sus OA (pantalla II de diseno-interfaz.jpg) ---------------------------


@pytest.mark.parametrize("valor, esperado", [
    ("avance", "avance"),
    ("Por reforzar", "por_reforzar"),
    ("negativo", "sin_dato"),
    (None, "sin_dato"),
])
def test_el_efecto_fuera_de_la_escala_queda_sin_dato(catalogo, cliente_falso, obs, valor, esperado):
    resultado, _ = _separar({"observaciones": [obs(efecto=valor)]}, catalogo, cliente_falso)
    assert resultado[0]["efecto"] == esperado


def test_la_herramienta_pide_el_efecto_con_su_escala(catalogo):
    items = construir_herramienta(catalogo)["inputSchema"]["json"]["properties"]["observaciones"]["items"]
    assert items["properties"]["efecto"]["enum"] == list(ESCALA_EFECTO)
    assert "efecto" in items["required"]
