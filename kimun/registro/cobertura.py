"""Cobertura de evidencia (PLAN.md, Task 3).

Para cada niño, cuántas observaciones aceptadas respaldan cada OA de su nivel
educativo y la fecha de la más reciente. Los OA sin evidencia se destacan en
la ficha como sugerencia de qué observar, no como falta del niño.

Las funciones que calculan son puras: reciben los datos ya cargados y no
consultan la base. `cobertura_del_nino` es la única que consulta y les pasa
los datos. Nada se guarda: se calcula cada vez que se pide, para que refleje
cada observación nueva (PLAN.md, "Flujo de procesamiento", paso 7).
"""
from dataclasses import dataclass
from datetime import date

from .models import ObjetivoAprendizaje, Observacion


@dataclass(frozen=True)
class CoberturaOA:
    """Evidencia que respalda un OA para un niño."""

    oa: ObjetivoAprendizaje
    cantidad: int
    ultima_fecha: date | None

    @property
    def sin_evidencia(self):
        return self.cantidad == 0


def cobertura_por_oa(oas, evidencias):
    """Cuenta la evidencia de cada OA y toma la fecha más reciente.

    - oas: los OA a mostrar, en el orden en que se muestran.
    - evidencias: pares (id del OA, fecha de la observación), uno por cada OA
      etiquetado en cada observación que cuenta. Los pares de OA que no están
      en `oas` se ignoran.

    Devuelve [CoberturaOA] en el orden de `oas`. Los OA sin evidencia quedan
    con cantidad 0 y sin fecha.
    """
    cantidades = {}
    ultimas = {}
    for oa_id, fecha in evidencias:
        cantidades[oa_id] = cantidades.get(oa_id, 0) + 1
        if oa_id not in ultimas or fecha > ultimas[oa_id]:
            ultimas[oa_id] = fecha
    return [
        CoberturaOA(oa=oa, cantidad=cantidades.get(oa.pk, 0), ultima_fecha=ultimas.get(oa.pk))
        for oa in oas
    ]


def oas_sin_evidencia(coberturas):
    """Los OA sin ninguna observación, como sugerencia de qué observar."""
    return [c.oa for c in coberturas if c.sin_evidencia]


def agrupar_por_nucleo(coberturas):
    """{sigla del núcleo: [CoberturaOA]}, respetando el orden de entrada."""
    por_nucleo = {}
    for c in coberturas:
        por_nucleo.setdefault(c.oa.nucleo.sigla, []).append(c)
    return por_nucleo


def cobertura_del_nino(nino):
    """{sigla del núcleo: [CoberturaOA]} con todos los OA del nivel educativo del niño.

    Cuentan solo las observaciones aceptadas del niño. Las pendientes y
    descartadas no cuentan, y las notas grupales tampoco, porque no se usan
    para evaluar. Un núcleo sin OA en ese nivel educativo no aparece.
    Hace una cantidad fija de consultas, sin importar cuántos OA u
    observaciones haya.
    """
    nivel_educativo = nino.curso.nivel_educativo
    oas = (
        ObjetivoAprendizaje.objects.filter(nivel_educativo=nivel_educativo)
        .select_related("nucleo")
        .order_by("nucleo__orden", "nucleo__sigla", "numero")
    )
    evidencias = Observacion.oas.through.objects.filter(
        observacion__nino=nino,
        observacion__estado=Observacion.Estado.ACEPTADA,
        observacion__grupal=False,
        objetivoaprendizaje__nivel_educativo=nivel_educativo,
    ).values_list("objetivoaprendizaje_id", "observacion__fecha")
    return agrupar_por_nucleo(cobertura_por_oa(oas, evidencias))
