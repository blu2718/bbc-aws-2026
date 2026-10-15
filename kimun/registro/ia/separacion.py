"""Separación de una nota en observaciones, una por niño.

Funciones puras: no dependen de Django ni de `registro.models`. El catálogo de
núcleos y OA llega por parámetro (con la forma de `datos/curriculo_transicion.json`),
así que la cantidad de núcleos y de OA sale de los datos y no del código.

El emparejamiento de `nombre_detectado` con los niños del curso no se hace aquí.
"""

import json
import logging
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

from .bedrock import ClienteBedrock, ErrorBedrock

logger = logging.getLogger(__name__)

RUTA_PROMPT = Path(__file__).resolve().parent / "prompts" / "separacion.md"
NOMBRE_HERRAMIENTA = "registrar_observaciones"
# Escala de apoyo del Programa Pedagógico de Transición (igual que `registro.models.Apoyo`).
ESCALA_APOYO = ("autonomo", "con_ayuda", "parcial", "no_lo_realiza", "sin_dato")
SIN_DATO = "sin_dato"

# "OA", número y sigla (empieza con letra; puede traer dígitos si el catálogo los usa).
_PATRON_OA = re.compile(r"^\s*OA\W*0*(\d+)\W*([^\W\d_][^\W_]*)\s*$", re.IGNORECASE)


class ErrorSeparacion(Exception):
    """La respuesta del modelo no se pudo usar. La captura debe quedar con error y poder reintentarse."""


def normalizar_codigo_oa(codigo):
    """'OA4 LV', 'oa 4 lv', 'OA 04 LV' -> 'OA 4 LV'. None si no tiene forma de código de OA."""
    if not isinstance(codigo, str):
        return None
    m = _PATRON_OA.match(codigo)
    if not m:
        return None
    return f"OA {int(m.group(1))} {m.group(2).upper()}"


def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _clave_literal(codigo):
    """Código tal como viene, sin diferencias de mayúsculas ni de espacios."""
    return " ".join(codigo.split()).upper() if isinstance(codigo, str) else None


def _codigo_oa(oa, sigla):
    """Código con que se muestra el OA al modelo: normalizado si se puede; si no, el del catálogo."""
    literal = _texto_o_none(oa.get("codigo"))
    if literal is None and oa.get("numero") is not None:
        literal = f"OA {oa['numero']} {sigla}"
    return normalizar_codigo_oa(literal) or literal


def _claves(codigo):
    """Claves de búsqueda de un código: normalizada ('OA 4 LV') y literal."""
    claves = []
    for clave in (normalizar_codigo_oa(codigo), _clave_literal(codigo)):
        if clave and clave not in claves:
            claves.append(clave)
    return claves


def _oas_con_codigo(catalogo):
    """[(sigla, oa, código)] de todos los OA, en el orden del catálogo.

    Si un mismo código aparece en más de un núcleo (por ejemplo "OA 1" sin sigla), se
    le agrega la sigla del núcleo ("OA 1 IA"). Así el modelo y el backend saben a qué
    núcleo pertenece cada OA. Los códigos que no se repiten quedan como en el catálogo.
    """
    filas = []
    for nucleo in catalogo["nucleos"]:
        for oa in nucleo.get("oas", []):
            filas.append((nucleo["sigla"], oa, _codigo_oa(oa, nucleo["sigla"])))
    nucleos_por_codigo = {}
    for sigla, _, codigo in filas:
        if codigo is not None:
            nucleos_por_codigo.setdefault(_clave_literal(codigo), set()).add(sigla)
    return [
        (sigla, oa, f"{codigo} {sigla}" if codigo is not None and len(nucleos_por_codigo[_clave_literal(codigo)]) > 1 else codigo)
        for sigla, oa, codigo in filas
    ]


def indexar_catalogo(catalogo):
    """Devuelve ({SIGLA en mayúsculas: sigla}, {(SIGLA, clave de código): (código, sigla del núcleo)}).

    Los OA se indexan por núcleo y código, porque un catálogo puede repetir el mismo
    código en varios núcleos. Cada OA queda con su código normalizado ('OA 4 LV') y su
    código literal como claves, así un catálogo con otro formato ('IA-OA1') también se valida.
    """
    nucleos = {n["sigla"].upper(): n["sigla"] for n in catalogo["nucleos"]}
    oas = {}
    for sigla, oa, codigo in _oas_con_codigo(catalogo):
        if codigo is None:
            logger.warning("OA sin código ni número en el núcleo %s, no se puede indexar: %r", sigla, oa)
            continue
        if normalizar_codigo_oa(codigo) is None:
            logger.info("OA %r de %s no tiene la forma 'OA <n> <sigla>'; se valida por su código literal", codigo, sigla)
        for clave in _claves(codigo) + _claves(oa.get("codigo")):
            oas.setdefault((sigla.upper(), clave), (codigo, sigla))
    return nucleos, oas


def _buscar_oa(codigo, oas_catalogo, siglas_observacion):
    """OA del catálogo que pueden corresponder a `codigo`: lista de (código, sigla).

    Si el código existe en varios núcleos, se queda con los de los núcleos que el modelo
    puso en la observación. Más de un resultado significa que no se pudo decidir.
    """
    claves = _claves(codigo)
    candidatos = []
    for (_, clave), encontrado in oas_catalogo.items():
        if clave in claves and encontrado not in candidatos:
            candidatos.append(encontrado)
    if len(candidatos) > 1:
        siglas = {sigla.upper() for sigla in siglas_observacion}
        filtrados = [c for c in candidatos if c[1].upper() in siglas]
        if filtrados:
            return filtrados
    return candidatos


def texto_catalogo(catalogo):
    """Núcleos (sigla y nombre) y OA (código y texto), sin conductas."""
    por_nucleo = {}
    for sigla, oa, codigo in _oas_con_codigo(catalogo):
        if codigo is not None:
            por_nucleo.setdefault(sigla, []).append(f"- {codigo}: {oa['texto']}")
    lineas = ["### Núcleos", ""]
    lineas += [f"- {n['sigla']}: {n['nombre']}" for n in catalogo["nucleos"]]
    for n in catalogo["nucleos"]:
        lineas += ["", f"### OA de {n['sigla']} ({n['nombre']})", ""]
        lineas += por_nucleo.get(n["sigla"]) or ["- (sin OA en el catálogo)"]
    return "\n".join(lineas)


def construir_prompt(fecha_captura, nombres_curso, catalogo):
    nombres = "\n".join(f"  - {nombre}" for nombre in nombres_curso) or "  - (sin lista)"
    return (
        RUTA_PROMPT.read_text(encoding="utf-8")
        .replace("{{fecha_captura}}", _como_fecha(fecha_captura).isoformat())
        .replace("{{nombres_curso}}", nombres)
        .replace("{{catalogo}}", texto_catalogo(catalogo))
    )


def construir_mensaje(texto):
    return f"Nota a separar:\n\n<nota>\n{texto.strip()}\n</nota>"


def construir_herramienta(catalogo):
    """toolSpec de Converse. Las siglas salen del catálogo; los OA se validan en código."""
    siglas = [n["sigla"] for n in catalogo["nucleos"]]
    texto_o_nulo = {"type": ["string", "null"]}
    observacion = {
        "type": "object",
        "properties": {
            "nombre_detectado": {**texto_o_nulo, "description": "Nombre tal como está escrito en la nota; null si es grupal."},
            "fecha": {"type": "string", "description": "Fecha de lo observado, AAAA-MM-DD."},
            "cita_literal": {"type": "string", "description": "Fragmento textual de la nota sobre este niño."},
            "interpretacion": {**texto_o_nulo, "description": "Valoración de quien escribió la nota, o null."},
            "nucleos": {"type": "array", "items": {"type": "string", "enum": siglas}},
            "oas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Códigos de OA exactamente como aparecen en el catálogo.",
            },
            "apoyo": {"type": "string", "enum": list(ESCALA_APOYO)},
            "grupal": {"type": "boolean", "description": "true si la nota es sobre el grupo completo."},
        },
        "required": ["nombre_detectado", "fecha", "cita_literal", "interpretacion", "nucleos", "oas", "apoyo", "grupal"],
    }
    return {
        "name": NOMBRE_HERRAMIENTA,
        "description": "Registra las observaciones separadas de la nota, una por niño (o una grupal).",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {"observaciones": {"type": "array", "items": observacion}},
                "required": ["observaciones"],
            }
        },
    }


def _como_fecha(valor):
    # datetime es subclase de date: se deja solo la fecha para poder comparar y serializar.
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor).strip())


def _texto_o_none(valor):
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    return None


def _como_lista(valor):
    if valor is None:
        return []
    if isinstance(valor, str):
        return [valor]
    if isinstance(valor, list):
        return valor
    return []


def _como_bool(valor):
    if isinstance(valor, str):
        return valor.strip().lower() in ("true", "si", "sí")
    return valor is True


def _apoyo(valor, posicion):
    if isinstance(valor, str):
        normalizado = _sin_tildes(valor).strip().lower().replace(" ", "_")
        if normalizado in ESCALA_APOYO:
            return normalizado
    logger.info("Observación %s: apoyo %r fuera de la escala, se usa %s", posicion, valor, SIN_DATO)
    return SIN_DATO


def _fecha(valor, fecha_captura, posicion):
    if valor in (None, ""):
        return fecha_captura
    try:
        fecha = _como_fecha(valor)
    except ValueError:
        logger.info("Observación %s: fecha %r inválida, se usa la de captura", posicion, valor)
        return fecha_captura
    if fecha > fecha_captura:
        logger.info("Observación %s: fecha %s posterior a la captura, se usa la de captura", posicion, fecha)
        return fecha_captura
    return fecha


def _extraer_observaciones(entrada):
    if isinstance(entrada, str):
        try:
            entrada = json.loads(entrada)
        except ValueError as error:
            raise ErrorSeparacion(f"La respuesta no es JSON válido: {error}") from error
    if not isinstance(entrada, dict):
        raise ErrorSeparacion(f"La respuesta no es un objeto JSON: {type(entrada).__name__}")
    observaciones = entrada.get("observaciones")
    # A veces el modelo entrega la lista serializada como texto.
    if isinstance(observaciones, str):
        try:
            observaciones = json.loads(observaciones)
        except ValueError as error:
            raise ErrorSeparacion(f"'observaciones' no es JSON válido: {error}") from error
    # Y a veces ese texto trae el objeto completo, {"observaciones": [...]}, en vez de solo la lista.
    if isinstance(observaciones, dict) and "observaciones" in observaciones:
        observaciones = observaciones["observaciones"]
    if not isinstance(observaciones, list):
        raise ErrorSeparacion("La respuesta no trae la lista 'observaciones'.")
    return observaciones


def _normalizar(cruda, posicion, nucleos_catalogo, oas_catalogo, fecha_captura):
    """Valida una observación. Devuelve None (y lo registra) si está incompleta."""
    if not isinstance(cruda, dict):
        logger.warning("Observación %s descartada: no es un objeto (%r)", posicion, cruda)
        return None
    cita = _texto_o_none(cruda.get("cita_literal"))
    if cita is None:
        logger.warning("Observación %s descartada: no trae cita_literal", posicion)
        return None

    nucleos = []
    for sigla in _como_lista(cruda.get("nucleos")):
        canonica = nucleos_catalogo.get(sigla.strip().upper()) if isinstance(sigla, str) else None
        if canonica is None:
            logger.warning("Observación %s: núcleo %r no existe en el catálogo, se descarta", posicion, sigla)
        elif canonica not in nucleos:
            nucleos.append(canonica)

    oas = []
    siglas_del_modelo = list(nucleos)
    for codigo in _como_lista(cruda.get("oas")):
        candidatos = _buscar_oa(codigo, oas_catalogo, siglas_del_modelo)
        if not candidatos:
            logger.warning("Observación %s: OA %r no existe en el catálogo, se descarta", posicion, codigo)
            continue
        if len(candidatos) > 1:
            logger.warning(
                "Observación %s: OA %r existe en varios núcleos (%s) y la observación no indica cuál, se descarta",
                posicion, codigo, ", ".join(sigla for _, sigla in candidatos),
            )
            continue
        canonico, sigla_oa = candidatos[0]
        if canonico not in oas:
            oas.append(canonico)
        if sigla_oa not in nucleos:
            nucleos.append(sigla_oa)

    grupal = _como_bool(cruda.get("grupal"))
    observacion = {
        "nombre_detectado": _texto_o_none(cruda.get("nombre_detectado")),
        "fecha": _fecha(cruda.get("fecha"), fecha_captura, posicion).isoformat(),
        "cita_literal": cita,
        "interpretacion": _texto_o_none(cruda.get("interpretacion")),
        "nucleos": nucleos,
        "oas": oas,
        "apoyo": _apoyo(cruda.get("apoyo"), posicion),
        "grupal": grupal,
    }
    if grupal:
        # Contexto del curso: no se asigna a un niño ni se usa para evaluar.
        observacion.update(nombre_detectado=None, oas=[], apoyo=SIN_DATO)
    return observacion


def separar(texto, fecha_captura, nombres_curso, catalogo, cliente=None):
    """Separa `texto` en observaciones validadas contra `catalogo`.

    `fecha_captura` es un `date`, un texto AAAA-MM-DD o un `datetime` (se usa solo su
    fecha, sin convertir de zona). Desde el backend conviene pasar la fecha local,
    p. ej. `timezone.localdate(captura.creada)`, para que "ayer" se resuelva bien.
    `cliente` es cualquier objeto con `invocar_herramienta(system, mensaje, herramienta)`;
    por defecto, `ClienteBedrock()`. Lanza ErrorSeparacion si la respuesta no sirve.
    """
    if not texto or not texto.strip():
        return []
    fecha_captura = _como_fecha(fecha_captura)
    nucleos_catalogo, oas_catalogo = indexar_catalogo(catalogo)
    system = construir_prompt(fecha_captura, nombres_curso, catalogo)
    herramienta = construir_herramienta(catalogo)
    if cliente is None:
        cliente = ClienteBedrock()
    try:
        entrada = cliente.invocar_herramienta(system, construir_mensaje(texto), herramienta)
    except ErrorBedrock as error:
        raise ErrorSeparacion(str(error)) from error

    observaciones = []
    for posicion, cruda in enumerate(_extraer_observaciones(entrada), start=1):
        observacion = _normalizar(cruda, posicion, nucleos_catalogo, oas_catalogo, fecha_captura)
        if observacion is not None:
            observaciones.append(observacion)
    return observaciones
