"""Prompt y validación de propuestas, sin Django ni acceso a la base de datos."""
from datetime import date
from pathlib import Path

from .bedrock import ClienteBedrock, ErrorBedrock
from .seudonimo import Seudonimizador

VERSION_PROMPT = "propuesta-v1"
RUTA_PROMPT = Path(__file__).resolve().parent / "prompts" / "propuesta.md"
CAMPOS = {"nivel", "evidencia_suficiente", "observaciones_citadas", "conductas_observadas", "justificacion"}
APOYOS = {"autonomo", "con_ayuda", "parcial", "no_lo_realiza", "sin_dato"}


class ErrorPropuesta(Exception):
    """No se puede usar la respuesta; los mensajes no incluyen citas ni respuestas crudas."""


class ErrorConfiguracionPropuesta(ErrorPropuesta):
    """Falta información para construir una propuesta fiel a la rúbrica."""


def leer_prompt():
    try:
        return RUTA_PROMPT.read_text(encoding="utf-8")
    except OSError:
        raise ErrorConfiguracionPropuesta("No se pudo leer el prompt de propuestas.") from None


def _texto(valor):
    return isinstance(valor, str) and bool(valor.strip())


def construir_contexto(datos):
    """Proyección explícita de datos: nunca incluye el diccionario de identidades."""
    rubricas = datos.get("rubrica", [])
    if not isinstance(rubricas, list) or len(rubricas) != 1:
        raise ErrorConfiguracionPropuesta("Debe existir una rúbrica para el nivel educativo.")
    maximo = rubricas[0].get("cantidad_niveles")
    if type(maximo) is not int or maximo < 2:
        raise ErrorConfiguracionPropuesta("La cantidad de niveles de la rúbrica no es válida.")
    referencia = datos.get("referencia")
    if not isinstance(referencia, dict) or type(referencia.get("nivel")) is not int or not 1 <= referencia["nivel"] <= maximo:
        raise ErrorConfiguracionPropuesta("Falta un nivel validado actual dentro de la rúbrica.")
    descriptores = datos.get("descriptores", [])
    if not isinstance(descriptores, list) or any(not isinstance(d, dict) for d in descriptores):
        raise ErrorConfiguracionPropuesta("Los descriptores de la rúbrica no son válidos.")
    por_nivel = {d.get("nivel"): d for d in descriptores}
    if (len(por_nivel) != len(descriptores) or set(por_nivel) != set(range(1, maximo + 1))
            or any(type(d.get("nivel")) is not int for d in descriptores)):
        raise ErrorConfiguracionPropuesta("Faltan descriptores o hay niveles duplicados en la rúbrica.")
    procedencias = {d.get("provisorio") for d in descriptores}
    if len(procedencias) != 1 or any(type(d.get("provisorio")) is not bool for d in descriptores):
        raise ErrorConfiguracionPropuesta("No se pueden mezclar descriptores oficiales y provisorios.")
    provisoria = descriptores[0]["provisorio"]
    niveles = []
    for numero in range(1, maximo + 1):
        d = por_nivel[numero]
        if not _texto(d.get("descripcion")) or (not provisoria and (
            not _texto(d.get("nombre")) or not _texto(d.get("conducta"))
        )):
            raise ErrorConfiguracionPropuesta("La rúbrica no tiene los textos esenciales de cada nivel.")
        nivel = {"nivel": numero, "nombre": d.get("nombre", ""), "descripcion": d["descripcion"]}
        if not provisoria:
            ejemplos = d.get("ejemplos", [])
            if not isinstance(ejemplos, list) or (ejemplos and not _texto(ejemplos[0])):
                raise ErrorConfiguracionPropuesta("El primer ejemplo de la rúbrica no es válido.")
            nivel.update(conducta=d["conducta"], ejemplos=ejemplos[:1])
        niveles.append(nivel)
    rubrica = {"origen": "provisoria" if provisoria else "integra", "nivel_maximo": maximo, "niveles": niveles}
    nucleo = datos.get("nucleo", {})
    if not isinstance(nucleo, dict) or not _texto(nucleo.get("sigla")) or not _texto(nucleo.get("nombre")):
        raise ErrorConfiguracionPropuesta("Falta el núcleo de la propuesta.")
    if provisoria:
        trayectoria = datos.get("trayectoria", {})
        if not isinstance(trayectoria, dict) or not _texto(trayectoria.get("inicio_nt1")):
            raise ErrorConfiguracionPropuesta("Falta la trayectoria inicial de la rúbrica provisoria.")
        conductas = []
        manifestaciones = datos.get("manifestaciones", [])
        for oa in datos.get("oas", []):
            item = {"oa": f"OA {oa['numero']} {nucleo['sigla']}", "NT1": [], "NT2": []}
            for m in manifestaciones:
                if m.get("oa_id") == oa["id"] and m.get("anio") in ("NT1", "NT2") and _texto(m.get("texto")):
                    item[m["anio"]].append(m["texto"])
            conductas.append(item)
        if any(not any(c[anio] for c in conductas) for anio in ("NT1", "NT2")):
            raise ErrorConfiguracionPropuesta("Faltan conductas NT1 o NT2 para la rúbrica provisoria.")
        rubrica.update(trayectoria=trayectoria, conductas_programa=conductas)
    observaciones, ids = [], set()
    for o in datos["evidencia"]:
        if (not isinstance(o, dict) or type(o.get("id")) is not int or o["id"] < 1 or o["id"] in ids
                or not _texto(o.get("cita")) or o.get("apoyo") not in APOYOS
                or not isinstance(o.get("oas"), list) or any(not _texto(oa) for oa in o["oas"])):
            raise ErrorConfiguracionPropuesta("La evidencia contiene datos incompletos o ids duplicados.")
        try:
            fecha = date.fromisoformat(o["fecha"]).isoformat()
        except (ValueError, TypeError, KeyError):
            raise ErrorConfiguracionPropuesta("La evidencia contiene una fecha inválida.") from None
        ids.add(o["id"])
        observaciones.append({"id": o["id"], "fecha": fecha, "cita": o["cita"], "oas": o["oas"], "apoyo": o["apoyo"]})
    observaciones.sort(key=lambda o: (o["fecha"], o["id"]))
    return {"nino": datos.get("nino"), "nivel_educativo": datos.get("nivel_educativo"),
            "nucleo": nucleo, "nivel_actual": referencia["nivel"], "rubrica": rubrica, "observaciones": observaciones}


def construir_herramienta(nivel_maximo, ids_enviados):
    return {"name": "proponer_nivel", "description": "Propone un nivel sustentado en las observaciones enviadas.",
            "inputSchema": {"json": {"type": "object", "additionalProperties": False, "required": sorted(CAMPOS),
                                     "properties": {
                "nivel": {"type": ["integer", "null"], "minimum": 1, "maximum": nivel_maximo},
                "evidencia_suficiente": {"type": "boolean"},
                "observaciones_citadas": {"type": "array", "uniqueItems": True,
                                          "items": {"type": "integer", "enum": sorted(ids_enviados)}},
                "conductas_observadas": {"type": "array", "maxItems": 20,
                                         "items": {"type": "string", "minLength": 1, "maxLength": 1000}},
                "justificacion": {"type": "string", "minLength": 1, "maxLength": 2000},
            }}}}


def validar_respuesta(respuesta, *, nivel_maximo, ids_enviados):
    if not isinstance(respuesta, dict) or set(respuesta) != CAMPOS:
        raise ErrorPropuesta("La respuesta no cumple el contrato de propuesta.")
    suficiente, nivel = respuesta["evidencia_suficiente"], respuesta["nivel"]
    if type(suficiente) is not bool or (suficiente and (type(nivel) is not int or not 1 <= nivel <= nivel_maximo)):
        raise ErrorPropuesta("La suficiencia o el nivel de la respuesta no son válidos.")
    if not suficiente and nivel is not None:
        raise ErrorPropuesta("Una respuesta sin evidencia suficiente debe tener nivel nulo.")
    citas, conductas, justificacion = (respuesta[c] for c in ("observaciones_citadas", "conductas_observadas", "justificacion"))
    if (not isinstance(citas, list) or any(type(i) is not int or i not in ids_enviados for i in citas)
            or len(set(citas)) != len(citas) or (suficiente and not citas)):
        raise ErrorPropuesta("Las citas deben ser ids únicos de las observaciones enviadas.")
    if (not isinstance(conductas, list) or len(conductas) > 20 or any(not _texto(c) or len(c) > 1000 for c in conductas)
            or (suficiente and not conductas) or not _texto(justificacion) or len(justificacion) > 2000):
        raise ErrorPropuesta("La respuesta requiere conductas y una justificación breve válidas.")
    return {"nivel": nivel, "evidencia_suficiente": suficiente, "observaciones_citadas": list(citas),
            "conductas_observadas": [c.strip() for c in conductas], "justificacion": justificacion.strip()}


def proponer(datos, identidades, *, cliente=None):
    """Devuelve una propuesta validada; no persiste ni modifica niveles."""
    if not isinstance(datos, dict) or not isinstance(datos.get("evidencia"), list):
        raise ErrorConfiguracionPropuesta("Se requiere una lista de evidencia.")
    if not datos["evidencia"]:
        return {"nivel": None, "evidencia_suficiente": False, "observaciones_citadas": [],
                "conductas_observadas": [], "justificacion": "Faltan observaciones aceptadas de este núcleo."}
    contexto = construir_contexto(datos)
    identidades = list(identidades)
    if contexto["nino"] not in {n.get("codigo") for n in identidades}:
        raise ErrorConfiguracionPropuesta("El código del niño no pertenece al curso enviado.")
    ids = {o["id"] for o in contexto["observaciones"]}
    try:
        seudonimo = Seudonimizador(identidades)
        respuesta = seudonimo.invocar(cliente if cliente is not None else ClienteBedrock(), leer_prompt(),
                                      contexto, construir_herramienta(contexto["rubrica"]["nivel_maximo"], ids))
    except ErrorBedrock:
        raise ErrorPropuesta("No se pudo generar la propuesta con Bedrock.") from None
    except (ValueError, TypeError):
        raise ErrorConfiguracionPropuesta("No se pudo preparar un envío con códigos y campos válidos.") from None
    validada = validar_respuesta(respuesta, nivel_maximo=contexto["rubrica"]["nivel_maximo"], ids_enviados=ids)
    return seudonimo.datos(validada)
