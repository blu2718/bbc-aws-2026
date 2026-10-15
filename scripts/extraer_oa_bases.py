"""Extrae los OA de sala cuna y nivel medio de las Bases Curriculares (MINEDUC, 2018).

El Programa Pedagógico de Transición (`extraer_curriculo.py`) solo cubre Transición.
Para trabajar con niños de 0 a 4 años hacen falta los 50 OA de sala cuna y los 71
de nivel medio, que están en las Bases. Este script los saca del PDF y escribe
`datos/curriculo_sala_cuna.json` y `datos/curriculo_medio.json`, con la misma forma
que `datos/curriculo_transicion.json` (sin conductas por año: las Bases no las traen).

El PDF no se versiona. Para regenerar:

    # desde la raíz del repo
    Invoke-WebRequest https://www.curriculumnacional.cl/614/articles-69957_bases.pdf `
        -OutFile contexto/bases-curriculares-educacion-parvularia-2018.pdf
    python -m pip install --target $env:TEMP/kimun_pdf pypdf==5.4.0
    python -X utf8 scripts/extraer_oa_bases.py --pypdf $env:TEMP/kimun_pdf

Revisa que los conteos calcen con la tabla de `contexto/hallazgos-bases-curriculares.md`
(el script falla si no calzan) y que los textos de Transición coincidan con el currículo ya cargado.
"""
import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA_PDF = RAIZ / "contexto" / "bases-curriculares-educacion-parvularia-2018.pdf"
FUENTE = "Bases Curriculares de la Educación Parvularia (MINEDUC, 2018), capítulo 2"
FUENTE_URL = "https://www.curriculumnacional.cl/614/articles-69957_bases.pdf"

NUCLEOS = {
    "Identidad y Autonomía": "IA",
    "Convivencia y Ciudadanía": "CC",
    "Corporalidad y Movimiento": "CM",
    "Lenguaje Verbal": "LV",
    "Lenguajes Artísticos": "LA",
    "Exploración del Entorno Natural": "EEN",
    "Comprensión del Entorno Sociocultural": "CES",
    "Pensamiento Matemático": "PM",
}
NIVELES = {"Sala Cuna": "sala_cuna", "Medio": "medio", "Transición": "transicion"}
# Conteos de la tabla de hallazgos-bases-curriculares.md, en el orden de NUCLEOS.
ESPERADOS = {
    "sala_cuna": [7, 6, 7, 8, 6, 5, 5, 6],
    "medio": [12, 10, 8, 8, 7, 9, 7, 10],
    "transicion": [13, 11, 9, 10, 7, 12, 11, 12],
}
PAGINAS_OA = range(47, 104)  # páginas del PDF del capítulo 2 con los OA

# El PDF a veces separa la primera letra por el interletrado ("T ercer Nivel").
ENCABEZADO_NIVEL = re.compile(r"^(P ?rimer|S ?egundo|T ?ercer) Nivel \((Sala Cuna|Medio|Transición)\)\s*$")
PIE_NUCLEO = re.compile(r"/\s*Núcleo\s+(.+?)\s*$")
ITEM = re.compile(r"^(\d{1,2})\.\s+(.*)$")
RUIDO = re.compile(
    r"^(\d{1,3}|Bases Curriculares de la Educación Parvularia|Capítulo 2\s*/\s*Organización Curricular|"
    r"Objetivos de Aprendizaje( transversales)?)\s*$"
)


def leer_paginas(ruta, ruta_pypdf):
    if ruta_pypdf:
        sys.path.insert(0, str(ruta_pypdf))
    from pypdf import PdfReader

    lector = PdfReader(str(ruta))
    return [(i + 1, pagina.extract_text() or "") for i, pagina in enumerate(lector.pages)]


def extraer(paginas):
    """{nivel educativo: {sigla: [(número, texto)]}}."""
    resultado = {nivel: {sigla: [] for sigla in NUCLEOS.values()} for nivel in NIVELES.values()}
    pendientes = []  # (nivel, número, texto) hasta ver el pie con el núcleo
    nivel = None
    actual = None
    previo = None    # (nivel, último número) de la página anterior, por si la lista sigue
    for numero_pagina, texto in paginas:
        if numero_pagina not in PAGINAS_OA:
            continue
        for linea in texto.splitlines():
            linea = " ".join(linea.split())
            if not linea or RUIDO.match(linea):
                continue
            if m := ENCABEZADO_NIVEL.match(linea):
                nivel, actual = NIVELES[m.group(2)], None
                continue
            if m := PIE_NUCLEO.search(linea):
                nombre = m.group(1)
                sigla = NUCLEOS.get(nombre)
                if sigla is None:
                    raise SystemExit(f"Página {numero_pagina}: núcleo desconocido «{nombre}».")
                for nivel_oa, numero, texto_oa in pendientes:
                    resultado[nivel_oa][sigla].append((numero, texto_oa))
                # La lista puede seguir en la página siguiente sin repetir el encabezado del nivel.
                previo = (nivel, actual[1]) if nivel and actual else None
                pendientes, actual, nivel = [], None, None
                continue
            if nivel is None:
                m = ITEM.match(linea)
                if not (m and previo and int(m.group(1)) == previo[1] + 1):
                    continue
                nivel, actual = previo[0], [previo[0], previo[1], ""]
                previo = None
            if (m := ITEM.match(linea)) and (actual is None or int(m.group(1)) == actual[1] + 1 or int(m.group(1)) == 1):
                actual = [nivel, int(m.group(1)), m.group(2)]
                pendientes.append(actual)
            elif actual is not None:
                actual[2] += " " + linea  # el OA sigue en la línea siguiente
    for nivel_oa in resultado.values():
        for sigla, oas in nivel_oa.items():
            vistos = {}
            for numero, texto_oa in oas:
                vistos.setdefault(numero, texto_oa.strip())
            nivel_oa[sigla] = sorted(vistos.items())
    return resultado


def revisar(resultado):
    errores = []
    for nivel, esperados in ESPERADOS.items():
        for (nombre, sigla), esperado in zip(NUCLEOS.items(), esperados):
            numeros = [n for n, _ in resultado[nivel][sigla]]
            if numeros != list(range(1, esperado + 1)):
                errores.append(f"{nivel} {sigla}: se esperaban {esperado} OA y salieron {numeros}")
    if errores:
        raise SystemExit("Los conteos no calzan con las Bases:\n" + "\n".join(errores))


def a_json(nivel, por_nucleo):
    return {
        "nivel_educativo": nivel,
        "fuente": FUENTE,
        "fuente_url": FUENTE_URL,
        "provisorio": False,
        "nucleos": [
            {
                "sigla": sigla,
                "nombre": nombre,
                "oas": [
                    {"numero": n, "codigo": f"OA {n} {sigla}", "texto": t, "conductas": {}}
                    for n, t in por_nucleo[sigla]
                ],
            }
            for nombre, sigla in NUCLEOS.items()
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", type=Path, default=RUTA_PDF)
    parser.add_argument("--pypdf", type=Path, help="carpeta donde se instaló pypdf con --target")
    args = parser.parse_args()
    resultado = extraer(leer_paginas(args.pdf, args.pypdf))
    revisar(resultado)
    for nivel, nombre in (("sala_cuna", "curriculo_sala_cuna.json"), ("medio", "curriculo_medio.json")):
        ruta = RAIZ / "datos" / nombre
        ruta.write_text(json.dumps(a_json(nivel, resultado[nivel]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        total = sum(len(v) for v in resultado[nivel].values())
        print(f"{ruta.relative_to(RAIZ)}: {total} OA")

    # Control: Transición debe calzar con el currículo que ya usa la app.
    transicion = json.loads((RAIZ / "datos" / "curriculo_transicion.json").read_text(encoding="utf-8"))
    distintos = [
        f"OA {oa['numero']} {n['sigla']}"
        for n in transicion["nucleos"] for oa in n["oas"]
        if dict(resultado["transicion"][n["sigla"]]).get(oa["numero"], "").split() != oa["texto"].split()
    ]
    print(f"Control con curriculo_transicion.json: {85 - len(distintos)} de 85 OA iguales" +
          (f" (distintos: {', '.join(distintos[:10])})" if distintos else ""))


if __name__ == "__main__":
    main()
