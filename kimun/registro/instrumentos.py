"""Instrumentos estandarizados: catálogo, validación, cálculos y lectura de la hoja (Task 14).

El catálogo (`datos/instrumentos.json`) describe cada instrumento como dato: áreas,
campos de puntaje con su rango, cálculos y categorías con sus puntos de corte. Nada de
eso está fijo en el código. Investigación y fuentes en `contexto/instrumentos-estandarizados.md`.

Reglas:

- El código calcula solo lo que no necesita tablas de normas con licencia: la edad al
  evaluar, sumas de puntajes brutos, la razón EM/EC y la categoría según los puntos de
  corte publicados. El CD de la EEDP y los puntajes T del TEPSI se copian de la hoja.
- Si la hoja trae una categoría que no calza con su puntaje, se guarda la de la hoja y
  se avisa, para que la educadora revise.
- Un resultado no es evidencia de aprendizaje: no entra en la propuesta de nivel, las
  alertas, la tabla del curso ni la vista del jardín. Solo se muestra en la ficha.

`valores` de un resultado:
    {"campos": {"CD": 92}, "areas": {"M": {"perfil": "acorde"}}, "categoria": "normal",
     "categorias_area": {"C": "normal"}, "areas_libres": [{"nombre": "...", "puntaje": "..."}]}
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .coincidencia import normalizar
from .models import Instrumento, RegistroCambio, ResultadoInstrumento

logger = logging.getLogger(__name__)

RUTA_INSTRUMENTOS = Path(settings.DATOS_DIR) / "instrumentos.json"
MAX_AREAS_LIBRES = 12
UMBRAL_LEYENDO_ATASCADA = timedelta(minutes=5)
TIPOS_CAMPO = {"numero", "opcion", "texto"}


# --- Catálogo -----------------------------------------------------------------------


class DefinicionInvalida(ValueError):
    pass


def leer_instrumentos(ruta=None):
    return json.loads(Path(ruta or RUTA_INSTRUMENTOS).read_text(encoding="utf-8"))


def _validar_campos(campos, donde):
    codigos = set()
    for c in campos:
        if c.get("tipo") not in TIPOS_CAMPO:
            raise DefinicionInvalida(f"{donde}: el campo {c.get('codigo')!r} tiene un tipo desconocido.")
        if c["codigo"] in codigos:
            raise DefinicionInvalida(f"{donde}: el campo {c['codigo']!r} está repetido.")
        codigos.add(c["codigo"])
        if c["tipo"] == "numero" and not (c.get("min", 0) <= c.get("max", 0)):
            raise DefinicionInvalida(f"{donde}: el rango de {c['codigo']!r} no es válido.")
        if c["tipo"] == "opcion" and not c.get("opciones"):
            raise DefinicionInvalida(f"{donde}: {c['codigo']!r} no tiene opciones.")
    return codigos


def _validar_categoria(categoria, campos, donde):
    if not categoria:
        return
    if categoria.get("usa"):
        return
    opciones = categoria.get("opciones") or []
    if not opciones:
        raise DefinicionInvalida(f"{donde}: la categoría no tiene opciones.")
    if categoria.get("campo"):
        if categoria["campo"] not in campos:
            raise DefinicionInvalida(f"{donde}: la categoría usa el campo {categoria['campo']!r}, que no existe.")
        cortes = [o.get("desde") for o in opciones]
        if cortes[-1] is not None or any(c is None for c in cortes[:-1]):
            raise DefinicionInvalida(f"{donde}: solo la última categoría puede quedar sin punto de corte.")
        if cortes[:-1] != sorted(cortes[:-1], reverse=True):
            raise DefinicionInvalida(f"{donde}: los puntos de corte deben ir de mayor a menor.")


def validar_definicion(d):
    donde = d.get("codigo", "?")
    if d.get("ambito") not in Instrumento.Ambito.values:
        raise DefinicionInvalida(f"{donde}: ámbito desconocido.")
    campos = _validar_campos(d.get("campos", []), donde)
    campos_area = _validar_campos(d.get("campos_area", []), f"{donde} (áreas)")
    areas = [a["codigo"] for a in d.get("areas", [])]
    if len(areas) != len(set(areas)):
        raise DefinicionInvalida(f"{donde}: hay áreas repetidas.")
    for c in d.get("campos", []):
        calculo = c.get("calculo")
        if calculo:
            tipo, _, origen = calculo.partition(":")
            if tipo == "suma_areas" and origen not in campos_area:
                raise DefinicionInvalida(f"{donde}: {c['codigo']} suma {origen!r}, que no es un campo de área.")
            if tipo == "razon_edad" and origen not in campos:
                raise DefinicionInvalida(f"{donde}: {c['codigo']} usa {origen!r}, que no existe.")
            if tipo not in ("suma_areas", "razon_edad"):
                raise DefinicionInvalida(f"{donde}: cálculo desconocido {tipo!r}.")
    _validar_categoria(d.get("categoria"), campos, donde)
    _validar_categoria(d.get("categoria_area"), campos_area, f"{donde} (áreas)")


@transaction.atomic
def cargar_instrumentos(datos):
    """Crea o actualiza los instrumentos del catálogo (idempotente). Devuelve cuántos cargó."""
    for orden, d in enumerate(datos["instrumentos"]):
        validar_definicion(d)
        Instrumento.objects.update_or_create(
            codigo=d["codigo"],
            defaults={"nombre": d["nombre"], "ambito": d["ambito"], "definicion": d,
                      "provisorio": bool(d.get("provisorio")), "orden": orden},
        )
    return len(datos["instrumentos"])


# --- Definición: accesos --------------------------------------------------------------


def categoria_area(defi):
    """La categoría por área, resolviendo {"usa": "categoria"} (TEPSI usa los mismos cortes)."""
    cat = defi.get("categoria_area")
    if cat and cat.get("usa") == "categoria":
        return {**defi["categoria"], "campo": cat.get("campo", defi["categoria"].get("campo"))}
    return cat


def opcion(categoria, codigo):
    for o in (categoria or {}).get("opciones", []):
        if o["codigo"] == codigo:
            return o
    return None


def maximo(campo, area=None):
    if area and campo["codigo"] in (area.get("maximos") or {}):
        return area["maximos"][campo["codigo"]]
    return campo.get("max")


# --- Normalización de valores ---------------------------------------------------------


def _numero(texto):
    if isinstance(texto, bool):
        return None
    if isinstance(texto, (int, float)):
        texto = str(texto)
    limpio = str(texto).strip().replace(" ", "")
    if not limpio:
        return None
    # "0,92" → 0.92; "1.234" se lee como 1,234 solo si hay coma también (no se usan miles en estas hojas).
    limpio = limpio.replace(",", ".")
    try:
        numero = Decimal(limpio)
    except InvalidOperation:
        return None
    # "NaN", "Infinity" o "1e999999" no son puntajes (y caerían al redondear).
    if not numero.is_finite() or abs(numero) > 10**6:
        return None
    return numero


def _redondear(valor, decimales):
    paso = Decimal(1).scaleb(-decimales)
    redondeado = valor.quantize(paso, rounding=ROUND_HALF_UP)
    return int(redondeado) if decimales == 0 else float(redondeado)


def _opcion_valida(opciones, crudo):
    if crudo in (None, ""):
        return None
    texto = normalizar(str(crudo))
    for o in opciones:
        if texto in (normalizar(o["codigo"]), normalizar(o["nombre"]), normalizar(o.get("texto_ficha", ""))):
            return o["codigo"]
    return False


def normalizar_campo(campo, crudo, area=None):
    """(valor, problema). valor None si viene vacío; problema es un texto si no sirve."""
    if crudo in (None, ""):
        return None, None
    nombre = campo["nombre"]
    if campo["tipo"] == "texto":
        return str(crudo).strip()[: campo.get("max_largo", 200)] or None, None
    if campo["tipo"] == "opcion":
        valor = _opcion_valida(campo["opciones"], crudo)
        if valor is False:
            return None, f"{nombre}: «{crudo}» no es una opción válida."
        return valor, None
    numero = _numero(crudo)
    if numero is None:
        return None, f"{nombre}: «{crudo}» no es un número."
    if campo.get("escala_100") and 0 < numero <= 2:
        # CD escrito como razón en la hoja: 0,92 o 1,00 (un CD de 1 o 2 puntos no existe).
        numero *= 100
    valor = _redondear(numero, campo.get("decimales", 0))
    tope = maximo(campo, area)
    if not (campo.get("min", 0) <= valor <= tope):
        return None, f"{nombre}: {valor} está fuera del rango del instrumento ({campo.get('min', 0)} a {tope})."
    return valor, None


def _dict(valor):
    return valor if isinstance(valor, dict) else {}


def normalizar_valores(defi, crudos):
    """Valores válidos según la definición y la lista de problemas (lo que se descartó y por qué)."""
    # Lo leído por Claude puede venir con otra forma (un texto donde se esperaba un objeto):
    # se ignora lo que no calza en vez de caer.
    crudos = _dict(crudos)
    problemas, valores = [], {"campos": {}, "areas": {}, "categorias_area": {}}
    for campo in defi.get("campos", []):
        valor, problema = normalizar_campo(campo, _dict(crudos.get("campos")).get(campo["codigo"]))
        if problema:
            problemas.append(problema)
        if valor is not None:
            valores["campos"][campo["codigo"]] = valor

    cat_area = categoria_area(defi)
    for area in defi.get("areas", []):
        crudo_area = _dict(_dict(crudos.get("areas")).get(area["codigo"]))
        fila = {}
        for campo in defi.get("campos_area", []):
            valor, problema = normalizar_campo(campo, crudo_area.get(campo["codigo"]), area)
            if problema:
                problemas.append(f"{area['nombre']}, {problema[0].lower()}{problema[1:]}")
            if valor is not None:
                fila[campo["codigo"]] = valor
        if fila:
            valores["areas"][area["codigo"]] = fila
        if cat_area:
            crudo_cat = _dict(crudos.get("categorias_area")).get(area["codigo"])
            cat = _opcion_valida(cat_area["opciones"], crudo_cat)
            if cat is False:
                problemas.append(f"{area['nombre']}: la categoría «{crudo_cat}» no es del instrumento.")
            elif cat:
                valores["categorias_area"][area["codigo"]] = cat

    if defi.get("categoria"):
        crudo_cat = crudos.get("categoria")
        cat = _opcion_valida(defi["categoria"]["opciones"], crudo_cat)
        if cat is False:
            problemas.append(f"La categoría «{crudo_cat}» no es del instrumento.")
        elif cat:
            valores["categoria"] = cat

    if defi.get("areas_libres"):
        libres = []
        filas = crudos.get("areas_libres")
        for fila in (filas if isinstance(filas, list) else [])[:MAX_AREAS_LIBRES]:
            fila = _dict(fila)
            nombre = str(fila.get("nombre") or "").strip()[:80]
            if not nombre:
                continue
            datos = {"nombre": nombre}
            for campo in defi.get("campos_area", []):
                valor, _ = normalizar_campo(campo, fila.get(campo["codigo"]))
                if valor is not None:
                    datos[campo["codigo"]] = valor
            libres.append(datos)
        valores["areas_libres"] = libres
    return valores, problemas


# --- Cálculos -------------------------------------------------------------------------


def edad_en_dias(nacimiento, fecha):
    if not nacimiento or not fecha or fecha < nacimiento:
        return None
    return (fecha - nacimiento).days


def edad_en_meses(nacimiento, fecha):
    if edad_en_dias(nacimiento, fecha) is None:
        return None
    meses = (fecha.year - nacimiento.year) * 12 + fecha.month - nacimiento.month
    return meses - (1 if fecha.day < nacimiento.day else 0)


def texto_edad_evaluacion(nacimiento, fecha):
    meses = edad_en_meses(nacimiento, fecha)
    if meses is None:
        return ""
    anios, resto = divmod(meses, 12)
    if not anios:
        return f"{meses} mes{'es' if meses != 1 else ''}"
    return f"{anios} año{'s' if anios != 1 else ''}" + (f" y {resto} mes{'es' if resto != 1 else ''}" if resto else "")


def calcular(defi, valores, edad_dias):
    """{código del campo: valor calculado} para los campos con `calculo`, si hay datos para calcularlo."""
    calculados = {}
    for campo in defi.get("campos", []):
        tipo, _, origen = (campo.get("calculo") or "").partition(":")
        if tipo == "suma_areas":
            areas = defi.get("areas", [])
            sumandos = [(valores.get("areas") or {}).get(a["codigo"], {}).get(origen) for a in areas]
            if areas and all(isinstance(s, (int, float)) for s in sumandos):
                calculados[campo["codigo"]] = _redondear(Decimal(str(sum(sumandos))), campo.get("decimales", 0))
        elif tipo == "razon_edad":
            base = (valores.get("campos") or {}).get(origen)
            if isinstance(base, (int, float)) and edad_dias:
                calculados[campo["codigo"]] = _redondear(Decimal(base) / Decimal(edad_dias), campo.get("decimales", 2))
    return calculados


def categoria_por_cortes(categoria, valor):
    """Código de la categoría que corresponde al valor según los puntos de corte; None si no hay cortes."""
    if not categoria or not categoria.get("campo") or not isinstance(valor, (int, float)):
        return None
    for o in categoria["opciones"]:
        if o.get("desde") is None or valor >= o["desde"]:
            return o["codigo"]
    return None


def completar(defi, valores, edad_dias):
    """Completa lo que se puede calcular y no vino en la hoja: campos calculados y categorías."""
    valores = json.loads(json.dumps(valores or {}))
    campos = valores.setdefault("campos", {})
    for codigo, valor in calcular(defi, valores, edad_dias).items():
        campos.setdefault(codigo, valor)
    cat = defi.get("categoria")
    if cat and cat.get("campo") and not valores.get("categoria"):
        calculada = categoria_por_cortes(cat, campos.get(cat["campo"]))
        if calculada:
            valores["categoria"] = calculada
    cat_area = categoria_area(defi)
    if cat_area and cat_area.get("campo"):
        por_area = valores.setdefault("categorias_area", {})
        for area in defi.get("areas", []):
            if area["codigo"] not in por_area:
                calculada = categoria_por_cortes(cat_area, (valores.get("areas") or {}).get(area["codigo"], {}).get(cat_area["campo"]))
                if calculada:
                    por_area[area["codigo"]] = calculada
    return valores


# --- Resumen para mostrar --------------------------------------------------------------


@dataclass
class Fila:
    nombre: str
    valor: str
    calculado: str = ""
    aviso: str = ""


@dataclass
class FilaArea:
    nombre: str
    valores: list
    categoria: dict | None = None
    destacar: bool = False   # su categoría no es la primera (la "dentro de lo esperado")


@dataclass
class Resumen:
    instrumento: Instrumento | None
    edad: str = ""
    principal: Fila | None = None
    categoria: dict | None = None
    campos: list = field(default_factory=list)
    columnas_area: list = field(default_factory=list)
    areas: list = field(default_factory=list)
    areas_libres: list = field(default_factory=list)
    avisos: list = field(default_factory=list)


def _texto_valor(campo, valor):
    if valor in (None, ""):
        return "–"
    if campo["tipo"] == "opcion":
        o = next((o for o in campo["opciones"] if o["codigo"] == valor), None)
        return o["nombre"] if o else str(valor)
    if isinstance(valor, float):
        return f"{valor:.{campo.get('decimales', 2)}f}".replace(".", ",")
    return str(valor)


def avisos_de_coherencia(defi, valores, nacimiento, fecha):
    """Lo que no calza: edad fuera del rango, cálculos o categorías distintos a lo de la hoja."""
    avisos = []
    edad = edad_en_meses(nacimiento, fecha)
    if fecha and not nacimiento:
        avisos.append("Falta la fecha de nacimiento del niño: no se puede calcular su edad al evaluar.")
    elif edad is not None and not (defi.get("edad_min_meses", 0) <= edad <= defi.get("edad_max_meses", 999)):
        avisos.append(
            f"A la fecha de aplicación tenía {texto_edad_evaluacion(nacimiento, fecha)}, fuera del rango del "
            f"instrumento ({defi.get('edad_min_meses')} a {defi.get('edad_max_meses')} meses). Revisa las fechas."
        )
    if fecha and fecha > timezone.localdate():
        avisos.append("La fecha de aplicación es posterior a hoy.")
    campos = valores.get("campos") or {}
    nombres = {c["codigo"]: c for c in defi.get("campos", [])}
    for codigo, calculado in calcular(defi, valores, edad_en_dias(nacimiento, fecha)).items():
        anotado = campos.get(codigo)
        tolerancia = 0.011 if isinstance(calculado, float) else 0
        if anotado is not None and abs(anotado - calculado) > tolerancia:
            c = nombres[codigo]
            avisos.append(f"{c['nombre']}: la hoja dice {_texto_valor(c, anotado)} y Kimün calcula {_texto_valor(c, calculado)}.")
    cat = defi.get("categoria")
    if cat and cat.get("campo") and valores.get("categoria"):
        calculada = categoria_por_cortes(cat, campos.get(cat["campo"]))
        if calculada and calculada != valores["categoria"]:
            avisos.append(
                f"El resultado anotado es «{opcion(cat, valores['categoria'])['nombre']}», pero con "
                f"{nombres[cat['campo']]['nombre']} {_texto_valor(nombres[cat['campo']], campos.get(cat['campo']))} "
                f"corresponde «{opcion(cat, calculada)['nombre']}» según los puntos de corte publicados. Revisa la hoja."
            )
    cat_area = categoria_area(defi)
    if cat_area and cat_area.get("campo"):
        for area in defi.get("areas", []):
            anotada = (valores.get("categorias_area") or {}).get(area["codigo"])
            calculada = categoria_por_cortes(cat_area, (valores.get("areas") or {}).get(area["codigo"], {}).get(cat_area["campo"]))
            if anotada and calculada and anotada != calculada:
                avisos.append(
                    f"{area['nombre']}: el resultado anotado es «{opcion(cat_area, anotada)['nombre']}», pero su "
                    f"puntaje corresponde a «{opcion(cat_area, calculada)['nombre']}»."
                )
    return avisos


def resumir(resultado):
    """Lo que la ficha y la pantalla del resultado muestran, con avisos de coherencia."""
    inst = resultado.instrumento
    if inst is None:
        return Resumen(instrumento=None, avisos=list(resultado.avisos or []))
    defi = inst.definicion
    nacimiento = resultado.nino.fecha_nacimiento
    valores = resultado.valores or {}
    campos = valores.get("campos") or {}
    calculados = calcular(defi, valores, edad_en_dias(nacimiento, resultado.fecha_aplicacion))
    resumen = Resumen(instrumento=inst, edad=texto_edad_evaluacion(nacimiento, resultado.fecha_aplicacion))
    for c in defi.get("campos", []):
        fila = Fila(c["nombre"], _texto_valor(c, campos.get(c["codigo"])),
                    _texto_valor(c, calculados[c["codigo"]]) if c["codigo"] in calculados else "")
        resumen.campos.append(fila)
        if c.get("principal"):
            resumen.principal = fila
    if defi.get("categoria"):
        resumen.categoria = opcion(defi["categoria"], valores.get("categoria"))
    cat_area = categoria_area(defi)
    resumen.columnas_area = [c["nombre"] for c in defi.get("campos_area", [])]
    for area in defi.get("areas", []):
        fila = (valores.get("areas") or {}).get(area["codigo"], {})
        cat = opcion(cat_area, (valores.get("categorias_area") or {}).get(area["codigo"])) if cat_area else None
        resumen.areas.append(FilaArea(
            area["nombre"], [_texto_valor(c, fila.get(c["codigo"])) for c in defi.get("campos_area", [])],
            cat, destacar=bool(cat) and cat["codigo"] != cat_area["opciones"][0]["codigo"],
        ))
    for fila in valores.get("areas_libres") or []:
        resumen.areas_libres.append(FilaArea(
            fila["nombre"], [_texto_valor(c, fila.get(c["codigo"])) for c in defi.get("campos_area", [])],
        ))
    resumen.avisos = list(resultado.avisos or []) + avisos_de_coherencia(defi, valores, nacimiento, resultado.fecha_aplicacion)
    return resumen


def etiquetador(instrumento):
    """Nombre legible de cada clave aplanada de una instantánea ("valores.areas.C.T" → "Coordinación · Puntaje T")."""
    defi = instrumento.definicion if instrumento else {}
    campos = {c["codigo"]: c["nombre"] for c in defi.get("campos", [])}
    campos_area = {c["codigo"]: c["nombre"] for c in defi.get("campos_area", [])}
    areas = {a["codigo"]: a["nombre"] for a in defi.get("areas", [])}
    fijos = {"instrumento": "Instrumento", "estado": "Estado", "origen": "Origen", "fecha_aplicacion": "Fecha de aplicación",
             "aplicado_por": "Aplicado por", "observaciones": "Observaciones", "valores.categoria": "Resultado"}

    opciones_campo = {c["codigo"]: {o["codigo"]: o["nombre"] for o in c.get("opciones", [])}
                      for c in defi.get("campos", []) + defi.get("campos_area", [])}
    cat_global = {o["codigo"]: o["nombre"] for o in (defi.get("categoria") or {}).get("opciones", [])}
    cat_a = categoria_area(defi) if defi else None
    cat_por_area = {o["codigo"]: o["nombre"] for o in (cat_a or {}).get("opciones", [])}
    estados, origenes = dict(ResultadoInstrumento.Estado.choices), dict(ResultadoInstrumento.Origen.choices)

    def formatear(clave, valor):
        """Texto legible de un valor del historial: nombres de estados, orígenes y categorías en vez de códigos."""
        partes = clave.split(".")
        if clave == "estado":
            return estados.get(valor, valor)
        if clave == "origen":
            return origenes.get(valor, valor)
        if clave == "valores.categoria":
            return cat_global.get(valor, valor)
        if partes[:2] == ["valores", "categorias_area"]:
            return cat_por_area.get(valor, valor)
        if partes[-1] in opciones_campo and opciones_campo[partes[-1]]:
            return opciones_campo[partes[-1]].get(valor, valor)
        return valor

    def etiquetar(clave):
        if clave in fijos:
            return fijos[clave]
        partes = clave.split(".")
        if partes[:2] == ["valores", "campos"] and len(partes) == 3:
            return campos.get(partes[2], partes[2])
        if partes[:2] == ["valores", "areas"] and len(partes) == 4:
            return f"{areas.get(partes[2], partes[2])} · {campos_area.get(partes[3], partes[3])}"
        if partes[:2] == ["valores", "categorias_area"] and len(partes) == 3:
            return f"{areas.get(partes[2], partes[2])} · Resultado"
        if partes[:2] == ["valores", "areas_libres"]:
            return "Áreas"
        return clave
    etiquetar.formatear = formatear
    return etiquetar


# --- Lectura de la hoja en el proceso de fondo ----------------------------------------


def coincide_nombre(nombre_en_hoja, nino):
    """True si el nombre leído en la hoja parece el del niño: su nombre de pila y, si la hoja trae más, un apellido."""
    hoja = set(normalizar(nombre_en_hoja or "").split())
    propio = normalizar(nino.nombre).split()
    if not hoja or not propio:
        return True
    if propio[0] not in hoja:
        return False
    return len(hoja) == 1 or len(propio) == 1 or bool(hoja & set(propio[1:]))


def _fecha(texto):
    try:
        return date.fromisoformat(str(texto)) if texto else None
    except ValueError:
        return None


def aplicar_lectura(resultado, lectura, instrumentos):
    """Pasa lo leído por Kimün al resultado (sin guardarlo). Devuelve los avisos."""
    avisos = []
    if not lectura.get("es_hoja_de_instrumento", True):
        avisos.append("Kimün no reconoció una hoja de resultados de un instrumento. Completa los datos a mano o descarta.")
    codigo = lectura.get("instrumento")
    if resultado.instrumento_id is None:
        resultado.instrumento = instrumentos.get(codigo) or instrumentos.get("OTRO")
    elif codigo and codigo != resultado.instrumento.codigo:
        avisos.append(f"Elegiste {resultado.instrumento.codigo}, pero la hoja parece de {codigo}. Revisa el instrumento.")
    defi = resultado.instrumento.definicion
    valores, problemas = normalizar_valores(defi, lectura)
    fecha = _fecha(lectura.get("fecha_aplicacion"))
    if lectura.get("fecha_aplicacion") and fecha is None:
        problemas.append(f"Fecha de aplicación ilegible: «{lectura['fecha_aplicacion']}».")
    if fecha and fecha > timezone.localdate():
        problemas.append(f"La fecha de aplicación leída ({fecha:%d-%m-%Y}) es posterior a hoy; queda vacía.")
        fecha = None
    resultado.fecha_aplicacion = fecha
    resultado.aplicado_por = str(lectura.get("aplicado_por") or "")[:120]
    resultado.observaciones = str(lectura.get("observaciones") or "")[:2000]
    resultado.valores = completar(defi, valores, edad_en_dias(resultado.nino.fecha_nacimiento, fecha))
    nino = resultado.nino
    if lectura.get("nombre_en_hoja") and not coincide_nombre(lectura["nombre_en_hoja"], nino):
        avisos.append(f"El nombre escrito en la hoja no parece ser el de {nino.nombre}. Revisa que sea su hoja.")
    nacimiento_hoja = _fecha(lectura.get("fecha_nacimiento_en_hoja"))
    if nacimiento_hoja and nino.fecha_nacimiento and nacimiento_hoja != nino.fecha_nacimiento:
        avisos.append(f"La fecha de nacimiento de la hoja ({nacimiento_hoja:%d-%m-%Y}) no coincide con la registrada.")
    ilegibles = [str(x)[:120] for x in (lectura.get("ilegibles") or [])][:10]
    if ilegibles:
        avisos.append("No se pudo leer: " + "; ".join(ilegibles) + ".")
    return avisos + problemas


def _con_resultados():
    return ResultadoInstrumento.objects.select_related("nino__curso", "instrumento")


def tomar_siguiente_lectura():
    while True:
        pk = (ResultadoInstrumento.objects.filter(estado=ResultadoInstrumento.Estado.POR_LEER)
              .order_by("creado", "pk").values_list("pk", flat=True).first())
        if pk is None:
            return None
        tomadas = ResultadoInstrumento.objects.filter(pk=pk, estado=ResultadoInstrumento.Estado.POR_LEER).update(
            estado=ResultadoInstrumento.Estado.LEYENDO, intentos=F("intentos") + 1, actualizado=timezone.now(),
        )
        if tomadas == 1:
            return _con_resultados().get(pk=pk)


def recuperar_lecturas_atascadas():
    ahora = timezone.now()
    return ResultadoInstrumento.objects.filter(
        estado=ResultadoInstrumento.Estado.LEYENDO, actualizado__lt=ahora - UMBRAL_LEYENDO_ATASCADA,
    ).update(estado=ResultadoInstrumento.Estado.POR_LEER, actualizado=ahora)


def borrar_hoja(resultado):
    if not resultado.archivo:
        return True
    nombre = resultado.archivo.name
    try:
        resultado.archivo.storage.delete(nombre)
    except Exception:
        logger.exception("Resultado %s: no se pudo borrar la hoja; se reintenta al volver a leer", resultado.pk)
        return False
    resultado.archivo = ""
    resultado.save(update_fields=["archivo", "actualizado"])
    return True


def procesar_lectura(resultado, cliente=None):
    """Lee la hoja con Claude, deja el resultado por revisar y borra el archivo. True si resultó."""
    from .historial import registrar
    from .ia.instrumento import ErrorLecturaInstrumento, HojaInvalida, leer_hoja

    instrumentos = {i.codigo: i for i in Instrumento.objects.all()}
    try:
        if not resultado.archivo:
            raise HojaInvalida("No hay hoja que leer.")
        with resultado.archivo.open("rb") as archivo:
            contenido = archivo.read()
        lectura = leer_hoja(
            contenido, [i.definicion for i in instrumentos.values()],
            codigo=resultado.instrumento.codigo if resultado.instrumento_id else None, cliente=cliente,
        )
    except HojaInvalida as error:
        borrar_hoja(resultado)
        _marcar_error(resultado, str(error))
        return False
    except ErrorLecturaInstrumento as error:
        logger.warning("Resultado %s: no se pudo leer la hoja: %s", resultado.pk, error)
        _marcar_error(resultado, "No se pudo leer la hoja. Puedes reintentar o ingresar los datos a mano.")
        return False
    except Exception:
        # Un error no previsto no puede botar al worker: si no, la hoja vuelve a la cola cada
        # 5 minutos, se llama de nuevo a Bedrock y las capturas normales tampoco avanzan.
        logger.exception("Resultado %s: error inesperado al leer la hoja", resultado.pk)
        _marcar_error(resultado, "No se pudo leer la hoja. Puedes reintentar o ingresar los datos a mano.")
        return False
    try:
        with transaction.atomic():
            resultado.avisos = aplicar_lectura(resultado, lectura, instrumentos)
            resultado.estado = ResultadoInstrumento.Estado.POR_REVISAR
            resultado.error = ""
            resultado.save()
            registrar(resultado, RegistroCambio.Accion.LECTURA_IA)
    except Exception:
        logger.exception("Resultado %s: no se pudo guardar lo leído de la hoja", resultado.pk)
        resultado.refresh_from_db()
        _marcar_error(resultado, "No se pudo leer la hoja. Puedes reintentar o ingresar los datos a mano.")
        return False
    borrar_hoja(resultado)
    logger.info("Resultado %s: hoja leída y borrada", resultado.pk)
    return True


def _marcar_error(resultado, mensaje):
    resultado.estado = ResultadoInstrumento.Estado.ERROR
    resultado.error = mensaje
    resultado.save(update_fields=["estado", "error", "actualizado"])


def procesar_lecturas_pendientes(cliente=None):
    """Lee todas las hojas pendientes. Entrega (resultado, ok)."""
    while (resultado := tomar_siguiente_lectura()) is not None:
        yield resultado, procesar_lectura(resultado, cliente=cliente)


def reintentar_lectura(resultado):
    """Vuelve a poner en la cola una hoja que no se pudo leer y que todavía está guardada."""
    if not resultado.archivo:
        return False
    return ResultadoInstrumento.objects.filter(pk=resultado.pk, estado=ResultadoInstrumento.Estado.ERROR).update(
        estado=ResultadoInstrumento.Estado.POR_LEER, error="", actualizado=timezone.now(),
    ) == 1


def instrumentos_para_elegir():
    return Instrumento.objects.all()

