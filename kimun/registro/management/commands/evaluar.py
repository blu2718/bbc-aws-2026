"""Mide la separación de notas contra Bedrock real (PLAN.md, Task 10).

    python manage.py evaluar                                  # modelo de BEDROCK_MODEL_ID (o Sonnet 5), las 20 notas
    python manage.py evaluar --modelo sonnet --modelo haiku   # compara modelos lado a lado
    python manage.py evaluar --ids n01 n04 --detalle          # algunas notas, con lo que no calzó
    python manage.py evaluar --json resultados.json           # guarda lo obtenido y las métricas

Usa el set `datos/eval/notas_separacion.json` y los niños de `datos/demo_curso.json`
(nombres y alias, sin tocar la base de datos). Cada nota pasa por `separar()` y luego
por `coincidencia.emparejar()`, igual que en `procesamiento.py`. Las métricas están en
`registro/evaluacion.py`.

Hoy mide solo notas de texto: las fotos (Task 8), los audios (Task 9) y la propuesta
de nivel (Task 7) se suman cuando existan. Los tests pasan clientes falsos con
`call_command(..., crear_cliente=...)`.
"""
import json
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from registro.curriculo import leer_curriculo
from registro.evaluacion import (
    ALIAS_MODELOS, ResultadoNota, asignar_ninos, diferencias, emparejar_observaciones, metricas_separacion,
    ninos_del_curso,
)
from registro.ia import ClienteBedrock, ErrorSeparacion, separar

RUTA_SET = Path(settings.DATOS_DIR) / "eval" / "notas_separacion.json"
RUTA_DEMO = Path(settings.DATOS_DIR) / "demo_curso.json"


def _leer(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _porcentaje(p):
    if p.valor is None:
        return "–"
    return f"{p.aciertos}/{p.total} ({p.valor * 100:.0f} %)"


def _numero(valor, decimales=1):
    return "–" if valor is None else f"{valor:,.{decimales}f}".replace(",", " ").replace(".", ",")


def _filas(m):
    """[(etiqueta, texto)] de las métricas de un modelo, en el orden de la tabla."""
    seg, ent, sal, costo = m["segundos"], m["tokens_entrada"], m["tokens_salida"], m["costo_usd"]
    return [
        ("Notas evaluadas (con error)", f"{m['notas']} ({m['notas_con_error']})"),
        ("Observaciones encontradas", _porcentaje(m["observaciones"])),
        ("Observaciones de más", str(m["observaciones_de_mas"])),
        ("Niños bien asignados", _porcentaje(m["ninos"])),
        ("Núcleos: precisión", _porcentaje(m["nucleos"].precision)),
        ("Núcleos: cobertura", _porcentaje(m["nucleos"].cobertura)),
        ("OA: precisión", _porcentaje(m["oas"].precision)),
        ("OA: cobertura", _porcentaje(m["oas"].cobertura)),
        ("Nivel de apoyo correcto", _porcentaje(m["apoyo"])),
        ("Fecha correcta", _porcentaje(m["fecha"])),
        ("Interpretación separada", _porcentaje(m["interpretacion"])),
        ("Segundos por nota: media", _numero(seg and seg["media"])),
        ("Segundos por nota: mediana", _numero(seg and seg["mediana"])),
        ("Segundos por nota: máximo", _numero(seg and seg["maximo"])),
        ("Tokens de entrada por nota", _numero(ent and ent["media"], 0)),
        ("Tokens de salida por nota", _numero(sal and sal["media"], 0)),
        ("USD por nota", _numero(costo and costo["media"], 4)),
        ("USD por 1.000 notas", _numero(costo and costo["media"] * 1000, 2)),
    ]


def _como_json(valor):
    """Serializa Proporcion y Conteo para --json."""
    if hasattr(valor, "precision"):
        return {
            "correctas": valor.correctas, "sobrantes": valor.sobrantes, "faltantes": valor.faltantes,
            "precision": valor.precision.valor, "cobertura": valor.cobertura.valor,
        }
    if hasattr(valor, "aciertos"):
        return {"aciertos": valor.aciertos, "total": valor.total, "valor": valor.valor}
    raise TypeError(type(valor).__name__)


class Command(BaseCommand):
    help = "Mide la separación de notas en observaciones contra Bedrock real, con el set de datos/eval/."
    stealth_options = ("crear_cliente",)

    def add_arguments(self, parser):
        parser.add_argument(
            "--modelo", action="append", dest="modelos", metavar="MODELO",
            help=(
                "ID del modelo o perfil de inferencia, o un alias: "
                + ", ".join(ALIAS_MODELOS)
                + ". Se puede repetir para comparar. Por defecto, BEDROCK_MODEL_ID o Sonnet 5."
            ),
        )
        parser.add_argument("--ids", nargs="+", metavar="ID", help="Solo estas notas del set (p. ej. n01 n04).")
        parser.add_argument("--detalle", action="store_true", help="Muestra, por nota, lo que no calzó.")
        parser.add_argument("--json", dest="ruta_json", metavar="RUTA", help="Guarda lo obtenido y las métricas.")
        parser.add_argument("--set", dest="ruta_set", default=str(RUTA_SET), help="Set de notas a usar.")

    def handle(self, *args, modelos, ids, detalle, ruta_json, ruta_set, **opciones):
        self.verbosity = opciones.get("verbosity", 1)
        crear_cliente = opciones.get("crear_cliente") or (lambda modelo: ClienteBedrock(modelo=modelo))
        conjunto = _leer(ruta_set)
        notas = conjunto["notas"]
        if ids:
            desconocidas = sorted(set(ids) - {n["id"] for n in notas})
            if desconocidas:
                raise CommandError(f"No existen en el set: {', '.join(desconocidas)}")
            notas = [n for n in notas if n["id"] in ids]
        ninos = ninos_del_curso(_leer(RUTA_DEMO))
        catalogo = leer_curriculo()
        modelos = [ALIAS_MODELOS.get(m, m) for m in modelos] if modelos else [None]

        por_modelo = {}
        for pedido in modelos:
            cliente = crear_cliente(pedido)
            modelo = getattr(cliente, "modelo", pedido) or "modelo"
            self.stdout.write(f"Evaluando {modelo} con {len(notas)} notas…")
            resultados = [self._evaluar_nota(nota, cliente, ninos, catalogo) for nota in notas]
            por_modelo[modelo] = (resultados, metricas_separacion(resultados, modelo=modelo))
            if detalle:
                self._detalle(resultados)

        self._tabla(por_modelo)
        if ruta_json:
            self._guardar(ruta_json, por_modelo)
        fallidos = [modelo for modelo, (_, m) in por_modelo.items() if m["notas"] and m["notas_con_error"] == m["notas"]]
        if fallidos:
            raise CommandError(
                f"Todas las notas fallaron con {', '.join(fallidos)}. Revisar las credenciales de AWS"
                " (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY y AWS_SESSION_TOKEN) y el acceso al modelo."
            )

    def _evaluar_nota(self, nota, cliente, ninos, catalogo):
        resultado = ResultadoNota(id=nota["id"], esperadas=nota["esperado"])
        inicio = time.perf_counter()
        try:
            separadas = separar(nota["texto"], nota["fecha_captura"], [n.nombre for n in ninos], catalogo, cliente=cliente)
        except ErrorSeparacion as error:
            resultado.error = str(error)
            self.stderr.write(f"  {nota['id']}: error: {error}")
            return resultado
        resultado.segundos = time.perf_counter() - inicio
        resultado.obtenidas = asignar_ninos(separadas, ninos)
        uso = getattr(cliente, "ultimo_uso", None) or {}
        resultado.tokens_entrada = uso.get("tokens_entrada")
        resultado.tokens_salida = uso.get("tokens_salida")
        if self.verbosity >= 2:
            self.stdout.write(f"  {nota['id']}: {len(separadas)} observaciones en {resultado.segundos:.1f} s")
        return resultado

    def _detalle(self, resultados):
        for r in resultados:
            if r.error:
                self.stdout.write(f"  {r.id}: error de Bedrock")
                continue
            pares, faltantes, de_mas = emparejar_observaciones(r.esperadas, r.obtenidas)
            lineas = [f"falta la observación de {e.get('nombre_detectado') or '(grupal)'}" for e in faltantes]
            lineas += [f"sobra la observación de {o.get('nombre_detectado') or '(grupal)'}" for o in de_mas]
            for esperada, obtenida in pares:
                quien = esperada.get("nombre_detectado") or "(grupal)"
                for campo, (esp, obt) in diferencias(esperada, obtenida).items():
                    lineas.append(f"{quien}: {campo} esperado {esp}, obtenido {obt}")
            if lineas:
                self.stdout.write(f"  {r.id}:")
                for linea in lineas:
                    self.stdout.write(f"    - {linea}")

    def _tabla(self, por_modelo):
        columnas = {modelo: dict(_filas(m)) for modelo, (_, m) in por_modelo.items()}
        etiquetas = [etiqueta for etiqueta, _ in _filas(next(iter(por_modelo.values()))[1])]
        ancho = max(len(e) for e in etiquetas)
        anchos = {modelo: max(len(modelo), *(len(v) for v in valores.values())) for modelo, valores in columnas.items()}
        self.stdout.write("")
        self.stdout.write("  ".join([" " * ancho] + [modelo.ljust(anchos[modelo]) for modelo in columnas]))
        for etiqueta in etiquetas:
            celdas = [columnas[modelo][etiqueta].ljust(anchos[modelo]) for modelo in columnas]
            self.stdout.write("  ".join([etiqueta.ljust(ancho)] + celdas))

    def _guardar(self, ruta, por_modelo):
        salida = {
            modelo: {
                "metricas": metricas,
                "notas": [vars(r) for r in resultados],
            }
            for modelo, (resultados, metricas) in por_modelo.items()
        }
        Path(ruta).write_text(json.dumps(salida, ensure_ascii=False, indent=2, default=_como_json), encoding="utf-8")
        self.stdout.write(f"Resultados guardados en {ruta}")
