"""Mide la separación de notas contra Bedrock real (PLAN.md, Task 10).

    python manage.py evaluar                                  # modelo de BEDROCK_MODEL_ID (o Sonnet 5), las 20 notas
    python manage.py evaluar --modelo sonnet --modelo haiku   # compara modelos lado a lado
    python manage.py evaluar --ids n01 n04 --detalle          # algunas notas, con lo que no calzó
    python manage.py evaluar --json resultados.json           # guarda lo obtenido y las métricas
    python manage.py evaluar --fuente audio                   # los audios de datos/eval/audios/ con Transcribe

Usa el set `datos/eval/notas_separacion.json` y los niños de `datos/demo_curso.json`
(nombres y alias, sin tocar la base de datos). Cada nota pasa por `separar()` y luego
por `coincidencia.emparejar()`, igual que en `procesamiento.py`. Las métricas están en
`registro/evaluacion.py`.

Con `--fuente audio`, cada audio (generado con `manage.py generar_audios`) se
transcribe primero con `ClienteTranscribe`, con los nombres del curso como
vocabulario, igual que un audio de la app (Task 9). Se transcribe una sola vez y
el texto se separa con cada modelo pedido. Necesita `KIMUN_BUCKET` (o `--bucket`).

Faltan las fotos (Task 8) y la propuesta de nivel (Task 7). Los tests pasan clientes
falsos con `call_command(..., crear_cliente=..., transcriptor=...)`.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from registro.curriculo import leer_curriculo
from registro.evaluacion import (
    ALIAS_MODELOS, ResultadoNota, asignar_ninos, diferencias, emparejar_observaciones, metricas_proteccion,
    metricas_separacion,
    ninos_del_curso,
)
from registro.ia import (
    ClienteBedrock, ClienteTranscribe, ErrorSeparacion, ErrorTranscripcion, separar, separar_completo,
)
from registro.management.commands.generar_audios import CARPETA_AUDIOS, texto_a_dictar
from registro.procesamiento import frases_del_curso

RUTA_SET = Path(settings.DATOS_DIR) / "eval" / "notas_separacion.json"
RUTA_DEMO = Path(settings.DATOS_DIR) / "demo_curso.json"
# Task 13: notas que deben (o no) marcarse como posible vulneración de derechos.
RUTA_SET_PROTECCION = Path(settings.DATOS_DIR) / "eval" / "notas_proteccion.json"
# Nombre base del vocabulario de Transcribe de la evaluación (los permisos del rol exigen "kimun-*").
PREFIJO_VOCABULARIO = "kimun-eval"
# Transcribe tarda unos 10-30 s por audio; se transcriben varios a la vez.
TRANSCRIPCIONES_EN_PARALELO = 8


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
    filas = [
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
    ]
    palabras, seg_tr = m["errores_palabras"], m["segundos_transcripcion"]
    if palabras is not None or seg_tr is not None:
        tasa = palabras and palabras["tasa_error"]
        filas += [
            ("Error de palabras (Transcribe)",
             "–" if tasa is None else f"{palabras['ediciones']}/{palabras['palabras']} ({tasa * 100:.0f} %)"),
            ("Segundos de transcripción: mediana", _numero(seg_tr and seg_tr["mediana"])),
        ]
    filas += [
        ("Segundos por nota: media", _numero(seg and seg["media"])),
        ("Segundos por nota: mediana", _numero(seg and seg["mediana"])),
        ("Segundos por nota: máximo", _numero(seg and seg["maximo"])),
        ("Tokens de entrada por nota", _numero(ent and ent["media"], 0)),
        ("Tokens de salida por nota", _numero(sal and sal["media"], 0)),
        ("USD de Bedrock por nota", _numero(costo and costo["media"], 4)),
        ("USD de Bedrock por 1.000 notas", _numero(costo and costo["media"] * 1000, 2)),
    ]
    return filas


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
    stealth_options = ("crear_cliente", "transcriptor")

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
        parser.add_argument(
            "--fuente", choices=("texto", "audio"), default="texto",
            help="texto: la nota escrita. audio: el audio de la nota, transcrito con Transcribe.",
        )
        parser.add_argument("--audios", default=str(CARPETA_AUDIOS), help="Carpeta con <id>.mp3 (--fuente audio).")
        parser.add_argument("--bucket", help="Bucket de Transcribe (--fuente audio). Por defecto, KIMUN_BUCKET.")
        parser.add_argument(
            "--proteccion", action="store_true",
            help="Corre el set de la Task 13 (datos/eval/notas_proteccion.json): cuántas notas se marcan como posible vulneración.",
        )

    def handle(self, *args, modelos, ids, detalle, ruta_json, ruta_set, fuente, audios, bucket, proteccion=False, **opciones):
        self.verbosity = opciones.get("verbosity", 1)
        crear_cliente = opciones.get("crear_cliente") or (lambda modelo: ClienteBedrock(modelo=modelo))
        if proteccion:
            return self._proteccion(crear_cliente, modelos)
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

        transcritas = {}
        if fuente == "audio":
            transcriptor = opciones.get("transcriptor") or ClienteTranscribe(bucket=bucket)
            transcritas = self._transcribir(notas, Path(audios), ninos, transcriptor)

        por_modelo = {}
        for pedido in modelos:
            cliente = crear_cliente(pedido)
            modelo = getattr(cliente, "modelo", pedido) or "modelo"
            self.stdout.write(f"Evaluando {modelo} con {len(notas)} notas ({fuente})…")
            resultados = [
                self._evaluar_nota(nota, cliente, ninos, catalogo, transcritas.get(nota["id"])) for nota in notas
            ]
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
                " (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY y AWS_SESSION_TOKEN), el acceso al modelo"
                " y, con audios, el bucket."
            )

    def _transcribir(self, notas, carpeta, ninos, transcriptor):
        """{id: {"texto", "segundos", "error"}}. Transcribe cada audio una vez, varios a la vez."""
        faltan = [n["id"] for n in notas if not (carpeta / f"{n['id']}.mp3").exists()]
        if faltan:
            raise CommandError(
                f"Faltan audios en {carpeta}: {', '.join(faltan)}. Generarlos con `manage.py generar_audios`."
            )
        frases = frases_del_curso(ninos)
        vocabulario = transcriptor.asegurar_vocabulario(PREFIJO_VOCABULARIO, frases)
        self.stdout.write(
            f"Vocabulario de nombres: {vocabulario}" if vocabulario
            else "Vocabulario de nombres: todavía no está listo (se creó o se está creando); se transcribe sin él."
        )

        def transcribir(nota):
            inicio = time.perf_counter()
            try:
                texto = transcriptor.transcribir(
                    (carpeta / f"{nota['id']}.mp3").read_bytes(),
                    id_trabajo=f"kimun-eval-{nota['id']}",
                    prefijo_vocabulario=PREFIJO_VOCABULARIO,
                    frases=frases,
                )
            except ErrorTranscripcion as error:
                return nota["id"], {"texto": None, "segundos": None, "error": str(error)}
            return nota["id"], {"texto": texto, "segundos": time.perf_counter() - inicio, "error": None}

        self.stdout.write(f"Transcribiendo {len(notas)} audios…")
        with ThreadPoolExecutor(max_workers=TRANSCRIPCIONES_EN_PARALELO) as hilos:
            transcritas = dict(hilos.map(transcribir, notas))
        for id_nota, t in transcritas.items():
            if t["error"]:
                self.stderr.write(f"  {id_nota}: error de transcripción: {t['error']}")
            elif self.verbosity >= 2:
                self.stdout.write(f"  {id_nota}: {t['texto']}")
        return transcritas

    def _evaluar_nota(self, nota, cliente, ninos, catalogo, transcrita=None):
        resultado = ResultadoNota(id=nota["id"], esperadas=nota["esperado"])
        texto, segundos_previos = nota["texto"], 0.0
        if transcrita is not None:
            resultado.texto_dictado = texto_a_dictar(nota)
            resultado.transcripcion = transcrita["texto"]
            resultado.segundos_transcripcion = transcrita["segundos"]
            if transcrita["error"]:
                resultado.error = transcrita["error"]
                return resultado
            texto, segundos_previos = transcrita["texto"], transcrita["segundos"]
        inicio = time.perf_counter()
        try:
            separadas = separar(texto, nota["fecha_captura"], [n.nombre for n in ninos], catalogo, cliente=cliente)
        except ErrorSeparacion as error:
            resultado.error = str(error)
            self.stderr.write(f"  {nota['id']}: error: {error}")
            return resultado
        resultado.segundos = segundos_previos + time.perf_counter() - inicio
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
                self.stdout.write(f"  {r.id}: error ({r.error})")
                continue
            pares, faltantes, de_mas = emparejar_observaciones(r.esperadas, r.obtenidas)
            lineas = [f"falta la observación de {e.get('nombre_detectado') or '(grupal)'}" for e in faltantes]
            lineas += [f"sobra la observación de {o.get('nombre_detectado') or '(grupal)'}" for o in de_mas]
            for esperada, obtenida in pares:
                quien = esperada.get("nombre_detectado") or "(grupal)"
                for campo, (esp, obt) in diferencias(esperada, obtenida).items():
                    lineas.append(f"{quien}: {campo} esperado {esp}, obtenido {obt}")
            if lineas and r.transcripcion is not None:
                lineas.insert(0, f"transcripción: {r.transcripcion}")
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


    def _proteccion(self, crear_cliente, modelos):
        """Task 13: corre `datos/eval/notas_proteccion.json` y cuenta lo marcado (sin escribir el texto de las notas)."""
        notas = _leer(RUTA_SET_PROTECCION)["notas"]
        nombres = [n["nombre"] for n in _leer(RUTA_DEMO)["ninos"]]
        catalogo = leer_curriculo()
        for pedido in [ALIAS_MODELOS.get(m, m) for m in modelos] if modelos else [None]:
            cliente = crear_cliente(pedido)
            pares = []
            for nota in notas:
                try:
                    senal = separar_completo(nota["texto"], nota["fecha_captura"], nombres, catalogo, cliente=cliente).senal
                except ErrorSeparacion as error:
                    self.stderr.write(f"{nota['id']}: error: {error}")
                    senal = None
                pares.append((nota, senal))
                esperado = "marcar" if nota["marcar"] else "no marcar"
                obtenido = f"marcada ({senal})" if senal else "no marcada"
                self.stdout.write(f"{nota['id']} ({esperado}): {obtenido}")
            m = metricas_proteccion(pares)
            modelo = getattr(cliente, "modelo", pedido) or "modelo"
            self.stdout.write(
                f"{modelo}: positivas marcadas {m['positivas_marcadas'].aciertos}/{m['positivas_marcadas'].total} (meta: todas), "
                f"negativas marcadas por error {m['negativas_marcadas'].aciertos}/{m['negativas_marcadas'].total}"
            )
