"""Seudonimización de la Task 7: funciones puras, sin BD, red ni credenciales."""
import copy
import json
import unicodedata

import pytest

from registro.ia.seudonimo import MARCADOR_AMBIGUO, Seudonimizador, seudonimizar_texto


@pytest.fixture
def identidades():
    return [
        {"nombre": "Pedro Salinas", "alias": ["Pedrito"], "codigo": "N-A00001"},
        {"nombre": "Naiara Fuentes", "alias": ["Nayara", "Naia"], "codigo": "N-A00002"},
        {"nombre": "Sofía Rojas", "alias": ["Sofi R", "Sofi"], "codigo": "N-A00003"},
        {"nombre": "Sofía Muñoz", "alias": ["Sofi M", "Sofi"], "codigo": "N-A00004"},
        {"nombre": "María José Pérez", "alias": ["Jose"], "codigo": "N-A00005"},
        {"nombre": "Rubí Contreras", "alias": [], "codigo": "N-A00006"},
    ]


@pytest.mark.parametrize("nombre", ["Pedro", "PEDRO", "pedro salinas", "Pedrito"])
def test_nombres_completos_de_pila_y_apodos(identidades, nombre):
    assert seudonimizar_texto(f"{nombre} eligió su ropa.", identidades) == "N-A00001 eligió su ropa."


@pytest.mark.parametrize("nombre", ["Naiara", "Nayara", "NAIA"])
def test_variantes_de_escritura_declaradas_como_alias(identidades, nombre):
    assert seudonimizar_texto(f"Con {nombre}.", identidades) == "Con N-A00002."


@pytest.mark.parametrize("nombre", ["Rubí", "RUBI", unicodedata.normalize("NFD", "Rubí")])
def test_tildes_y_unicode_descompuesto(identidades, nombre):
    assert seudonimizar_texto(f"{nombre}: ¡sí, lo logré!", identidades) == "N-A00006: ¡sí, lo logré!"


@pytest.mark.parametrize("nombre", ["María", "MARIA JOSE", "María José Pérez", "María\tJosé\nPérez"])
def test_nombres_compuestos_y_coincidencia_mas_larga(identidades, nombre):
    assert seudonimizar_texto(f"{nombre} participó.", identidades) == "N-A00005 participó."


def test_solo_el_nombre_ambiguo_no_se_atribuye_a_una_sofia(identidades):
    texto = "Sofía y Sofi jugaron con Sofía Rojas, SOFIA MUÑOZ, Sofi R y Sofi M."
    assert seudonimizar_texto(texto, identidades) == (
        f"{MARCADOR_AMBIGUO} y {MARCADOR_AMBIGUO} jugaron con N-A00003, N-A00004, N-A00003 y N-A00004."
    )


def test_alias_que_coincide_con_otro_nombre_tambien_es_ambiguo(identidades):
    identidades[0]["alias"].append("Naiara Fuentes")
    assert seudonimizar_texto("Naiara Fuentes habló.", identidades) == f"{MARCADOR_AMBIGUO} habló."


def test_alias_repetidos_del_mismo_nino_no_crean_ambiguedad(identidades):
    identidades[0]["alias"] += ["PEDRO", "Pédro", "Pedrito"]
    assert seudonimizar_texto("Pedro y Pedrito.", identidades) == "N-A00001 y N-A00001."


def test_no_reemplaza_fragmentos_de_palabras_y_conserva_el_original(identidades):
    texto = "  La pedagogía y el rubidio: Pedrote, Naiarita, pedro_id, xPedro, Pedro2.\n¡Qué día!  "
    assert seudonimizar_texto(texto, identidades) == texto
    assert seudonimizar_texto("(Pedro), «Rubí»; Naiara/Pedrito.", identidades) == (
        "(N-A00001), «N-A00006»; N-A00002/N-A00001."
    )


def test_reemplaza_a_todos_los_ninos_mencionados_y_conserva_signos(identidades):
    assert seudonimizar_texto("Pedro ayudó a Nayara; Rubí dijo: «¡gracias!».", identidades) == (
        "N-A00001 ayudó a N-A00002; N-A00006 dijo: «¡gracias!»."
    )


def test_alias_con_signos_no_es_una_expresion_regular(identidades):
    identidades[0]["alias"] = ["Pe.dro", "P+P"]
    assert seudonimizar_texto("Pe.dro y P+P; Pexdro.", identidades) == "N-A00001 y N-A00001; Pexdro."


def test_nombres_con_guion_y_apostrofo():
    ninos = [{"nombre": "Ana-María D'Ángelo", "codigo": "N-B00001"}]
    assert seudonimizar_texto("Ana-Maria D'Angelo y Ana-María.", ninos) == "N-B00001 y N-B00001."


def test_orden_del_curso_no_cambia_el_resultado(identidades):
    texto = "Sofía Rojas y Sofía con María José."
    assert seudonimizar_texto(texto, identidades) == seudonimizar_texto(texto, reversed(identidades))


def test_no_reescribe_codigos_ni_marcadores_y_es_idempotente(identidades):
    identidades[0]["alias"] += ["N", "NINO_AMBIGUO", "A00003"]
    seudonimo = Seudonimizador(identidades)
    texto = f"N-A00003, N-FFFFFF y {MARCADOR_AMBIGUO} con Pedro."
    salida = f"N-A00003, N-FFFFFF y {MARCADOR_AMBIGUO} con N-A00001."
    assert seudonimo.texto(texto) == salida
    assert seudonimo.texto(salida) == salida


def test_curso_vacio_y_texto_vacio():
    assert seudonimizar_texto("Una nota sin lista del curso.", []) == "Una nota sin lista del curso."
    assert seudonimizar_texto("", []) == ""


def test_datos_anidados_no_mutan_entrada_ni_identidades(identidades):
    datos = {"citas": [{"id": 7, "texto": "Pedro con Rubí", "apoyo": None}],
             "ejemplos": ["Nayara eligió", True, 3, 1.5], "interpretacion": "Sofía quiso ayudar"}
    original, curso = copy.deepcopy(datos), copy.deepcopy(identidades)
    salida = Seudonimizador(identidades).datos(datos)
    assert salida == {"citas": [{"id": 7, "texto": "N-A00001 con N-A00006", "apoyo": None}],
                      "ejemplos": ["N-A00002 eligió", True, 3, 1.5],
                      "interpretacion": f"{MARCADOR_AMBIGUO} quiso ayudar"}
    assert datos == original and identidades == curso


def test_envio_completo_limpia_prompt_ejemplos_y_descripciones_sin_enviar_diccionario(identidades, cliente_falso, caplog):
    cliente = cliente_falso({"nivel": 3})
    herramienta = {"name": "proponer_nivel", "description": "Conductas como las de Rubí",
                   "inputSchema": {"json": {"type": "object", "properties": {
                       "nivel": {"type": "integer", "description": "Ejemplo: Nayara eligió sola"}}}}}
    respuesta = Seudonimizador(identidades).invocar(
        cliente, "Ejemplo oficial: Pedro se vistió", "Sofía y María José cooperaron", herramienta,
    )
    assert respuesta == {"nivel": 3}
    llamada = cliente.llamadas[0]
    assert llamada["system"] == "Ejemplo oficial: N-A00001 se vistió"
    assert llamada["mensaje"] == f"{MARCADOR_AMBIGUO} y N-A00005 cooperaron"
    assert llamada["herramienta"]["inputSchema"]["json"]["properties"]["nivel"]["description"] == (
        "Ejemplo: N-A00002 eligió sola"
    )
    serializado = json.dumps(llamada, ensure_ascii=False)
    for palabra in ["Pedro", "Rubí", "Nayara", "Sofía", "María", "identidades", "alias"]:
        assert palabra not in serializado
        assert palabra not in caplog.text
    assert herramienta["description"] == "Conductas como las de Rubí"


def test_claves_con_nombres_se_rechazan_antes_del_envio(identidades, cliente_falso):
    cliente = cliente_falso({})
    with pytest.raises(ValueError):
        Seudonimizador(identidades).invocar(cliente, "Pedro", "Una cita", {"Pedro": "descripción"})
    assert cliente.llamadas == []


@pytest.mark.parametrize("serializado", [False, True])
def test_mensaje_json_limpia_nombres_antes_de_serializar_incluso_con_escapes(identidades, cliente_falso, serializado):
    mensaje = {"citas": ["Sofía con Rubí"], "ejemplos": ["Nayara eligió"]}
    cliente = cliente_falso({})
    entrada = json.dumps(mensaje, ensure_ascii=True) if serializado else mensaje
    Seudonimizador(identidades).invocar(cliente, "Rúbrica", entrada, {"name": "proponer_nivel"})
    assert json.loads(cliente.llamadas[0]["mensaje"]) == {
        "citas": [f"{MARCADOR_AMBIGUO} con N-A00006"], "ejemplos": ["N-A00002 eligió"],
    }


def test_no_infiere_por_similitud_nombres_no_declarados(identidades):
    assert seudonimizar_texto("Naira y una visitante.", identidades) == "Naira y una visitante."


def _demo_con_codigos():
    from pathlib import Path

    demo = json.loads((Path(__file__).resolve().parents[4] / "datos" / "demo_curso.json").read_text(encoding="utf-8"))
    for i, nino in enumerate(demo["ninos"]):
        nino["codigo"] = f"N-{i:06X}"
    return demo


def test_los_datos_de_demo_pueden_usarse_sin_django():
    ninos = _demo_con_codigos()["ninos"]
    seudonimo = Seudonimizador(ninos)
    for nino in ninos:
        for nombre in [nino["nombre"], *nino["alias"]]:
            assert seudonimo.texto(nombre) == nino["codigo"]


def test_las_citas_de_demo_identifican_a_su_propio_nino():
    """Con dos Sofías, «Sofía M.» debe ser un alias declarado: si no, su propia evidencia llega ambigua."""
    demo = _demo_con_codigos()
    codigos = {n["nombre"]: n["codigo"] for n in demo["ninos"]}
    seudonimo = Seudonimizador(demo["ninos"])
    for i, obs in enumerate(demo["observaciones"]):
        if obs.get("nino"):
            assert codigos[obs["nino"]] in seudonimo.texto(obs["cita"]), f"observación {i} de la demo"
    assert seudonimo.texto("Sofía M. miró a Sofía R.") == f"{codigos['Sofía Muñoz']} miró a {codigos['Sofía Rojas']}"
    assert seudonimo.texto("Sofía miró") == f"{MARCADOR_AMBIGUO} miró"


@pytest.mark.parametrize("identidad", [
    {"nombre": "Pedro", "codigo": "Pedro"},
    {"nombre": "", "codigo": "N-A00001"},
    {"nombre": "Pedro", "codigo": "N-A00001", "alias": "Pedrito"},
    {"nombre": "Pedro", "codigo": "N-A00001", "alias": [42]},
    {"codigo": "N-A00001"},
])
def test_datos_de_identidad_invalidos_fallan_sin_revelar_nombres(identidad):
    with pytest.raises(ValueError) as error:
        Seudonimizador([identidad])
    assert "Pedro" not in str(error.value) and "Pedrito" not in str(error.value)


def test_no_admite_codigos_repetidos(identidades):
    identidades[1]["codigo"] = identidades[0]["codigo"]
    with pytest.raises(ValueError):
        Seudonimizador(identidades)


def test_tipos_no_textuales_no_se_convierten_a_repr(identidades):
    with pytest.raises(TypeError):
        Seudonimizador(identidades).texto(None)
    with pytest.raises(TypeError):
        Seudonimizador(identidades).datos(object())
