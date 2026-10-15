"""Métricas de la Task 10 sobre resultados conocidos, y `manage.py evaluar` con cliente falso."""
import json
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command

from registro.coincidencia import emparejar
from registro.evaluacion import (
    INDICE_EJEMPLO_RESERVADO, ResultadoNota, asignar_ninos, casos_propuesta_ia, costo_usd, diferencias,
    emparejar_observaciones, metricas_propuestas, metricas_separacion, ninos_del_curso,
)
from registro.tests.ia.conftest import ClienteFalso

DATOS = Path(settings.DATOS_DIR)
SET = json.loads((DATOS / "eval" / "notas_separacion.json").read_text(encoding="utf-8"))
DEMO = json.loads((DATOS / "demo_curso.json").read_text(encoding="utf-8"))
RUBRICA = json.loads((DATOS / "rubrica_integra.json").read_text(encoding="utf-8"))
NINOS = ninos_del_curso(DEMO)
SONNET = "us.anthropic.claude-sonnet-5"


def _esperada(nombre="Pedro", nino="Pedro Salinas", nucleos=("PM",), oas=("OA 2 PM",), apoyo="autonomo", **otros):
    return {"nombre_detectado": nombre, "nino": nino, "nucleos": list(nucleos), "oas": list(oas),
            "apoyo": apoyo, "grupal": False, **otros}


def _obtenida(**campos):
    """Como la devuelve separar() más asignar_ninos(): mismos campos que _esperada, con cita e interpretación."""
    obs = {"cita_literal": "cita", "interpretacion": None, "fecha": "2026-05-25", **_esperada(**campos)}
    obs.pop("tiene_interpretacion", None)
    return obs


def _grupal():
    return {"nombre_detectado": None, "nucleos": [], "oas": [], "apoyo": "sin_dato", "grupal": True}


# --- El set de prueba ---

def test_los_nombres_del_set_son_los_ninos_de_la_demo():
    assert SET["nombres_curso"] == [n.nombre for n in NINOS]


@pytest.mark.parametrize(
    "nota_id, esperada",
    [(n["id"], e) for n in SET["notas"] for e in n["esperado"] if not e["grupal"]],
)
def test_el_nino_esperado_es_el_que_asigna_la_coincidencia(nota_id, esperada):
    """Si el modelo detecta el nombre tal como está escrito, la coincidencia asigna el niño esperado."""
    assert "nino" in esperada
    nino = emparejar(esperada["nombre_detectado"], NINOS).nino
    assert (nino.nombre if nino else None) == esperada["nino"]


def test_el_set_trae_casos_sin_asignar():
    sin_asignar = {e["nombre_detectado"] for n in SET["notas"] for e in n["esperado"] if "nino" in e and e["nino"] is None}
    assert sin_asignar == {"Sofía", "Abel"}


# --- Emparejamiento de observaciones ---

def test_empareja_por_nombre_normalizado_y_luego_por_nino():
    esperadas = [_esperada("Rubi", "Rubí Contreras"), _esperada("Benja", "Benjamín Soto"), _grupal()]
    obtenidas = [_obtenida(nombre="Benjamín", nino="Benjamín Soto"), _obtenida(nombre="RUBI", nino="Rubí Contreras"),
                 {**_grupal(), "nino": None}]
    pares, faltantes, sobrantes = emparejar_observaciones(esperadas, obtenidas)
    assert [(e["nombre_detectado"], o["nombre_detectado"]) for e, o in pares] == [
        ("Rubi", "RUBI"), (None, None), ("Benja", "Benjamín")
    ]
    assert faltantes == [] and sobrantes == []


def test_sin_nino_no_empareja_por_nino():
    """Dos observaciones sin niño asignado (p. ej. Sofía y Abel) no se emparejan entre sí."""
    pares, faltantes, sobrantes = emparejar_observaciones([_esperada("Sofía", None)], [_obtenida(nombre="Abel", nino=None)])
    assert pares == [] and len(faltantes) == 1 and len(sobrantes) == 1


def test_asignar_ninos_deja_sin_nino_las_grupales_y_las_ambiguas():
    obs = [{"nombre_detectado": "Nayara", "grupal": False}, {"nombre_detectado": "Sofía", "grupal": False},
           {"nombre_detectado": "Pedro", "grupal": True}]
    assert [o["nino"] for o in asignar_ninos(obs, NINOS)] == ["Naiara Fuentes", None, None]


# --- Métricas de separación ---

def test_todo_correcto_da_100_por_ciento():
    esperadas = [_esperada(fecha="2026-05-25", tiene_interpretacion=False), _grupal()]
    obtenidas = [_obtenida(), {**_grupal(), "nino": None}]
    m = metricas_separacion([ResultadoNota("n1", esperadas, obtenidas, segundos=2.0)])
    for clave in ("observaciones", "ninos", "apoyo", "fecha", "interpretacion"):
        assert m[clave].valor == 1, clave
    for clave in ("nucleos", "oas"):
        assert m[clave].precision.valor == 1 and m[clave].cobertura.valor == 1, clave
    assert m["observaciones_de_mas"] == 0 and m["notas_con_error"] == 0


def test_precision_y_cobertura_de_oa_suman_etiquetas():
    esperadas = [_esperada(oas=["OA 2 PM", "OA 4 PM"])]
    obtenidas = [_obtenida(oas=["OA 2 PM", "OA 6 PM", "OA 7 PM"])]
    oas = metricas_separacion([ResultadoNota("n1", esperadas, obtenidas)])["oas"]
    assert (oas.correctas, oas.sobrantes, oas.faltantes) == (1, 2, 1)
    assert oas.precision.valor == pytest.approx(1 / 3) and oas.cobertura.valor == pytest.approx(1 / 2)


def test_una_observacion_que_falta_resta_en_ninos_y_cobertura_pero_no_en_apoyo():
    esperadas = [_esperada(), _esperada("Emilio", "Emilio Vargas", nucleos=["LV"], oas=["OA 8 LV"])]
    m = metricas_separacion([ResultadoNota("n1", esperadas, [_obtenida()])])
    assert (m["observaciones"].aciertos, m["observaciones"].total) == (1, 2)
    assert (m["ninos"].aciertos, m["ninos"].total) == (1, 2)
    assert m["nucleos"].cobertura.valor == 1 / 2 and m["nucleos"].precision.valor == 1
    assert (m["apoyo"].aciertos, m["apoyo"].total) == (1, 1)


def test_una_observacion_de_mas_resta_en_precision():
    obtenidas = [_obtenida(), _obtenida(nombre="Abel", nino=None, nucleos=["CM"], oas=["OA 7 CM"])]
    m = metricas_separacion([ResultadoNota("n1", [_esperada()], obtenidas)])
    assert m["observaciones_de_mas"] == 1 and m["observaciones_obtenidas"] == 2
    assert m["nucleos"].precision.valor == 1 / 2 and m["oas"].precision.valor == 1 / 2
    assert m["ninos"].valor == 1


def test_nino_mal_asignado_y_apoyo_distinto():
    esperadas = [_esperada("Sofía", None, apoyo="autonomo")]
    obtenidas = [_obtenida(nombre="Sofía", nino="Sofía Rojas", apoyo="con_ayuda")]
    m = metricas_separacion([ResultadoNota("n1", esperadas, obtenidas)])
    assert m["ninos"].valor == 0 and m["apoyo"].valor == 0
    assert diferencias(esperadas[0], obtenidas[0]) == {
        "nino": (None, "Sofía Rojas"), "apoyo": ("autonomo", "con_ayuda")
    }


def test_nota_con_error_cuenta_todo_como_faltante_y_no_entra_en_los_tiempos():
    con_error = ResultadoNota("n1", [_esperada()], error="Bedrock falló")
    bien = ResultadoNota("n2", [_esperada()], [_obtenida()], segundos=3.0, tokens_entrada=1000, tokens_salida=100)
    m = metricas_separacion([con_error, bien], modelo=SONNET)
    assert m["notas_con_error"] == 1
    assert (m["ninos"].aciertos, m["ninos"].total) == (1, 2)
    assert m["segundos"] == {"media": 3.0, "mediana": 3.0, "maximo": 3.0}
    assert m["costo_usd"]["media"] == pytest.approx(costo_usd(SONNET, 1000, 100))


def test_tiempos_media_mediana_y_maximo():
    resultados = [ResultadoNota(f"n{i}", [], [], segundos=s) for i, s in enumerate([1.0, 2.0, 6.0, 3.0])]
    assert metricas_separacion(resultados)["segundos"] == {"media": 3.0, "mediana": 2.5, "maximo": 6.0}


def test_sin_casos_las_proporciones_quedan_vacias():
    m = metricas_separacion([])
    assert m["ninos"].valor is None and m["oas"].precision.valor is None and m["segundos"] is None


def test_costo_con_los_precios_de_la_investigacion():
    assert costo_usd(SONNET, 1_000_000, 0) == pytest.approx(2.20)
    assert costo_usd(SONNET, 1000, 100) == pytest.approx(0.0022 + 0.0011)
    assert costo_usd("us.anthropic.claude-haiku-4-5-20251001-v1:0", 0, 1_000_000) == pytest.approx(5.50)
    assert costo_usd("modelo-desconocido", 1000, 100) is None
    assert costo_usd(SONNET, None, 100) is None


# --- Propuesta de nivel (para la Task 7) ---

def test_propuestas_exactas_y_a_un_nivel():
    m = metricas_propuestas([(3, 3), (4, 5), (7, 4), (2, None)])
    assert m["casos"] == 4 and m["sin_propuesta"] == 1
    assert (m["exactas"].aciertos, m["exactas"].total) == (1, 4)
    assert (m["a_un_nivel"].aciertos, m["a_un_nivel"].total) == (2, 4)
    assert m["error_medio"] == pytest.approx((0 + 1 + 3) / 3)


def test_propuestas_sin_ninguna():
    m = metricas_propuestas([(1, None)])
    assert m["exactas"].valor == 0 and m["error_medio"] is None


def test_casos_de_propuesta_usan_el_ejemplo_reservado_de_cada_nivel_de_ia():
    casos = casos_propuesta_ia(RUBRICA)
    bloque = next(b for b in RUBRICA["rubricas"] if b["nivel_educativo"] == "transicion" and b["sigla"] == "IA")
    assert [c["nivel"] for c in casos] == list(range(1, 9))
    assert casos[2]["nombre"] == "Desarrollando"
    for caso, nivel in zip(casos, bloque["niveles"]):
        assert caso["texto"] == nivel["ejemplos"][INDICE_EJEMPLO_RESERVADO]
        assert caso["texto"] not in nivel["ejemplos"][:INDICE_EJEMPLO_RESERVADO]


def test_casos_de_propuesta_de_un_nucleo_sin_rubrica():
    with pytest.raises(ValueError, match="LV"):
        casos_propuesta_ia(RUBRICA, sigla="LV")


# --- manage.py evaluar con cliente falso ---

def _respuesta_perfecta(nota):
    """Lo que devolvería un modelo que acierta todo en la nota."""
    return {"observaciones": [
        {
            "nombre_detectado": e["nombre_detectado"],
            "fecha": e.get("fecha", nota["fecha_captura"]),
            "cita_literal": nota["texto"][:40],
            "interpretacion": "Interpretación de quien escribe." if e.get("tiene_interpretacion") else None,
            "nucleos": e["nucleos"],
            "oas": e["oas"],
            "apoyo": e["apoyo"],
            "grupal": e["grupal"],
        }
        for e in nota["esperado"]
    ]}


class _ClienteFalsoConUso(ClienteFalso):
    def __init__(self, modelo, *respuestas):
        super().__init__(*respuestas)
        self.modelo = modelo
        self.ultimo_uso = {"tokens_entrada": 9500, "tokens_salida": 400}


def _evaluar(*args, respuestas=None, **opciones):
    """Corre el comando. Sin `respuestas`, el falso acierta todo en las notas pedidas, en su orden."""
    ids = opciones.get("ids")
    notas = [n for n in SET["notas"] if not ids or n["id"] in ids]
    clientes = []

    def crear_cliente(modelo):
        cliente = _ClienteFalsoConUso(modelo or SONNET, *(respuestas or [_respuesta_perfecta(n) for n in notas]))
        clientes.append(cliente)
        return cliente

    salida, errores = StringIO(), StringIO()
    call_command("evaluar", *args, crear_cliente=crear_cliente, stdout=salida, stderr=errores, **opciones)
    return salida.getvalue(), errores.getvalue(), clientes


def _valor(salida, etiqueta):
    """Lo que dice la tabla en la fila `etiqueta` (con un solo modelo)."""
    linea = next(l for l in salida.splitlines() if l.startswith(etiqueta))
    return linea[len(etiqueta):].strip()


def test_evaluar_con_respuestas_perfectas_da_100_por_ciento_en_todo_el_set():
    salida, errores, clientes = _evaluar()
    assert errores == ""
    assert len(clientes[0].llamadas) == len(SET["notas"]) == 20
    assert _valor(salida, "Niños bien asignados") == "22/22 (100 %)"
    assert _valor(salida, "Observaciones encontradas") == "23/23 (100 %)"
    assert _valor(salida, "Observaciones de más") == "0"
    for etiqueta in ("Núcleos: precisión", "Núcleos: cobertura", "OA: precisión", "OA: cobertura",
                     "Nivel de apoyo correcto", "Fecha correcta", "Interpretación separada"):
        assert _valor(salida, etiqueta).endswith("(100 %)"), etiqueta
    # 9.500 tokens de entrada y 400 de salida con Sonnet 5: 0,0209 + 0,0044 USD.
    assert _valor(salida, "USD por nota") == "0,0253"
    assert _valor(salida, "USD por 1.000 notas") == "25,30"


def test_evaluar_compara_modelos_y_acepta_alias():
    salida, _, clientes = _evaluar("--modelo", "sonnet", "--modelo", "haiku", ids=["n01"])
    assert [c.modelo for c in clientes] == [SONNET, "us.anthropic.claude-haiku-4-5-20251001-v1:0"]
    # Una columna por modelo en la misma tabla.
    assert any(SONNET in l and "claude-haiku-4-5" in l for l in salida.splitlines())
    assert _valor(salida, "Niños bien asignados").count("1/1 (100 %)") == 2


def test_evaluar_detalle_muestra_lo_que_no_calzo():
    nota = next(n for n in SET["notas"] if n["id"] == "n04")
    respuesta = _respuesta_perfecta(nota)
    respuesta["observaciones"][2]["apoyo"] = "autonomo"  # Rubi era con_ayuda
    del respuesta["observaciones"][1]  # falta Emilio
    salida, _, _ = _evaluar("--detalle", ids=["n04"], respuestas=[respuesta])
    assert "falta la observación de Emilio" in salida
    assert "Rubi: apoyo esperado con_ayuda, obtenido autonomo" in salida
    assert _valor(salida, "Observaciones encontradas") == "2/3 (67 %)"


def test_evaluar_registra_errores_de_bedrock_y_sigue():
    from registro.ia import ErrorBedrock

    nota = next(n for n in SET["notas"] if n["id"] == "n02")
    salida, errores, _ = _evaluar(ids=["n01", "n02"], respuestas=[ErrorBedrock("throttling"), _respuesta_perfecta(nota)])
    assert "n01: error" in errores
    assert _valor(salida, "Notas evaluadas (con error)") == "2 (1)"


def test_evaluar_guarda_json(tmp_path):
    ruta = tmp_path / "resultados.json"
    _evaluar(ids=["n01", "n05"], json=str(ruta))
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    resultado = datos[SONNET]
    assert resultado["metricas"]["ninos"] == {"aciertos": 1, "total": 1, "valor": 1.0}
    assert resultado["metricas"]["oas"]["precision"] == 1.0
    assert [n["id"] for n in resultado["notas"]] == ["n01", "n05"]
    assert resultado["notas"][0]["obtenidas"][0]["nino"] == "Naiara Fuentes"


def test_evaluar_falla_si_todas_las_notas_fallan():
    """Sin credenciales, todas fallan: el comando muestra la tabla y termina con un error claro."""
    from registro.ia import ErrorBedrock

    with pytest.raises(CommandError, match="credenciales"):
        _evaluar(ids=["n01", "n02"], respuestas=[ErrorBedrock("sin credenciales")] * 2)


def test_evaluar_rechaza_ids_que_no_existen():
    with pytest.raises(CommandError, match="n99"):
        _evaluar(ids=["n01", "n99"])
