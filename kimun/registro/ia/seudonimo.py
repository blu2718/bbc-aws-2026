"""Sustituye identidades conocidas del curso antes de proponer niveles.

Funciones sin Django, red ni logs. Recibe diccionarios con nombre, codigo y
alias opcionales. No infiere identidades por similitud: las coincidencias
compartidas se ocultan con un marcador neutral.
"""
import json
import re
import unicodedata
from collections.abc import Mapping

MARCADOR_AMBIGUO = "[NINO_AMBIGUO]"
_CODIGO = re.compile(r"N-[0-9A-F]{6}\Z")


def _normalizar(texto):
    """Texto comparable y posiciones originales; nunca devuelve este texto al usuario."""
    caracteres, posiciones = [], []
    for i, caracter in enumerate(texto):
        normal = "".join(c for c in unicodedata.normalize("NFD", caracter.casefold())
                         if not unicodedata.category(c).startswith("M"))
        if not normal and posiciones:
            # Incluir las tildes descompuestas al sustituir el último carácter del nombre.
            posiciones[-1] = (posiciones[-1][0], i + 1)
        for c in normal:
            caracteres.append(c)
            posiciones.append((i, i + 1))
    return "".join(caracteres), posiciones


def _clave(texto):
    return " ".join(_normalizar(texto)[0].split())


class Seudonimizador:
    """Preparar una vez por curso y reutilizar para citas, ejemplos y envío.

    Reconoce el nombre completo, sus prefijos (p. ej., María José y María) y
    los alias explícitos. Otros nombres de uso deben declararse como alias.
    Las claves de objetos JSON deben ser campos estructurales sin identidades.
    """

    def __init__(self, ninos):
        variantes, codigos = {}, set()
        for nino in ninos:
            if not isinstance(nino, Mapping):
                raise ValueError("Se requieren diccionarios de identidad del curso.")
            nombre, codigo, alias = nino.get("nombre"), nino.get("codigo"), nino.get("alias", [])
            if not isinstance(nombre, str) or not _clave(nombre):
                raise ValueError("Cada identidad requiere un nombre no vacío.")
            if not isinstance(codigo, str) or not _CODIGO.fullmatch(codigo):
                raise ValueError("Cada identidad requiere un código con formato N-XXXXXX hexadecimal.")
            if codigo in codigos:
                raise ValueError("Los códigos del curso deben ser únicos.")
            if not isinstance(alias, (list, tuple)) or any(not isinstance(a, str) for a in alias):
                raise ValueError("Los alias deben ser una lista de textos.")
            codigos.add(codigo)
            partes = _clave(nombre).split()
            nombres = [" ".join(partes[:i]) for i in range(1, len(partes) + 1)]
            nombres.extend(_clave(a) for a in alias)
            for variante in nombres:
                if variante:
                    variantes.setdefault(variante, set()).add(codigo)
        self._reemplazos = {
            nombre: next(iter(opciones)) if len(opciones) == 1 else MARCADOR_AMBIGUO
            for nombre, opciones in variantes.items()
        }
        # Una sola pasada: los códigos insertados nunca se vuelven a interpretar como nombres.
        # Proteger además códigos y marcadores ya existentes permite repetir la operación.
        patrones = [r"(?<!\w)n-[0-9a-f]{6}(?!\w)", re.escape(MARCADOR_AMBIGUO.casefold())]
        if variantes:
            alternativas = [r"\s+".join(re.escape(p) for p in nombre.split())
                            for nombre in sorted(variantes, key=lambda n: (-len(n), n))]
            patrones.append(r"(?<!\w)(?P<identidad>" + "|".join(alternativas) + r")(?!\w)")
        self._patron = re.compile("|".join(patrones))
        self._tiene_identidades = bool(variantes)

    def texto(self, texto):
        """Sustituye coincidencias completas conservando literalmente el resto del texto."""
        if not isinstance(texto, str):
            raise TypeError("Se requiere un texto para sustituir identidades.")
        if not self._tiene_identidades:
            return texto
        normal, posiciones = _normalizar(texto)
        partes, ultimo = [], 0
        for coincidencia in self._patron.finditer(normal):
            inicio = posiciones[coincidencia.start()][0]
            fin = posiciones[coincidencia.end() - 1][1]
            partes.append(texto[ultimo:inicio])
            if coincidencia.group("identidad") is not None:
                partes.append(self._reemplazos[_clave(coincidencia.group("identidad"))])
            else:
                partes.append(texto[inicio:fin])
            ultimo = fin
        partes.append(texto[ultimo:])
        return "".join(partes)

    def datos(self, valor):
        """Copia datos JSON y limpia todas sus hojas textuales, sin mutar el original.

        No convierte objetos arbitrarios a texto ni admite identidades en claves:
        podría filtrar datos o cambiar la estructura del contrato de respuesta.
        """
        if isinstance(valor, str):
            return self.texto(valor)
        if valor is None or isinstance(valor, (bool, int, float)):
            return valor
        if isinstance(valor, list):
            return [self.datos(elemento) for elemento in valor]
        if isinstance(valor, dict):
            resultado = {}
            for clave, contenido in valor.items():
                if not isinstance(clave, str) or self.texto(clave) != clave:
                    raise ValueError("Las claves JSON deben ser campos estructurales sin identidades.")
                resultado[clave] = self.datos(contenido)
            return resultado
        raise TypeError("Solo se admiten textos y estructuras JSON.")

    def invocar(self, cliente, system, mensaje, herramienta):
        """Limpia el envío a un ClienteBedrock real o falso sin añadir el diccionario.

        El mensaje puede ser texto o datos JSON. Un JSON ya serializado se
        decodifica antes de limpiar para reconocer también nombres con escapes.
        La construcción del prompt de nivel corresponde al punto 3 de la Task 7.
        """
        if isinstance(mensaje, str):
            try:
                estructurado = json.loads(mensaje)
            except json.JSONDecodeError:
                limpio = self.texto(mensaje)
            else:
                limpio = json.dumps(self.datos(estructurado), ensure_ascii=False)
        else:
            limpio = json.dumps(self.datos(mensaje), ensure_ascii=False)
        return cliente.invocar_herramienta(self.texto(system), limpio, self.datos(herramienta))


def seudonimizar_texto(texto, ninos):
    """Atajo para una sola cita; para varias, reutilizar un Seudonimizador."""
    return Seudonimizador(ninos).texto(texto)
