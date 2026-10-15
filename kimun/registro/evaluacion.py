"""Métricas de calidad del pipeline de IA (PLAN.md, Task 10).

Funciones puras: reciben lo esperado (`datos/eval/`) y lo obtenido, y no llaman a
Bedrock ni a la base de datos. `manage.py evaluar` las usa con Bedrock real; los
tests, con resultados conocidos.

Separación de notas (Task 5):

- Cada observación obtenida se empareja con una esperada por el nombre detectado
  (normalizado, sin tildes ni mayúsculas) o, si no calza, por el niño asignado.
  Las notas grupales se emparejan entre sí.
- Niños bien asignados: sobre todas las observaciones esperadas que no son
  grupales. Una observación que falta cuenta como mal asignada. Dejar sin niño un
  nombre ambiguo o desconocido es el resultado correcto (decide la educadora).
- Núcleos y OA: precisión y cobertura sumando etiquetas de todas las notas. Las
  etiquetas de una observación que falta cuentan como no encontradas, y las de
  una observación de más, como sobrantes.
- Apoyo, fecha e interpretación: solo sobre las observaciones encontradas, porque
  las que faltan ya restan arriba.
- Una nota con error de Bedrock (o de Transcribe) cuenta todas sus observaciones
  como faltantes y no entra en los tiempos.
- Audios (Task 9): además, la tasa de error de palabras entre lo dictado y lo que
  transcribió Transcribe, y los segundos de transcripción.

Propuesta de nivel (Task 7): `metricas_propuestas` y `casos_propuesta_ia` quedan
listas para cuando exista la propuesta.
"""
import re
from dataclasses import dataclass, field
from statistics import mean, median
from types import SimpleNamespace

from .coincidencia import emparejar, normalizar

# USD por millón de tokens (entrada, salida) en us-east-1. Fuente: docs/investigacion_servicios.md.
PRECIOS_POR_MILLON = {
    "us.anthropic.claude-sonnet-5": (2.20, 11.00),
    "us.anthropic.claude-haiku-4-5-20251001-v1:0": (1.10, 5.50),
}
# Nombres cortos para la línea de comandos.
ALIAS_MODELOS = {
    "sonnet": "us.anthropic.claude-sonnet-5",
    "haiku": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
}

# De los dos ejemplos de cada nivel de la rúbrica de Integra, el prompt de propuesta
# (Task 7) muestra uno al modelo y el otro se reserva para medir, para no evaluar con
# lo mismo que se le mostró. Este es el índice del reservado: la Task 7 usa el otro.
INDICE_EJEMPLO_RESERVADO = 1

CLAVE_GRUPAL = "(grupal)"


@dataclass(frozen=True)
class Proporcion:
    aciertos: int
    total: int

    @property
    def valor(self):
        """Entre 0 y 1; None si no hay casos."""
        return self.aciertos / self.total if self.total else None


@dataclass
class Conteo:
    """Etiquetas (núcleos u OA) bien puestas, de más y que faltaron."""

    correctas: int = 0
    sobrantes: int = 0
    faltantes: int = 0

    def sumar(self, esperadas, obtenidas):
        esperadas, obtenidas = set(esperadas), set(obtenidas)
        self.correctas += len(esperadas & obtenidas)
        self.sobrantes += len(obtenidas - esperadas)
        self.faltantes += len(esperadas - obtenidas)

    @property
    def precision(self):
        """De lo que puso el modelo, qué parte era correcta."""
        return Proporcion(self.correctas, self.correctas + self.sobrantes)

    @property
    def cobertura(self):
        """De lo esperado, qué parte encontró el modelo."""
        return Proporcion(self.correctas, self.correctas + self.faltantes)


@dataclass
class ResultadoNota:
    """Lo que pasó con una nota del set.

    `obtenidas` son las observaciones de `separar()` con la clave `nino` agregada
    (nombre completo del niño asignado o None); ver `asignar_ninos`.
    """

    id: str
    esperadas: list
    obtenidas: list = field(default_factory=list)
    # Tiempo total de la captura: transcripción (si es audio) más separación.
    segundos: float = None
    tokens_entrada: int = None
    tokens_salida: int = None
    error: str = None
    # Solo en audios: lo que se dictó, lo que entendió Transcribe y cuánto tardó.
    texto_dictado: str = None
    transcripcion: str = None
    segundos_transcripcion: float = None


def ninos_del_curso(demo):
    """Niños de `datos/demo_curso.json` como objetos con `nombre` y `alias`, igual que `Nino`."""
    return [SimpleNamespace(nombre=n["nombre"], alias=n.get("alias", [])) for n in demo["ninos"]]


def asignar_ninos(observaciones, ninos, umbral=None):
    """Copia de `observaciones` con `nino`: el nombre del niño que asigna `coincidencia.emparejar`.

    Las grupales quedan sin niño, igual que en `procesamiento.py`.
    """
    asignadas = []
    for obs in observaciones:
        nino = None
        if not obs.get("grupal"):
            nino = emparejar(obs.get("nombre_detectado") or "", ninos, umbral=umbral).nino
        asignadas.append({**obs, "nino": nino.nombre if nino else None})
    return asignadas


def _clave(obs):
    return CLAVE_GRUPAL if obs.get("grupal") else normalizar(obs.get("nombre_detectado") or "")


def emparejar_observaciones(esperadas, obtenidas):
    """Devuelve (pares [(esperada, obtenida)], faltantes, sobrantes).

    Primero por nombre detectado normalizado (o por ser grupal) y después, para las
    que quedan, por el niño asignado. Así "Rubí" y "Rubi" se emparejan aunque el
    modelo haya cambiado la tilde.
    """
    libres = list(obtenidas)
    pares, sin_par = [], []
    for esperada in esperadas:
        obtenida = next((o for o in libres if _clave(o) == _clave(esperada)), None)
        if obtenida is None:
            sin_par.append(esperada)
        else:
            libres.remove(obtenida)
            pares.append((esperada, obtenida))
    faltantes = []
    for esperada in sin_par:
        nino = esperada.get("nino")
        obtenida = next((o for o in libres if nino and not o.get("grupal") and o.get("nino") == nino), None)
        if obtenida is None:
            faltantes.append(esperada)
        else:
            libres.remove(obtenida)
            pares.append((esperada, obtenida))
    return pares, faltantes, libres


def diferencias(esperada, obtenida):
    """Campos de la observación encontrada que no calzan: {campo: (esperado, obtenido)}."""
    difs = {}
    if not esperada.get("grupal") and esperada.get("nino") != obtenida.get("nino"):
        difs["nino"] = (esperada.get("nino"), obtenida.get("nino"))
    for campo in ("nucleos", "oas"):
        if set(esperada.get(campo, [])) != set(obtenida.get(campo, [])):
            difs[campo] = (sorted(esperada.get(campo, [])), sorted(obtenida.get(campo, [])))
    for campo in ("apoyo", "fecha"):
        if campo in esperada and esperada[campo] != obtenida.get(campo):
            difs[campo] = (esperada[campo], obtenida.get(campo))
    if "tiene_interpretacion" in esperada:
        tiene = obtenida.get("interpretacion") is not None
        if tiene != esperada["tiene_interpretacion"]:
            difs["interpretacion"] = (esperada["tiene_interpretacion"], tiene)
    return difs


def _palabras(texto):
    """Palabras sin tildes, mayúsculas ni puntuación: "¡Rubí, ven!" -> ["rubi", "ven"]."""
    return re.sub(r"[^\w\s]", " ", normalizar(texto)).split()


def errores_palabras(referencia, hipotesis):
    """(ediciones, palabras de la referencia) entre lo dictado y lo transcrito.

    Ediciones = palabras cambiadas, sobrantes o faltantes (distancia de Levenshtein por
    palabras). Ediciones / palabras es la tasa de error de palabras (WER).
    """
    ref, hip = _palabras(referencia), _palabras(hipotesis)
    previa = list(range(len(hip) + 1))
    for i, palabra in enumerate(ref, start=1):
        actual = [i]
        for j, otra in enumerate(hip, start=1):
            actual.append(min(previa[j] + 1, actual[j - 1] + 1, previa[j - 1] + (palabra != otra)))
        previa = actual
    return previa[-1], len(ref)


def costo_usd(modelo, tokens_entrada, tokens_salida):
    """Costo de una llamada en USD; None si no se conoce el precio del modelo o faltan tokens."""
    precio = PRECIOS_POR_MILLON.get(modelo)
    if precio is None or tokens_entrada is None or tokens_salida is None:
        return None
    return (tokens_entrada * precio[0] + tokens_salida * precio[1]) / 1_000_000


def _resumen(valores):
    valores = [v for v in valores if v is not None]
    if not valores:
        return None
    return {"media": mean(valores), "mediana": median(valores), "maximo": max(valores)}


def metricas_separacion(resultados, modelo=None):
    """Métricas sumadas sobre una lista de `ResultadoNota`. Ver el docstring del módulo."""
    observaciones = Proporcion(0, 0)
    ninos = apoyo = fecha = interpretacion = Proporcion(0, 0)
    nucleos, oas = Conteo(), Conteo()
    obtenidas = sobrantes = 0

    def mas(p, acierto):
        return Proporcion(p.aciertos + int(acierto), p.total + 1)

    for r in resultados:
        pares, faltantes, de_mas = emparejar_observaciones(r.esperadas, r.obtenidas)
        obtenidas += len(r.obtenidas)
        sobrantes += len(de_mas)
        observaciones = Proporcion(observaciones.aciertos + len(pares), observaciones.total + len(r.esperadas))
        for esperada, obtenida in pares:
            if not esperada.get("grupal"):
                ninos = mas(ninos, esperada.get("nino") == obtenida.get("nino"))
                apoyo = mas(apoyo, esperada.get("apoyo") == obtenida.get("apoyo"))
            nucleos.sumar(esperada.get("nucleos", []), obtenida.get("nucleos", []))
            oas.sumar(esperada.get("oas", []), obtenida.get("oas", []))
            if "fecha" in esperada:
                fecha = mas(fecha, esperada["fecha"] == obtenida.get("fecha"))
            if "tiene_interpretacion" in esperada:
                tiene = obtenida.get("interpretacion") is not None
                interpretacion = mas(interpretacion, tiene == esperada["tiene_interpretacion"])
        for esperada in faltantes:
            if not esperada.get("grupal"):
                ninos = mas(ninos, False)
            nucleos.sumar(esperada.get("nucleos", []), [])
            oas.sumar(esperada.get("oas", []), [])
        for obtenida in de_mas:
            nucleos.sumar([], obtenida.get("nucleos", []))
            oas.sumar([], obtenida.get("oas", []))

    sin_error = [r for r in resultados if r.error is None]
    costos = [costo_usd(modelo, r.tokens_entrada, r.tokens_salida) for r in sin_error]
    transcritas = [r for r in resultados if r.transcripcion is not None and r.texto_dictado]
    palabras = None
    if transcritas:
        ediciones, total = map(sum, zip(*(errores_palabras(r.texto_dictado, r.transcripcion) for r in transcritas)))
        palabras = {"ediciones": ediciones, "palabras": total, "tasa_error": ediciones / total if total else None}
    return {
        "notas": len(resultados),
        "notas_con_error": len(resultados) - len(sin_error),
        "observaciones": observaciones,
        "observaciones_obtenidas": obtenidas,
        "observaciones_de_mas": sobrantes,
        "ninos": ninos,
        "nucleos": nucleos,
        "oas": oas,
        "apoyo": apoyo,
        "fecha": fecha,
        "interpretacion": interpretacion,
        "segundos": _resumen([r.segundos for r in sin_error]),
        "tokens_entrada": _resumen([r.tokens_entrada for r in sin_error]),
        "tokens_salida": _resumen([r.tokens_salida for r in sin_error]),
        "costo_usd": _resumen(costos),
        # Solo en audios (None con notas de texto).
        "errores_palabras": palabras,
        "segundos_transcripcion": _resumen([r.segundos_transcripcion for r in resultados]),
    }


def metricas_propuestas(pares):
    """Propuesta de nivel frente al nivel esperado. `pares`: [(esperado, propuesto o None)].

    Un caso sin propuesta ("faltan observaciones") cuenta como fallo en las dos cifras.
    """
    pares = list(pares)
    con_propuesta = [(e, p) for e, p in pares if p is not None]
    return {
        "casos": len(pares),
        "sin_propuesta": len(pares) - len(con_propuesta),
        "exactas": Proporcion(sum(1 for e, p in con_propuesta if e == p), len(pares)),
        "a_un_nivel": Proporcion(sum(1 for e, p in con_propuesta if abs(e - p) <= 1), len(pares)),
        "error_medio": mean(abs(e - p) for e, p in con_propuesta) if con_propuesta else None,
    }


def casos_propuesta_ia(rubrica_integra, nivel_educativo="transicion", sigla="IA"):
    """Casos para medir la propuesta de nivel: el ejemplo reservado de cada nivel, con su nivel oficial.

    Devuelve [{"nivel", "nombre", "texto"}], uno por nivel del bloque de la rúbrica de Integra.
    """
    bloque = next(
        (b for b in rubrica_integra["rubricas"] if b["nivel_educativo"] == nivel_educativo and b["sigla"] == sigla),
        None,
    )
    if bloque is None:
        raise ValueError(f"La rúbrica de Integra no trae {sigla} para {nivel_educativo}.")
    return [
        {"nivel": n["nivel"], "nombre": n["nombre"], "texto": n["ejemplos"][INDICE_EJEMPLO_RESERVADO]}
        for n in bloque["niveles"]
    ]
