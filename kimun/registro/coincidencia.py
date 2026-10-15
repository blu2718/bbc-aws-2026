"""Emparejamiento de `nombre_detectado` con los niños del curso (PLAN.md, "Flujo de procesamiento", paso 4).

Se hace en nuestro código y no en el modelo, para que el resultado sea predecible
y testeable:

1. Se normaliza (sin tildes, en minúsculas y con los espacios colapsados).
2. Coincidencia exacta con el nombre completo, el nombre de pila o un alias.
3. Si no hay exacta, comparación aproximada con difflib sobre un umbral.

Si hay más de un candidato el resultado es "ambiguo"; si no hay ninguno, "desconocido".
En los dos casos la observación queda sin niño y la educadora lo resuelve en la revisión.
"""
import difflib
import unicodedata
from dataclasses import dataclass

from django.conf import settings

# "Nayara" frente a "Naiara" da 0,83; "Pedro" frente a "Emilio", 0,18.
UMBRAL_POR_DEFECTO = 0.8

EXACTA = "exacta"
APROXIMADA = "aproximada"
AMBIGUO = "ambiguo"
DESCONOCIDO = "desconocido"


@dataclass(frozen=True)
class Coincidencia:
    """`nino` es None si la razón es AMBIGUO o DESCONOCIDO."""

    nino: object
    razon: str
    candidatos: tuple = ()

    @property
    def encontrada(self):
        return self.nino is not None


def normalizar(texto):
    """'  SOFÍA   Muñoz ' -> 'sofia munoz'."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_tildes.casefold().split())


def claves(nino):
    """Formas normalizadas con que se puede nombrar al niño: nombre completo, de pila y alias."""
    completo = normalizar(nino.nombre)
    formas = [completo, completo.split(" ")[0]] + [normalizar(a) for a in (nino.alias or []) if isinstance(a, str)]
    return {f for f in formas if f}


def es_exacta(nombre_detectado, nino):
    """True si el nombre calza exacto (normalizado) con el nombre completo, de pila o un alias del niño."""
    return normalizar(nombre_detectado) in claves(nino)


def umbral_configurado():
    return getattr(settings, "COINCIDENCIA_UMBRAL", UMBRAL_POR_DEFECTO)


def _unico(candidatos, razon):
    if len(candidatos) == 1:
        return Coincidencia(candidatos[0], razon, tuple(candidatos))
    return Coincidencia(None, AMBIGUO, tuple(candidatos))


def emparejar(nombre_detectado, ninos, umbral=None):
    """Busca a qué niño de `ninos` corresponde `nombre_detectado`.

    - ninos: iterable de `Nino` (o cualquier objeto con `nombre` y `alias`).
    - umbral: entre 0 y 1; por defecto `settings.COINCIDENCIA_UMBRAL` o UMBRAL_POR_DEFECTO.
    """
    umbral = umbral_configurado() if umbral is None else umbral
    buscado = normalizar(nombre_detectado)
    ninos = list(ninos)
    if not buscado:
        return Coincidencia(None, DESCONOCIDO)

    exactos = [n for n in ninos if buscado in claves(n)]
    if exactos:
        return _unico(exactos, EXACTA)

    aproximados = [
        n for n in ninos
        if max((difflib.SequenceMatcher(None, buscado, clave).ratio() for clave in claves(n)), default=0) >= umbral
    ]
    if aproximados:
        return _unico(aproximados, APROXIMADA)
    return Coincidencia(None, DESCONOCIDO)
