"""Cobertura de evidencia (PLAN.md, Tasks 2 y 3).

- Por niño (Task 3): cuántas observaciones aceptadas respaldan cada OA de su
  nivel educativo y la fecha de la más reciente. Los OA sin evidencia se
  destacan en la ficha como sugerencia de qué observar, no como falta del niño.
- Por quincena (Task 2): por núcleo, cuántas observaciones aceptadas tiene el
  curso y cuántos niños tienen al menos una. Los núcleos sin observaciones se
  destacan, porque la Política de Calidad de Integra pide una oferta que cubra
  todos los núcleos en cada quincena.

Las funciones que calculan son puras: reciben los datos ya cargados y no
consultan la base. `cobertura_del_nino` y `cobertura_quincena_del_curso` son
las únicas que consultan y les pasan los datos. Nada se guarda: se calcula
cada vez que se pide, para que refleje cada observación nueva (PLAN.md,
"Flujo de procesamiento", paso 7).
"""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from .models import Nucleo, ObjetivoAprendizaje, Observacion


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


# --- Resumen de la quincena ------------------------------------------------------------


@dataclass(frozen=True)
class Quincena:
    """Del 1 al 15 o del 16 a fin de mes, según la fecha de la observación."""

    inicio: date
    fin: date

    def contiene(self, fecha):
        return self.inicio <= fecha <= self.fin

    def anterior(self):
        return quincena_de(self.inicio - timedelta(days=1))

    def siguiente(self):
        return quincena_de(self.fin + timedelta(days=1))


def quincena_de(fecha):
    if fecha.day <= 15:
        return Quincena(fecha.replace(day=1), fecha.replace(day=15))
    ultimo = calendar.monthrange(fecha.year, fecha.month)[1]
    return Quincena(fecha.replace(day=16), fecha.replace(day=ultimo))


@dataclass(frozen=True)
class CoberturaNucleoQuincena:
    nucleo: object
    observaciones: int
    ninos: int

    @property
    def sin_observaciones(self):
        return self.observaciones == 0


def cobertura_quincena(nucleos, evidencias, quincena):
    """Por núcleo, observaciones de la quincena y niños con al menos una.

    - nucleos: los núcleos a mostrar, en orden. Todos aparecen, aunque no
      tengan observaciones.
    - evidencias: tuplas (id de la observación, id del niño, fecha, id del
      núcleo). Una observación etiquetada con un núcleo y con uno de sus OA
      puede venir repetida: cuenta una vez. Las fechas fuera de la quincena se
      ignoran.

    Devuelve [CoberturaNucleoQuincena] en el orden de `nucleos`.
    """
    observaciones, ninos = {}, {}
    for obs_id, nino_id, fecha, nucleo_id in evidencias:
        if not quincena.contiene(fecha):
            continue
        observaciones.setdefault(nucleo_id, set()).add(obs_id)
        ninos.setdefault(nucleo_id, set()).add(nino_id)
    return [
        CoberturaNucleoQuincena(n, len(observaciones.get(n.pk, ())), len(ninos.get(n.pk, ())))
        for n in nucleos
    ]


def cobertura_quincena_del_curso(curso, quincena, nucleos=None):
    """[CoberturaNucleoQuincena] del curso en la quincena, con todos los núcleos.

    Cuentan las observaciones aceptadas de los niños del curso. Las notas
    grupales no cuentan, porque son contexto y no se usan para evaluar. Una
    observación cuenta para un núcleo si está etiquetada con él o con uno de
    sus OA. Hace tres consultas (dos si se pasan los núcleos).
    """
    if nucleos is None:
        nucleos = list(Nucleo.objects.all())
    filtro = {
        "observacion__nino__curso": curso,
        "observacion__estado": Observacion.Estado.ACEPTADA,
        "observacion__grupal": False,
        "observacion__fecha__range": (quincena.inicio, quincena.fin),
    }
    columnas = ("observacion_id", "observacion__nino_id", "observacion__fecha")
    por_nucleo = Observacion.nucleos.through.objects.filter(**filtro).values_list(*columnas, "nucleo_id")
    por_oa = Observacion.oas.through.objects.filter(**filtro).values_list(
        *columnas, "objetivoaprendizaje__nucleo_id"
    )
    return cobertura_quincena(nucleos, [*por_nucleo, *por_oa], quincena)
