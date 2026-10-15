"""El currículo extraído del Programa Pedagógico de Transición está completo."""
from registro.curriculo import leer_curriculo

SIGLAS = ["IA", "CC", "CM", "LV", "LA", "EEN", "CES", "PM"]


def test_tiene_los_8_nucleos_en_orden():
    datos = leer_curriculo()
    assert [n["sigla"] for n in datos["nucleos"]] == SIGLAS


def test_tiene_85_oa():
    datos = leer_curriculo()
    assert sum(len(n["oas"]) for n in datos["nucleos"]) == 85


def test_oa_numerados_sin_saltos_por_nucleo():
    for n in leer_curriculo()["nucleos"]:
        numeros = [o["numero"] for o in n["oas"]]
        assert numeros == list(range(1, len(numeros) + 1)), n["sigla"]


def test_cada_oa_tiene_conductas_de_nt1_y_nt2():
    faltantes = [
        (o["codigo"], anio)
        for n in leer_curriculo()["nucleos"]
        for o in n["oas"]
        for anio in ("NT1", "NT2")
        if not o["conductas"].get(anio)
    ]
    assert faltantes == []


def test_cada_nucleo_tiene_su_trayectoria_completa():
    for n in leer_curriculo()["nucleos"]:
        assert n["esperado_inicio_nt1"].startswith("Al iniciar Primer Nivel de Transición"), n["sigla"]
        assert n["continuidad_basica"].startswith("Durante"), n["sigla"]


def test_no_quedan_textos_marcados_para_revisar():
    import json

    assert "REVISAR" not in json.dumps(leer_curriculo(), ensure_ascii=False)
