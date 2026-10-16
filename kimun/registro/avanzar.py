"""Qué observar para avanzar al nivel siguiente (PLAN.md, "Pasos a seguir").

La ficha y la tarjeta del suceso muestran, junto a la descripción del nivel
siguiente de la rúbrica, conductas concretas que observar. Todo sale de datos
que ya están cargados; nada se genera con IA:

- En los núcleos con rúbrica provisoria, el nivel siguiente se describe con
  las conductas del Programa Pedagógico de Transición (`Manifestacion`) del
  año que le corresponde según el mapeo provisorio (`rubrica.MAPEO_PROVISORIO`:
  niveles 2 a 4 son NT1, 5 a 8 son NT2). Primero van los OA sin evidencia del
  niño, porque son los que todavía no se han observado.
- En los núcleos con rúbrica de Integra no se usa ese mapeo, porque sus
  niveles no siguen la lógica de NT1 y NT2: se muestran la descripción, la
  conducta y los ejemplos del nivel siguiente, y los OA sin evidencia.

Las funciones que calculan son puras; `manifestaciones_por_oa` es la única que
consulta.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import Manifestacion
from .rubrica import MAPEO_PROVISORIO

# OA sin evidencia que se muestran abiertos; el resto queda plegado.
LIMITE_PRIORITARIOS = 3
# Conductas por OA en la tarjeta del suceso, que es más chica que la ficha.
LIMITE_TARJETA = 3

ANIO_POR_NIVEL = {nivel: anio for nivel, anio, _criterio in MAPEO_PROVISORIO if anio}


def anio_del_nivel(nivel):
    """'NT1' o 'NT2' para un nivel de la rúbrica provisoria; '' si el mapeo no lo cubre."""
    return ANIO_POR_NIVEL.get(nivel, "") if nivel is not None else ""


@dataclass(frozen=True)
class ConductasOA:
    """Las conductas del Programa de un OA para un año (NT1 o NT2)."""

    oa: object
    sin_evidencia: bool
    conductas: tuple


@dataclass(frozen=True)
class ParaAvanzar:
    """Qué observar en un núcleo para el nivel siguiente.

    - anio: año de las conductas ('NT1' o 'NT2'), o '' si no se muestran conductas.
    - prioritarias: OA sin evidencia, con sus conductas, hasta `LIMITE_PRIORITARIOS`.
    - otras: los demás OA con conductas para ese año (plegados en la ficha).
    - sin_evidencia: todos los OA del núcleo sin evidencia del niño.
    """

    anio: str = ""
    prioritarias: list = field(default_factory=list)
    otras: list = field(default_factory=list)
    sin_evidencia: list = field(default_factory=list)

    @property
    def tiene_conductas(self):
        return bool(self.prioritarias or self.otras)


def manifestaciones_por_oa(oa_ids=None, nivel_educativo=None):
    """{id del OA: {año: [texto, ...]}} en el orden del Programa. Una consulta.

    Se filtra por OA o por nivel educativo; sin filtros trae todas.
    """
    qs = Manifestacion.objects.order_by("oa_id", "anio", "orden")
    if oa_ids is not None:
        qs = qs.filter(oa_id__in=list(oa_ids))
    if nivel_educativo is not None:
        qs = qs.filter(oa__nivel_educativo=nivel_educativo)
    resultado = {}
    for oa_id, anio, texto in qs.values_list("oa_id", "anio", "texto"):
        resultado.setdefault(oa_id, {}).setdefault(anio, []).append(texto)
    return resultado


def para_avanzar(cobertura, manifestaciones, nivel_siguiente, provisorio, limite=LIMITE_PRIORITARIOS):
    """`ParaAvanzar` de un núcleo. Pura.

    - cobertura: [CoberturaOA] del núcleo para el niño, en el orden de los OA.
    - manifestaciones: lo que devuelve `manifestaciones_por_oa`.
    - nivel_siguiente: el nivel al que avanzaría, o None si ya está en el máximo.
    - provisorio: si el núcleo usa la rúbrica provisoria. Solo entonces se
      muestran las conductas del Programa, porque solo ahí el nivel tiene un año.
    """
    sin_evidencia = [c.oa for c in cobertura if c.sin_evidencia]
    anio = anio_del_nivel(nivel_siguiente) if provisorio else ""
    if not anio:
        return ParaAvanzar(sin_evidencia=sin_evidencia)
    con_conductas = [
        ConductasOA(c.oa, c.sin_evidencia, tuple(manifestaciones.get(c.oa.pk, {}).get(anio, ())))
        for c in cobertura
    ]
    con_conductas = [c for c in con_conductas if c.conductas]
    # Primero los OA sin evidencia (en el orden de los OA), después los demás.
    ordenadas = [c for c in con_conductas if c.sin_evidencia] + [c for c in con_conductas if not c.sin_evidencia]
    prioritarias = [c for c in ordenadas if c.sin_evidencia][:limite]
    otras = [c for c in ordenadas if c not in prioritarias]
    return ParaAvanzar(anio=anio, prioritarias=prioritarias, otras=otras, sin_evidencia=sin_evidencia)


def conductas_de_oas(oas, manifestaciones, anio, limite=LIMITE_TARJETA):
    """[ConductasOA] de los OA de un suceso para un año, hasta `limite` conductas por OA. Pura."""
    if not anio:
        return []
    resultado = []
    for oa in oas:
        conductas = tuple(manifestaciones.get(oa.pk, {}).get(anio, ())[:limite])
        if conductas:
            resultado.append(ConductasOA(oa, False, conductas))
    return resultado
