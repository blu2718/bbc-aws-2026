"""Propuestas de nivel: contrato puro, privacidad y cliente falso."""
import copy
import json

import pytest

from registro.ia.bedrock import ErrorBedrock
from registro.ia.propuesta import ErrorConfiguracionPropuesta, ErrorPropuesta, proponer, validar_respuesta


@pytest.fixture
def entrada():
    return {
        "nino": "N-A00001", "nivel_educativo": "transicion",
        "nucleo": {"sigla": "IA", "nombre": "Identidad y Autonomía"},
        "referencia": {"id": 1, "nivel": 1, "fecha": "2026-03-01"},
        "rubrica": [{"cantidad_niveles": 8}],
        "descriptores": [{"nivel": i, "nombre": f"Nombre {i}", "descripcion": f"Descripción {i}",
                           "conducta": f"Conducta {i}", "provisorio": False,
                           "ejemplos": [f"Pedro eligió, ejemplo {i}", f"RESERVADO {i}"]} for i in range(1, 9)],
        "evidencia": [{"id": 20, "fecha": "2026-04-03", "cita": "Pedro se vistió solo con Nayara",
                       "oas": ["OA 1 IA"], "apoyo": "autonomo"},
                      {"id": 10, "fecha": "2026-04-01", "cita": "Pedro se vistió con ayuda",
                       "oas": ["OA 1 IA"], "apoyo": "con_ayuda"}],
        "oas": [{"id": 1, "numero": 1, "texto": "Objetivo"}],
    }


@pytest.fixture
def identidades():
    return [{"nombre": "Pedro Salinas", "codigo": "N-A00001", "alias": ["Pedrito"]},
            {"nombre": "Naiara Fuentes", "codigo": "N-A00002", "alias": ["Nayara"]}]


@pytest.fixture
def respuesta():
    return {"nivel": 3, "evidencia_suficiente": True, "observaciones_citadas": [10, 20],
            "conductas_observadas": ["Se viste de forma autónoma"], "justificacion": "Avanza de ayuda a autonomía."}


def test_oficial_reserva_ejemplos_seudonimiza_y_ordena(entrada, identidades, respuesta, cliente_falso):
    original = copy.deepcopy(entrada)
    cliente = cliente_falso(respuesta)
    assert proponer(entrada, identidades, cliente=cliente) == respuesta
    llamada = cliente.llamadas[0]
    enviado = json.loads(llamada["mensaje"])
    assert [o["id"] for o in enviado["observaciones"]] == [10, 20]
    assert enviado["nivel_actual"] == 1
    assert enviado["rubrica"]["origen"] == "integra"
    assert "trayectoria" not in enviado["rubrica"] and "conductas_programa" not in enviado["rubrica"]
    serializado = json.dumps(llamada, ensure_ascii=False)
    for texto in ["Pedro", "Salinas", "Nayara", "Naiara", "RESERVADO", '"identidades":', '"alias":']:
        assert texto not in serializado
    assert "N-A00002" in serializado and "N-A00001" in serializado
    assert entrada == original


def test_provisoria_envia_trayectoria_conductas_y_mapeo(entrada, identidades, respuesta, cliente_falso):
    for d in entrada["descriptores"]:
        d["provisorio"] = True
        d["conducta"] = ""
    entrada["trayectoria"] = {"inicio_nt1": "Inicio esperado", "continuidad": "Hacia básica"}
    entrada["manifestaciones"] = [{"oa_id": 1, "anio": "NT1", "orden": 0, "texto": "Con ayuda"},
                                 {"oa_id": 1, "anio": "NT2", "orden": 0, "texto": "De forma autónoma"}]
    cliente = cliente_falso(respuesta)
    proponer(entrada, identidades, cliente=cliente)
    rubrica = json.loads(cliente.llamadas[0]["mensaje"])["rubrica"]
    assert rubrica["origen"] == "provisoria"
    assert rubrica["trayectoria"]["inicio_nt1"] == "Inicio esperado"
    assert rubrica["conductas_programa"][0] == {"oa": "OA 1 IA", "NT1": ["Con ayuda"], "NT2": ["De forma autónoma"]}
    assert len(rubrica["niveles"]) == 8


def test_sin_observaciones_no_invoca_ni_requiere_rubrica(identidades, cliente_falso):
    cliente = cliente_falso()
    resultado = proponer({"evidencia": []}, identidades, cliente=cliente)
    assert resultado["nivel"] is None and resultado["evidencia_suficiente"] is False
    assert resultado["observaciones_citadas"] == [] and cliente.llamadas == []


def test_una_observacion_puede_bastar_sin_exigir_ascenso(entrada, identidades, respuesta, cliente_falso):
    entrada["evidencia"] = entrada["evidencia"][:1]
    respuesta.update(nivel=1, observaciones_citadas=[20])
    cliente = cliente_falso(respuesta)
    assert proponer(entrada, identidades, cliente=cliente)["nivel"] == 1
    assert "No impongas un mínimo" in cliente.llamadas[0]["system"]


def test_rubrica_de_nueve_niveles(entrada, identidades, respuesta, cliente_falso):
    entrada["rubrica"][0]["cantidad_niveles"] = 9
    entrada["descriptores"].append({**entrada["descriptores"][-1], "nivel": 9})
    respuesta["nivel"] = 9
    cliente = cliente_falso(respuesta)
    assert proponer(entrada, identidades, cliente=cliente)["nivel"] == 9
    propiedad = cliente.llamadas[0]["herramienta"]["inputSchema"]["json"]["properties"]["nivel"]
    assert propiedad["maximum"] == 9


@pytest.mark.parametrize("cambio", ["sin_rubrica", "sin_descriptor", "sin_conducta", "mixta", "sin_referencia", "sin_trayectoria"])
def test_configuracion_incompleta_falla_antes_de_invocar(entrada, identidades, cliente_falso, cambio):
    if cambio == "sin_rubrica":
        entrada["rubrica"] = []
    elif cambio == "sin_descriptor":
        entrada["descriptores"].pop()
    elif cambio == "sin_conducta":
        entrada["descriptores"][0]["conducta"] = ""
    elif cambio == "mixta":
        entrada["descriptores"][0]["provisorio"] = True
    elif cambio == "sin_referencia":
        entrada["referencia"] = None
    else:
        for d in entrada["descriptores"]:
            d["provisorio"] = True
    cliente = cliente_falso()
    with pytest.raises(ErrorConfiguracionPropuesta):
        proponer(entrada, identidades, cliente=cliente)
    assert cliente.llamadas == []


@pytest.mark.parametrize("campo,valor", [
    ("nivel", True), ("nivel", 3.0), ("nivel", "3"), ("nivel", 0), ("nivel", 9), ("nivel", None),
    ("evidencia_suficiente", "true"), ("evidencia_suficiente", 1),
    ("observaciones_citadas", [999]), ("observaciones_citadas", [True]), ("observaciones_citadas", ["10"]),
    ("observaciones_citadas", [10, 10]), ("observaciones_citadas", []), ("observaciones_citadas", "10"),
    ("conductas_observadas", []), ("conductas_observadas", [""]), ("conductas_observadas", [4]),
    ("conductas_observadas", "Conducta"), ("justificacion", "  "), ("justificacion", None),
])
def test_rechaza_tipos_rangos_citas_y_textos_incoherentes(respuesta, campo, valor):
    respuesta[campo] = valor
    with pytest.raises(ErrorPropuesta):
        validar_respuesta(respuesta, nivel_maximo=8, ids_enviados={10, 20})


@pytest.mark.parametrize("valor", [None, [], "json inválido", {"nivel": 3}])
def test_rechaza_respuestas_sin_contrato(valor):
    with pytest.raises(ErrorPropuesta):
        validar_respuesta(valor, nivel_maximo=8, ids_enviados={10})


def test_insuficiencia_exige_nivel_nulo(respuesta):
    respuesta["evidencia_suficiente"] = False
    with pytest.raises(ErrorPropuesta):
        validar_respuesta(respuesta, nivel_maximo=8, ids_enviados={10, 20})
    respuesta.update(nivel=None, observaciones_citadas=[], conductas_observadas=[])
    assert validar_respuesta(respuesta, nivel_maximo=8, ids_enviados={10, 20})["nivel"] is None


def test_error_de_bedrock_no_expone_texto_del_error(entrada, identidades, cliente_falso, caplog):
    cliente = cliente_falso(ErrorBedrock("Respuesta con Pedro y su cita"))
    with pytest.raises(ErrorPropuesta) as error:
        proponer(entrada, identidades, cliente=cliente)
    assert "Pedro" not in str(error.value) and "Pedro" not in caplog.text


def test_limpia_nombres_conocidos_en_la_respuesta(entrada, identidades, respuesta, cliente_falso):
    respuesta["justificacion"] = "Pedro progresó con Nayara."
    resultado = proponer(entrada, identidades, cliente=cliente_falso(respuesta))
    assert resultado["justificacion"] == "N-A00001 progresó con N-A00002."
