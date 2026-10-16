"""Regenera las tablas de contenidos de `contexto/*.md` y el catálogo de `contexto/INDICE.md`.

Cada archivo lleva su tabla entre `<!-- indice:inicio -->` y `<!-- indice:fin -->`, antes del
primer encabezado `##`. Cada entrada trae el ancla y el rango de líneas de la sección, para
que un agente lea solo ese tramo (por ejemplo, con offset y limit). INDICE.md lleva, entre
`<!-- catalogo:inicio -->` y `<!-- catalogo:fin -->`, la tabla con el tamaño de cada archivo.

Uso, desde la raíz del repo:
    python scripts/indice_contexto.py              # reescribe los índices
    python scripts/indice_contexto.py --comprobar  # sale con código 1 si alguno está desactualizado

Correrlo después de editar cualquier archivo de `contexto/`: los rangos de líneas cambian.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

CONTEXTO = Path(__file__).resolve().parent.parent / "contexto"
INDICE = "INDICE.md"
INICIO, FIN = "<!-- indice:inicio -->", "<!-- indice:fin -->"
CAT_INICIO, CAT_FIN = "<!-- catalogo:inicio -->", "<!-- catalogo:fin -->"

ENCABEZADO = re.compile(r"^(#{2,4}) (.+?)\s*$")
# Subtítulos sin "#" que conviene indexar: las tablas de OA de la enciclopedia.
SUBTITULO = re.compile(r"^((?:Primer|Segundo|Tercer) Nivel \(.+?\) — pp?\. [\d–-]+)\s*$")


def ancla(texto, vistas):
    """Ancla al estilo de GitHub: minúsculas, sin puntuación, espacios a guiones, sufijo si se repite."""
    t = unicodedata.normalize("NFC", texto.replace("`", "")).lower()
    t = re.sub(r"[^\w\- ]", "", t).replace(" ", "-")
    n = vistas.get(t, 0)
    vistas[t] = n + 1
    return t if n == 0 else f"{t}-{n}"


def secciones(lineas):
    """Lista de (nivel, título, ancla o None, línea inicial) fuera de bloques de código y del índice."""
    res, vistas, en_codigo, en_indice = [], {}, False, False
    for i, linea in enumerate(lineas, start=1):
        if linea.startswith("```"):
            en_codigo = not en_codigo
        if en_codigo:
            continue
        if linea.strip() == INICIO:
            en_indice = True
        if en_indice:
            en_indice = linea.strip() != FIN
            continue
        m = ENCABEZADO.match(linea)
        if m:
            res.append((len(m.group(1)), m.group(2), ancla(m.group(2), vistas), i))
            continue
        m = SUBTITULO.match(linea)
        reales = [r for r in res if r[2] is not None]
        if m and reales:
            res.append((reales[-1][0] + 1, m.group(1), None, i))
    return res


def tabla(lineas):
    secs = secciones(lineas)
    total = len(lineas)
    filas = [
        INICIO,
        "## Índice",
        "",
        "Generado por `scripts/indice_contexto.py`. Cada entrada indica sus líneas en este archivo; lee solo las que necesites.",
        "",
    ]
    for k, (nivel, titulo, anc, ini) in enumerate(secs):
        fin = total
        for nivel2, _, _, ini2 in secs[k + 1:]:
            if nivel2 <= nivel or anc is None:
                fin = ini2 - 1
                break
        while fin > ini and not lineas[fin - 1].strip():
            fin -= 1
        sangria = "  " * (nivel - 2)
        nombre = f"[{titulo}](#{anc})" if anc else titulo
        filas.append(f"{sangria}- {nombre} · líneas {ini}–{fin}")
    filas.append(FIN)
    return filas


def con_indice(texto):
    """Devuelve el texto con su índice actualizado. Repite hasta que los números de línea se estabilizan."""
    lineas = texto.split("\n")
    if INICIO in texto:
        a, b = lineas.index(INICIO), lineas.index(FIN)
        lineas = lineas[:a] + lineas[b + 1:]
        pos = a
    else:
        pos = next(i for i, l in enumerate(lineas) if l.startswith("## "))
        lineas = lineas[:pos] + [""] + lineas[pos:]
    actual = lineas[:pos] + [INICIO, FIN] + lineas[pos:]
    for _ in range(5):
        a, b = actual.index(INICIO), actual.index(FIN)
        nuevo = actual[:a] + tabla(actual) + actual[b + 1:]
        if nuevo == actual:
            break
        actual = nuevo
    return "\n".join(actual)


def catalogo(archivos):
    filas = [CAT_INICIO, "| Archivo | Líneas | Palabras |", "|---|---:|---:|"]
    for p in archivos:
        t = p.read_text(encoding="utf-8")
        filas.append(f"| [`{p.name}`]({p.name}) | {t.count(chr(10)) + 1} | {len(t.split()):,} |".replace(",", "."))
    filas.append(CAT_FIN)
    return "\n".join(filas)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--comprobar", action="store_true", help="no escribe; falla si algún índice está desactualizado")
    args = ap.parse_args()

    archivos = sorted(p for p in CONTEXTO.glob("*.md") if p.name != INDICE)
    pendientes = []
    for p in archivos:
        viejo = p.read_text(encoding="utf-8")
        nuevo = con_indice(viejo)
        if nuevo != viejo:
            pendientes.append(p.name)
            if not args.comprobar:
                p.write_text(nuevo, encoding="utf-8")

    ruta = CONTEXTO / INDICE
    viejo = ruta.read_text(encoding="utf-8")
    a, b = viejo.index(CAT_INICIO), viejo.index(CAT_FIN) + len(CAT_FIN)
    nuevo = viejo[:a] + catalogo(archivos) + viejo[b:]
    if nuevo != viejo:
        pendientes.append(INDICE)
        if not args.comprobar:
            ruta.write_text(nuevo, encoding="utf-8")

    if args.comprobar and pendientes:
        print("Índices desactualizados: " + ", ".join(pendientes) + ". Corre python scripts/indice_contexto.py")
        return 1
    print(("Desactualizados: " if args.comprobar else "Actualizados: ") + (", ".join(pendientes) or "ninguno"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
