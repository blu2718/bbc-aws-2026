"""Lectura con Claude de la hoja de resultados de un instrumento estandarizado (Task 14).

Funciones puras: no dependen de Django. La hoja llega como bytes (foto o PDF) junto con
la estructura del catálogo de instrumentos (áreas, campos y categorías, sin tablas de
normas). Claude identifica el instrumento y copia lo que dice la hoja; no calcula ni
convierte puntajes. La validación de rangos y los cálculos los hace `registro/instrumentos.py`.

- `detectar_tipo(contenido)`: ("imagen", formato) o ("pdf", None), o None.
- `validar_hoja(contenido)`: tipo y formato, o HojaInvalida con un mensaje para la usuaria.
- `leer_hoja(contenido, definiciones, codigo=None, cliente=None)`: dict con lo leído.
"""
import json
from pathlib import Path

from .bedrock import ClienteBedrock, ErrorBedrock
from .foto import TAMANO_MAXIMO as TAMANO_MAXIMO_IMAGEN
from .foto import detectar_formato

RUTA_PROMPT = Path(__file__).resolve().parent / "prompts" / "lectura_instrumento.md"
NOMBRE_HERRAMIENTA = "registrar_resultado_instrumento"
# Límite de Converse por documento: 4,5 MB.
TAMANO_MAXIMO_PDF = 4_500_000
NOMBRE_DOCUMENTO = "hoja de resultados"


class HojaInvalida(ValueError):
    """El archivo no es una foto o un PDF aceptado. Reintentar no sirve."""


class ErrorLecturaInstrumento(Exception):
    """Falló Bedrock o la respuesta no sirve. La hoja se conserva para reintentar."""


def detectar_tipo(contenido):
    if bytes(contenido[:5]) == b"%PDF-":
        return "pdf", None
    formato = detectar_formato(contenido)
    return ("imagen", formato) if formato else None


def validar_hoja(contenido):
    if not contenido:
        raise HojaInvalida("El archivo está vacío.")
    tipo = detectar_tipo(contenido)
    if tipo is None:
        raise HojaInvalida("El archivo no es una foto (JPEG, PNG, GIF o WebP) ni un PDF.")
    limite = TAMANO_MAXIMO_PDF if tipo[0] == "pdf" else TAMANO_MAXIMO_IMAGEN
    if len(contenido) > limite:
        raise HojaInvalida(
            f"El archivo pesa {len(contenido) / 1_000_000:.1f} MB y el máximo es {limite / 1_000_000:.2f} MB.".replace(".", ",")
        )
    return tipo


def estructura_para_el_modelo(definiciones):
    """La parte del catálogo que Claude necesita: códigos, nombres, rangos y opciones. Sin textos de la ficha."""
    salida = []
    for d in definiciones:
        def campos(lista):
            return [{k: c[k] for k in ("codigo", "nombre", "tipo", "min", "max", "opciones") if k in c} for c in lista]

        item = {
            "codigo": d["codigo"], "nombre": d["nombre"], "edad_meses": [d.get("edad_min_meses"), d.get("edad_max_meses")],
            "campos": campos(d.get("campos", [])),
            "areas": [{"codigo": a["codigo"], "nombre": a["nombre"]} for a in d.get("areas", [])],
            "campos_area": campos(d.get("campos_area", [])),
        }
        for clave in ("categoria", "categoria_area"):
            cat = d.get(clave)
            if cat and cat.get("usa"):
                cat = d.get(cat["usa"])
            if cat:
                item[clave] = [{"codigo": o["codigo"], "nombre": o["nombre"]} for o in cat["opciones"]]
        if d.get("areas_libres"):
            item["areas_libres"] = True
        for c in item["campos"] + item["campos_area"]:
            if "opciones" in c:
                c["opciones"] = [{"codigo": o["codigo"], "nombre": o["nombre"]} for o in c["opciones"]]
        salida.append(item)
    return salida


def construir_herramienta(codigos):
    texto_o_nulo = {"type": ["string", "null"]}
    return {
        "name": NOMBRE_HERRAMIENTA,
        "description": "Registra lo que dice la hoja de resultados de un instrumento estandarizado, tal como está escrito.",
        "inputSchema": {"json": {
            "type": "object",
            "properties": {
                "es_hoja_de_instrumento": {"type": "boolean", "description": "false si la imagen no es una hoja de resultados."},
                "instrumento": {"type": "string", "enum": list(codigos), "description": "Código del catálogo; OTRO si no está."},
                "fecha_aplicacion": {**texto_o_nulo, "description": "AAAA-MM-DD, o null si no aparece."},
                "aplicado_por": {**texto_o_nulo, "description": "Cargo o centro de quien lo aplicó. Sin RUT."},
                "nombre_en_hoja": {**texto_o_nulo, "description": "Nombre del niño o niña como aparece, solo para verificar."},
                "fecha_nacimiento_en_hoja": {**texto_o_nulo, "description": "AAAA-MM-DD, o null."},
                "campos": {"type": "object", "description": "Puntajes globales: {código del campo: valor como está escrito}."},
                "areas": {"type": "object", "description": "{código del área: {código del campo de área: valor}}."},
                "categoria": {**texto_o_nulo, "description": "Código de la categoría global marcada en la hoja."},
                "categorias_area": {"type": "object", "description": "{código del área: código de la categoría marcada}."},
                "areas_libres": {
                    "type": "array", "description": "Solo para OTRO: cada área o escala que trae la hoja.",
                    "items": {"type": "object", "properties": {
                        "nombre": {"type": "string"}, "puntaje": texto_o_nulo, "resultado": texto_o_nulo,
                    }, "required": ["nombre"]},
                },
                "observaciones": {**texto_o_nulo, "description": "Observaciones escritas en la hoja, textuales."},
                "ilegibles": {"type": "array", "items": {"type": "string"},
                              "description": "Qué datos aparecen en la hoja pero no se pudieron leer."},
            },
            "required": ["es_hoja_de_instrumento", "instrumento", "campos", "areas", "ilegibles"],
        }},
    }


def construir_mensaje(definiciones, codigo=None):
    partes = ["Catálogo de instrumentos (estructura, sin tablas de normas):",
              json.dumps(estructura_para_el_modelo(definiciones), ensure_ascii=False)]
    if codigo:
        partes.append(f"La educadora indicó que la hoja es del instrumento {codigo}. Si claramente es otro, usa el código correcto.")
    else:
        partes.append("La educadora no indicó el instrumento: identifícalo en la hoja.")
    partes.append("Registra lo que dice la hoja con la herramienta.")
    return "\n\n".join(partes)


def _validar_forma(entrada, codigos):
    if not isinstance(entrada, dict):
        raise ErrorLecturaInstrumento("La respuesta no es un objeto.")
    if entrada.get("instrumento") not in codigos:
        raise ErrorLecturaInstrumento(f"Instrumento desconocido: {entrada.get('instrumento')!r}.")
    for clave in ("campos", "areas", "categorias_area"):
        valor = entrada.get(clave)
        if valor is None:
            entrada[clave] = {}
        elif not isinstance(valor, dict):
            raise ErrorLecturaInstrumento(f"'{clave}' debe ser un objeto.")
    entrada["areas"] = {k: v for k, v in entrada["areas"].items() if isinstance(v, dict)}
    for clave in ("ilegibles", "areas_libres"):
        if not isinstance(entrada.get(clave) or [], list):
            raise ErrorLecturaInstrumento(f"'{clave}' debe ser una lista.")
    return entrada


def leer_hoja(contenido, definiciones, codigo=None, cliente=None):
    tipo, formato = validar_hoja(contenido)
    codigos = [d["codigo"] for d in definiciones]
    if cliente is None:
        cliente = ClienteBedrock()
    argumentos = {"imagenes": [(formato, bytes(contenido))]} if tipo == "imagen" else {
        "documentos": [(NOMBRE_DOCUMENTO.replace(" ", "-"), bytes(contenido))]
    }
    try:
        entrada = cliente.invocar_herramienta(
            RUTA_PROMPT.read_text(encoding="utf-8"), construir_mensaje(definiciones, codigo),
            construir_herramienta(codigos), **argumentos,
        )
    except ErrorBedrock as error:
        raise ErrorLecturaInstrumento(str(error)) from error
    return _validar_forma(entrada, codigos)
