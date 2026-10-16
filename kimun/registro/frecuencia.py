"""Cuántas veces se observa a cada niño, frente al resto del curso.

Tres señales, redactadas como sugerencias y no como diagnóstico:

- Pocas observaciones (aviso, naranjo): en los últimos `VENTANA_AVISO` días
  el niño tiene `PROPORCION_AVISO` (⅔) o menos de la mediana del curso en esos
  mismos días. Con una mediana de 6 por semana, 4 o menos.
- Muy pocas observaciones (alerta, rojo): en los últimos `VENTANA_ALERTA` días,
  `PROPORCION_ALERTA` (⅓) o menos de la mediana del curso en esos días. Si hay
  alerta no se muestra además el aviso.
- Pendientes por revisar (aviso): el niño acumula muchas observaciones
  pendientes frente al resto: al menos `PENDIENTES_MINIMO` y al menos
  `PENDIENTES_VECES_MEDIANA` veces la mediana de pendientes del curso.

Cuentan las observaciones con niño, aceptadas o pendientes (las descartadas
no), que no son grupales ni salen de una nota de "todo el curso": esas llegan a
todos por igual y no muestran atención a cada niño. Se usa la fecha de la
observación; las pendientes cuentan cualquiera sea su fecha.

Sin referencia no se compara: una ventana cuya mediana no alcanza
`MEDIANA_MINIMA_SEMANAL` por semana (2 en 7 días, 4 en 14) no da señales, por
ejemplo en vacaciones. Un niño que ingresó después del primer día de una
ventana no entra en la mediana de esa ventana ni recibe su señal.

Los umbrales son nuestros y provisorios. `calcular_frecuencia` es pura;
`frecuencia_del_curso` es la única que consulta. Nada se guarda.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction

from django.db.models import Count
from django.utils import timezone

from .alertas import Gravedad, _numero, mediana
from .models import Observacion
from .procesamiento import NOMBRE_TODO_EL_CURSO

VENTANA_AVISO = 7
VENTANA_ALERTA = 14
PROPORCION_AVISO = Fraction(2, 3)
PROPORCION_ALERTA = Fraction(1, 3)
MEDIANA_MINIMA_SEMANAL = 2
PENDIENTES_MINIMO = 3
PENDIENTES_VECES_MEDIANA = 2


@dataclass(frozen=True)
class Ventana:
    """Los últimos `dias` días hasta hoy inclusive, con la mediana del curso en ellos."""

    dias: int
    desde: date
    hasta: date
    mediana: float | int | None  # None si ningún niño estaba en el curso desde el primer día

    @property
    def minima(self):
        return Fraction(MEDIANA_MINIMA_SEMANAL * self.dias, 7)

    @property
    def compara(self):
        """Si la mediana alcanza el mínimo para dar señales."""
        return self.mediana is not None and Fraction(self.mediana) >= self.minima

    @property
    def texto_mediana(self):
        return "–" if self.mediana is None else _numero(self.mediana)

    def incluye(self, nino):
        return nino.fecha_ingreso <= self.desde


def ventana(hoy, dias):
    return Ventana(dias, hoy - timedelta(days=dias - 1), hoy, None)


def _bajo(cantidad, referencia, proporcion):
    return Fraction(cantidad) <= proporcion * Fraction(referencia)


@dataclass(frozen=True)
class FrecuenciaNino:
    nino: object
    semana: int        # observaciones en la ventana del aviso
    dos_semanas: int   # observaciones en la ventana de la alerta
    pendientes: int
    gravedad: Gravedad  # de las pocas observaciones
    texto: str          # "" si no hay señal
    texto_corto: str
    pendientes_gravedad: Gravedad
    texto_pendientes: str


@dataclass(frozen=True)
class FrecuenciaCurso:
    aviso: Ventana
    alerta: Ventana
    mediana_pendientes: float | int | None
    filas: list  # FrecuenciaNino, en el orden de los niños

    @property
    def con_senal(self):
        """Los niños con pocas observaciones, primero los más urgentes y los menos observados."""
        filas = [f for f in self.filas if f.gravedad != Gravedad.NORMAL]
        return sorted(filas, key=lambda f: (-f.gravedad.orden, f.dos_semanas, f.semana, f.nino.nombre))

    @property
    def con_pendientes(self):
        return [f for f in self.filas if f.pendientes_gravedad != Gravedad.NORMAL]

    @property
    def promedio_semana(self):
        """Promedio de observaciones por niño en la ventana del aviso, entre los que comparan."""
        valores = [f.semana for f in self.filas if self.aviso.incluye(f.nino)]
        return Fraction(sum(valores), len(valores)) if valores else None

    @property
    def texto_promedio_semana(self):
        promedio = self.promedio_semana
        return "–" if promedio is None else f"{float(promedio):.1f}".replace(".", ",")


def _plural(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def calcular_frecuencia(ninos, fechas, pendientes, hoy):
    """Arma la frecuencia del curso. Pura: no consulta la base.

    - ninos: objetos con `pk`, `nombre` y `fecha_ingreso`, en el orden de las filas.
    - fechas: {id del niño: [fecha de cada observación que cuenta]}; las que
      quedan fuera de las ventanas se ignoran.
    - pendientes: {id del niño: observaciones pendientes que cuentan}.
    """
    aviso, alerta = ventana(hoy, VENTANA_AVISO), ventana(hoy, VENTANA_ALERTA)

    def contar(nino, v):
        return sum(1 for f in fechas.get(nino.pk, ()) if v.desde <= f <= v.hasta)

    semana = {n.pk: contar(n, aviso) for n in ninos}
    dos_semanas = {n.pk: contar(n, alerta) for n in ninos}
    aviso = Ventana(aviso.dias, aviso.desde, aviso.hasta, mediana([semana[n.pk] for n in ninos if aviso.incluye(n)]))
    alerta = Ventana(
        alerta.dias, alerta.desde, alerta.hasta, mediana([dos_semanas[n.pk] for n in ninos if alerta.incluye(n)])
    )
    mediana_pendientes = mediana([pendientes.get(n.pk, 0) for n in ninos])

    filas = []
    for nino in ninos:
        s, d, p = semana[nino.pk], dos_semanas[nino.pk], pendientes.get(nino.pk, 0)
        gravedad, texto, corto = Gravedad.NORMAL, "", ""
        if alerta.compara and alerta.incluye(nino) and _bajo(d, alerta.mediana, PROPORCION_ALERTA):
            gravedad = Gravedad.ALERTA
            corto = f"Muy pocas observaciones: {d} en {alerta.dias} días"
            texto = f"{corto} (mediana del curso: {alerta.texto_mediana})"
        elif aviso.compara and aviso.incluye(nino) and _bajo(s, aviso.mediana, PROPORCION_AVISO):
            gravedad = Gravedad.AVISO
            corto = f"Pocas observaciones: {s} en {aviso.dias} días"
            texto = f"{corto} (mediana del curso: {aviso.texto_mediana})"
        gravedad_p, texto_p = Gravedad.NORMAL, ""
        if p >= PENDIENTES_MINIMO and Fraction(p) >= PENDIENTES_VECES_MEDIANA * Fraction(mediana_pendientes or 0):
            gravedad_p = Gravedad.AVISO
            texto_p = f"{_plural(p, 'observación pendiente', 'observaciones pendientes')} de revisar"
        filas.append(FrecuenciaNino(nino, s, d, p, gravedad, texto, corto, gravedad_p, texto_p))
    return FrecuenciaCurso(aviso, alerta, mediana_pendientes, filas)


def _que_cuentan(curso):
    return Observacion.objects.filter(
        nino__curso=curso,
        grupal=False,
        estado__in=[Observacion.Estado.ACEPTADA, Observacion.Estado.PENDIENTE],
    ).exclude(nombre_detectado=NOMBRE_TODO_EL_CURSO)


def frecuencia_del_curso(curso, hoy=None, ninos=None):
    """FrecuenciaCurso de los niños del curso. Dos consultas (tres si no se pasan los niños)."""
    hoy = hoy or timezone.localdate()
    if ninos is None:
        ninos = list(curso.ninos.all())
    fechas = {}
    desde = hoy - timedelta(days=max(VENTANA_AVISO, VENTANA_ALERTA) - 1)
    for nino_id, fecha in _que_cuentan(curso).filter(fecha__range=(desde, hoy)).values_list("nino_id", "fecha"):
        fechas.setdefault(nino_id, []).append(fecha)
    # Sin order_by() el orden por defecto de Observacion entraría en el GROUP BY.
    pendientes = dict(
        _que_cuentan(curso).filter(estado=Observacion.Estado.PENDIENTE).order_by()
        .values("nino_id").annotate(cantidad=Count("id")).values_list("nino_id", "cantidad")
    )
    return calcular_frecuencia(ninos, fechas, pendientes, hoy)
