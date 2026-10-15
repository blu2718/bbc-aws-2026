"""Lee la foto de una nota contra Bedrock real, la separa y compara con lo esperado (Task 8).

Se corre desde la raíz del repo con el entorno de kimun/:

    kimun/.venv/Scripts/python.exe -X utf8 scripts/probar_foto.py --id p04
    kimun/.venv/Scripts/python.exe -X utf8 scripts/probar_foto.py --foto ruta/postit.jpg [--solo-lectura]

Con --id usa datos/eval/fotos/<id>.jpg y compara la lectura con el texto del
post-it y la separación con lo esperado (datos/eval/postits_fotos.json).
La foto debe pesar menos de 3,75 MB: si viene directo de la cámara, achícala
antes (por ejemplo, a 1600 px de lado mayor) o súbela desde la app, que lo hace sola.
El modelo sale de BEDROCK_MODEL_ID (o --modelo). No usa Django.
"""

import argparse
import difflib
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kimun"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from probar_separacion import comparar  # noqa: E402
from registro.ia import (  # noqa: E402
    ClienteBedrock,
    ErrorSeparacion,
    ErrorTranscripcion,
    ImagenInvalida,
    separar,
    transcribir_foto,
)

RUTA_CATALOGO = RAIZ / "datos" / "curriculo_transicion.json"
RUTA_SET = RAIZ / "datos" / "eval" / "postits_fotos.json"
RUTA_NOMBRES = RAIZ / "datos" / "eval" / "notas_separacion.json"
CARPETA_FOTOS = RAIZ / "datos" / "eval" / "fotos"


def _leer(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))


def _normalizar(texto):
    return " ".join(texto.split()).lower()


def comparar_lectura(esperado, obtenido):
    """Similitud entre lo escrito y lo leído (0 a 1), sin contar espacios ni mayúsculas."""
    similitud = difflib.SequenceMatcher(None, _normalizar(esperado), _normalizar(obtenido)).ratio()
    print(f"  Similitud con el texto del post-it: {similitud:.0%}")
    if similitud < 1:
        for linea in difflib.unified_diff(esperado.splitlines(), obtenido.splitlines(), "escrito", "leído", lineterm=""):
            print(f"    {linea}")
    return similitud


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--id", help="id de un post-it del set (p. ej. p04)")
    grupo.add_argument("--foto", type=Path, help="ruta de una foto cualquiera")
    parser.add_argument("--solo-lectura", action="store_true", help="no separar en observaciones")
    parser.add_argument("--modelo", help="ID del modelo o perfil de inferencia (por defecto BEDROCK_MODEL_ID)")
    args = parser.parse_args()

    conjunto = _leer(RUTA_SET)
    postit = None
    if args.id:
        postit = next((p for p in conjunto["postits"] if p["id"] == args.id), None)
        if postit is None:
            parser.error(f"no existe el post-it {args.id!r} en {RUTA_SET.relative_to(RAIZ)}")
        ruta = CARPETA_FOTOS / f"{args.id}.jpg"
    else:
        ruta = args.foto
    if not ruta.is_file():
        parser.error(f"no existe la foto {ruta}")

    cliente = ClienteBedrock(modelo=args.modelo)
    print(f"Modelo: {cliente.modelo} ({cliente.region})")
    print(f"Foto: {ruta} ({ruta.stat().st_size / 1_000_000:.2f} MB)\n")
    inicio = time.perf_counter()
    try:
        texto = transcribir_foto(ruta.read_bytes(), cliente=cliente)
    except (ImagenInvalida, ErrorTranscripcion) as error:
        print(f"No se pudo leer la foto: {error}", file=sys.stderr)
        return 1
    lectura = time.perf_counter() - inicio
    uso = cliente.ultimo_uso or {}
    print(f"Lectura ({lectura:.2f} s · tokens entrada: {uso.get('tokens_entrada')} · salida: {uso.get('tokens_salida')}):")
    print(texto or "(sin texto)")
    if postit:
        print()
        comparar_lectura(postit["texto"], texto)
    if args.solo_lectura:
        return 0

    inicio = time.perf_counter()
    try:
        observaciones = separar(
            texto, conjunto["fecha_captura"], _leer(RUTA_NOMBRES)["nombres_curso"], _leer(RUTA_CATALOGO), cliente=cliente
        )
    except ErrorSeparacion as error:
        print(f"Error de separación: {error}", file=sys.stderr)
        return 1
    print(f"\nSeparación ({time.perf_counter() - inicio:.2f} s):")
    print(json.dumps(observaciones, ensure_ascii=False, indent=2))
    if postit:
        print(f"\nComparación con lo esperado ({postit['caso']}):")
        comparar(postit["esperado"], observaciones)
    return 0


if __name__ == "__main__":
    sys.exit(main())
