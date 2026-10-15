"""Separa una nota contra Bedrock real y muestra el resultado, la latencia y los tokens.

Se corre desde la raíz del repo con el entorno de kimun/:

    kimun/.venv/bin/python scripts/probar_separacion.py --id n04
    kimun/.venv/bin/python scripts/probar_separacion.py --texto "Pedro y Emilio clasificaron hojas por color" [--fecha 2026-05-25]

Con --id compara con el resultado esperado del set (datos/eval/notas_separacion.json).
El modelo sale de BEDROCK_MODEL_ID (o --modelo). No usa Django.
"""

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kimun"))

from registro.ia import ClienteBedrock, ErrorSeparacion, separar  # noqa: E402

RUTA_CATALOGO = RAIZ / "datos" / "curriculo_transicion.json"
RUTA_SET = RAIZ / "datos" / "eval" / "notas_separacion.json"
CAMPOS_COMPARADOS = ("nucleos", "oas", "apoyo", "grupal", "fecha")


def _leer(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))


def _clave(observacion):
    return "(grupal)" if observacion.get("grupal") else observacion.get("nombre_detectado")


def _igual(campo, esperado, obtenido):
    if campo in ("nucleos", "oas"):
        return set(esperado) == set(obtenido)
    return esperado == obtenido


def comparar(esperadas, obtenidas):
    """Empareja por nombre_detectado exacto (o por ser grupal) y compara campo a campo."""
    aciertos = total = 0
    pendientes = list(obtenidas)
    for esperada in esperadas:
        clave = _clave(esperada)
        obtenida = next((o for o in pendientes if _clave(o) == clave), None)
        total += 1
        if obtenida is None:
            print(f"  ✗ {clave}: falta la observación")
            continue
        pendientes.remove(obtenida)
        aciertos += 1
        print(f"  ✓ {clave}: observación encontrada")
        campos = [c for c in CAMPOS_COMPARADOS if c in esperada]
        if "tiene_interpretacion" in esperada:
            campos.append("tiene_interpretacion")
        for campo in campos:
            valor = obtenida["interpretacion"] is not None if campo == "tiene_interpretacion" else obtenida[campo]
            total += 1
            if _igual(campo, esperada[campo], valor):
                aciertos += 1
                print(f"      ✓ {campo}: {valor}")
            else:
                print(f"      ✗ {campo}: esperado {esperada[campo]}, obtenido {valor}")
    for sobrante in pendientes:
        total += 1
        print(f"  ✗ {_clave(sobrante)}: observación no esperada")
    print(f"  Aciertos: {aciertos}/{total}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--id", help="id de una nota del set (p. ej. n04)")
    grupo.add_argument("--texto", help="texto libre de una nota")
    parser.add_argument("--fecha", help="fecha de captura AAAA-MM-DD (por defecto la de la nota o hoy)")
    parser.add_argument("--modelo", help="ID del modelo o perfil de inferencia (por defecto BEDROCK_MODEL_ID)")
    args = parser.parse_args()

    catalogo = _leer(RUTA_CATALOGO)
    conjunto = _leer(RUTA_SET)
    nota = None
    if args.id:
        nota = next((n for n in conjunto["notas"] if n["id"] == args.id), None)
        if nota is None:
            parser.error(f"no existe la nota {args.id!r} en {RUTA_SET.relative_to(RAIZ)}")
        texto = nota["texto"]
    else:
        texto = args.texto
    fecha = args.fecha or (nota and nota["fecha_captura"]) or date.today().isoformat()

    cliente = ClienteBedrock(modelo=args.modelo)
    print(f"Modelo: {cliente.modelo} ({cliente.region})")
    print(f"Fecha de captura: {fecha}")
    print(f"Nota: {texto}\n")
    inicio = time.perf_counter()
    try:
        observaciones = separar(texto, fecha, conjunto["nombres_curso"], catalogo, cliente=cliente)
    except ErrorSeparacion as error:
        print(f"Error de separación: {error}", file=sys.stderr)
        return 1
    latencia = time.perf_counter() - inicio

    print(json.dumps(observaciones, ensure_ascii=False, indent=2))
    uso = cliente.ultimo_uso or {}
    print(
        f"\nLatencia total: {latencia:.2f} s (modelo: {uso.get('latencia_ms')} ms, intentos: {uso.get('intentos')})"
        f" · tokens entrada: {uso.get('tokens_entrada')} · salida: {uso.get('tokens_salida')}"
    )
    if nota:
        print(f"\nComparación con lo esperado ({nota['caso']}):")
        comparar(nota["esperado"], observaciones)
    return 0


if __name__ == "__main__":
    sys.exit(main())
