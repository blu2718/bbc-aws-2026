"""Nivel esperado, brechas y vista del curso (PLAN.md, Task 2).

Por cada niño y núcleo se muestran dos señales, redactadas como sugerencias de
revisión y no como diagnóstico ("sin juicios perentorios", Bases Curriculares):

- Bajo sus pares (señal principal): mediana del curso − nivel del niño.
- Bajo lo esperado: nivel esperado − nivel actual validado.

En ambas, una brecha de 2 es aviso y una de más de 2 es alerta. Los umbrales
son nuestros y provisorios. Además se avisa cuando un núcleo de un niño lleva
más de 14 días sin observaciones aceptadas, o nunca tuvo.

Las funciones que calculan son puras: reciben los datos ya cargados y no
consultan la base. `tabla_del_curso` es la única que consulta y les pasa los
datos. Nada se guarda: se calcula cada vez que se pide, para que refleje cada
observación y cada nivel nuevo (PLAN.md, "Flujo de procesamiento", paso 7).

Ni la cantidad de núcleos ni la de niveles están fijas en el código: salen de
los datos y de `Rubrica` (Integra pide pensar en 10 núcleos y 8 o 9 niveles).

Vista del jardín para la directora (Task 12): por núcleo, el promedio del
nivel actual validado de los niños de cada sala, comparado solo con las otras
salas del mismo nivel educativo. Si una sala queda `UMBRAL_SALA_BAJO` o más
niveles bajo el promedio de las demás, se sugiere revisarla. `comparar_salas`
es pura; `resumen_del_jardin` es la única que consulta.
"""
import math
import statistics
from dataclasses import dataclass
from datetime import date
from enum import Enum
from fractions import Fraction

from django.db.models import Count, Max
from django.utils import timezone

from .models import (
    NIVEL_MIN,
    DescriptorNivel,
    NivelEducativo,
    NivelValidado,
    Nucleo,
    Observacion,
    Rubrica,
    Semestre,
    texto_nivel,
)

# Umbrales provisorios (PLAN.md, "Rezago"): 0–1 normal, 2 aviso, más de 2 alerta.
BRECHA_AVISO = 2
DIAS_DATOS_RECIENTES = 14


class Gravedad(str, Enum):
    NORMAL = "normal"
    AVISO = "aviso"
    ALERTA = "alerta"

    @property
    def orden(self):
        return [Gravedad.NORMAL, Gravedad.AVISO, Gravedad.ALERTA].index(self)


class EstadoDatos(str, Enum):
    AL_DIA = "al_dia"
    DESACTUALIZADO = "desactualizado"
    SIN_DATOS = "sin_datos"


# --- Tiempo y nivel esperado -----------------------------------------------------------


def semestre_de_permanencia(fecha_ingreso, hoy, semestres):
    """En qué semestre de permanencia está el niño hoy (1, 2, 3...).

    Cuenta los semestres que ya empezaron y que no terminaron antes del
    ingreso, así que el semestre de ingreso cuenta completo aunque haya entrado
    a la mitad. En vacaciones se mantiene el último semestre cursado. Si
    ingresó en vacaciones, el semestre siguiente es su semestre 1, y mientras
    tanto ya está en su semestre 1.

    - semestres: objetos con `inicio` y `fin` (por ejemplo Semestre), en
      cualquier orden.

    Devuelve None si no hay semestres configurados.
    """
    if not semestres:
        return None
    cursados = sum(1 for s in semestres if s.fin >= fecha_ingreso and s.inicio <= hoy)
    return max(cursados, 1)


def nivel_esperado(semestre, metas, nivel_maximo):
    """Nivel esperado según la tabla de metas del curso.

    - metas: {semestre de permanencia: nivel esperado}, editable por la
      educadora (por defecto 1, 3, 5 y 7).
    - Después del último semestre de la tabla se espera el máximo de la
      rúbrica (hoy 8, lo esperado al egresar).
    - Un semestre sin meta usa la del semestre anterior más cercano; antes de
      la primera meta se espera el nivel 1.
    - Nunca supera el máximo de la rúbrica.

    Devuelve None si falta el semestre o la tabla está vacía: sin referencia no
    se compara. No supone que el avance sea lineal.
    """
    if semestre is None or not metas:
        return None
    if semestre > max(metas):
        return nivel_maximo
    anteriores = [s for s in metas if s <= semestre]
    esperado = metas[max(anteriores)] if anteriores else NIVEL_MIN
    return min(esperado, nivel_maximo)


# --- Brechas ---------------------------------------------------------------------------


def mediana(niveles):
    """Mediana de los niveles del curso en un núcleo, ignorando los vacíos.

    Con una cantidad par de niños es el promedio de los dos centrales (puede
    quedar en x,5). Devuelve None si no hay niveles.
    """
    valores = [n for n in niveles if n is not None]
    if not valores:
        return None
    m = statistics.median(valores)
    return int(m) if m == int(m) else m


def gravedad(brecha):
    """0–1 normal, 2 aviso, más de 2 alerta. Una brecha negativa (sobre la referencia) es normal."""
    if brecha is None or brecha < BRECHA_AVISO:
        return Gravedad.NORMAL
    if brecha > BRECHA_AVISO:
        return Gravedad.ALERTA
    return Gravedad.AVISO


def _numero(valor):
    """2 → "2"; 2.5 → "2,5" (formato chileno)."""
    return str(int(valor)) if valor == int(valor) else f"{valor:.1f}".replace(".", ",")


@dataclass(frozen=True)
class Brecha:
    """Distancia entre una referencia (la mediana del curso o lo esperado) y el nivel del niño."""

    PARES = "la mediana del curso"
    ESPERADO = "lo esperado"

    valor: float | int | None
    contra: str

    @classmethod
    def calcular(cls, referencia, nivel, contra):
        valor = None if referencia is None or nivel is None else referencia - nivel
        return cls(valor, contra)

    @property
    def gravedad(self):
        return gravedad(self.valor)

    @property
    def texto(self):
        """Sugerencia de revisión, o "" si no hay nada que mostrar."""
        if self.gravedad == Gravedad.NORMAL:
            return ""
        verbo = "Revisar" if self.gravedad == Gravedad.ALERTA else "Observar"
        return f"{verbo}: {_numero(self.valor)} niveles bajo {self.contra}"


# --- Datos desactualizados ---------------------------------------------------------------


def estado_datos(ultima_fecha, hoy, dias=DIAS_DATOS_RECIENTES):
    """Al día si la última observación aceptada tiene hasta `dias` días; si no, desactualizado o sin datos."""
    if ultima_fecha is None:
        return EstadoDatos.SIN_DATOS
    if (hoy - ultima_fecha).days > dias:
        return EstadoDatos.DESACTUALIZADO
    return EstadoDatos.AL_DIA


# --- Distribución del curso --------------------------------------------------------------


@dataclass(frozen=True)
class Distribucion:
    conteos: list  # [(nivel, cantidad de niños)], del 1 al máximo
    mas_frecuentes: tuple  # los niveles con más niños; varios si hay empate


def distribucion(niveles, nivel_maximo):
    """Cuántos niños hay en cada nivel, del 1 al máximo de la rúbrica, y en cuál está la mayoría.

    Si algún nivel supera el máximo (porque la rúbrica se achicó), se agregan
    columnas hasta ese nivel para no perder niños.
    """
    valores = [n for n in niveles if n is not None]
    techo = max([nivel_maximo, *valores])
    conteos = [(nivel, valores.count(nivel)) for nivel in range(NIVEL_MIN, techo + 1)]
    mayor = max((c for _, c in conteos), default=0)
    mas_frecuentes = tuple(nivel for nivel, c in conteos if mayor and c == mayor)
    return Distribucion(conteos, mas_frecuentes)


# --- Tabla del curso ---------------------------------------------------------------------


@dataclass(frozen=True)
class Celda:
    """Un niño en un núcleo."""

    nucleo: object
    nivel: int | None
    nombre_nivel: str
    pares: Brecha
    esperado: Brecha
    datos: EstadoDatos
    ultima_observacion: date | None
    dias_sin_observar: int | None

    @property
    def texto_nivel(self):
        return "–" if self.nivel is None else texto_nivel(self.nivel, self.nombre_nivel)

    @property
    def gravedad(self):
        """La más grave de las dos señales, para el color de la celda."""
        return max(self.pares.gravedad, self.esperado.gravedad, key=lambda g: g.orden)

    @property
    def senales(self):
        """Textos de las brechas que hay que mostrar, primero la de pares (la principal)."""
        return [b for b in (self.pares, self.esperado) if b.texto]

    @property
    def texto_datos(self):
        if self.datos == EstadoDatos.SIN_DATOS:
            return "Sin datos"
        if self.datos == EstadoDatos.DESACTUALIZADO:
            return f"Datos de hace {self.dias_sin_observar} días"
        return ""


@dataclass(frozen=True)
class FilaNino:
    nino: object
    semestre: int | None
    nivel_esperado: int | None
    celdas: list  # una por núcleo, en el orden de TablaCurso.nucleos

    @property
    def alertas(self):
        return sum(1 for c in self.celdas if c.gravedad == Gravedad.ALERTA)

    @property
    def avisos(self):
        return sum(1 for c in self.celdas if c.gravedad == Gravedad.AVISO)


@dataclass(frozen=True)
class DistribucionNucleo:
    nucleo: object
    conteos: list
    mas_frecuentes: tuple
    mediana: float | int | None
    nombres: dict  # {nivel: nombre}, vacío en la rúbrica provisoria

    @property
    def texto_mas_frecuentes(self):
        return " y ".join(texto_nivel(n, self.nombres.get(n, "")) for n in self.mas_frecuentes) or "–"

    @property
    def texto_mediana(self):
        return "–" if self.mediana is None else _numero(self.mediana)


@dataclass(frozen=True)
class TablaCurso:
    nucleos: list
    niveles: list  # columnas de la distribución: del 1 al máximo de la rúbrica
    filas: list
    distribuciones: list  # una por núcleo
    nivel_maximo: int
    hoy: date


def calcular_tabla(ninos, nucleos, niveles, ultimas_fechas, metas, semestres, nivel_maximo, hoy, nombres=None):
    """Arma la tabla del curso. Pura: no consulta la base.

    - ninos: objetos con `pk` y `fecha_ingreso`, en el orden de las filas.
    - nucleos: objetos con `pk` y `sigla`, en el orden de las columnas.
    - niveles: {(id del niño, id del núcleo): nivel actual validado}.
    - ultimas_fechas: {(id del niño, id del núcleo): fecha de la última
      observación aceptada}.
    - metas: {semestre de permanencia: nivel esperado}.
    - semestres: objetos con `inicio` y `fin`.
    - nombres: {sigla del núcleo: {nivel: nombre}}, para mostrar "3 · Desarrollando".
    """
    nombres = nombres or {}
    medianas = {k.pk: mediana([niveles.get((n.pk, k.pk)) for n in ninos]) for k in nucleos}

    filas = []
    for nino in ninos:
        semestre = semestre_de_permanencia(nino.fecha_ingreso, hoy, semestres)
        esperado = nivel_esperado(semestre, metas, nivel_maximo)
        celdas = []
        for nucleo in nucleos:
            nivel = niveles.get((nino.pk, nucleo.pk))
            ultima = ultimas_fechas.get((nino.pk, nucleo.pk))
            celdas.append(Celda(
                nucleo=nucleo,
                nivel=nivel,
                nombre_nivel=nombres.get(nucleo.sigla, {}).get(nivel, ""),
                pares=Brecha.calcular(medianas[nucleo.pk], nivel, Brecha.PARES),
                esperado=Brecha.calcular(esperado, nivel, Brecha.ESPERADO),
                datos=estado_datos(ultima, hoy),
                ultima_observacion=ultima,
                dias_sin_observar=None if ultima is None else (hoy - ultima).days,
            ))
        filas.append(FilaNino(nino, semestre, esperado, celdas))

    distribuciones = []
    for nucleo in nucleos:
        d = distribucion([niveles.get((n.pk, nucleo.pk)) for n in ninos], nivel_maximo)
        distribuciones.append(DistribucionNucleo(
            nucleo, d.conteos, d.mas_frecuentes, medianas[nucleo.pk], nombres.get(nucleo.sigla, {})
        ))
    # Todas las distribuciones con las mismas columnas, aunque alguna tenga un nivel sobre el máximo.
    techo = max(len(d.conteos) for d in distribuciones) if distribuciones else nivel_maximo
    return TablaCurso(
        nucleos=list(nucleos),
        niveles=list(range(NIVEL_MIN, max(techo, nivel_maximo) + 1)),
        filas=filas,
        distribuciones=[_completar(d, techo) for d in distribuciones],
        nivel_maximo=nivel_maximo,
        hoy=hoy,
    )


def _completar(d, techo):
    faltan = [(nivel, 0) for nivel in range(len(d.conteos) + 1, techo + 1)]
    if not faltan:
        return d
    return DistribucionNucleo(d.nucleo, d.conteos + faltan, d.mas_frecuentes, d.mediana, d.nombres)


def _ultimas_fechas(curso):
    """{(niño, núcleo): fecha de la última observación aceptada e individual}.

    Una observación cuenta para un núcleo si está etiquetada con él o con uno
    de sus OA.
    """
    filtro = {
        "observacion__nino__curso": curso,
        "observacion__estado": Observacion.Estado.ACEPTADA,
        "observacion__grupal": False,
    }
    por_nucleo = (
        Observacion.nucleos.through.objects.filter(**filtro)
        .values_list("observacion__nino_id", "nucleo_id")
        .annotate(ultima=Max("observacion__fecha"))
    )
    por_oa = (
        Observacion.oas.through.objects.filter(**filtro)
        .values_list("observacion__nino_id", "objetivoaprendizaje__nucleo_id")
        .annotate(ultima=Max("observacion__fecha"))
    )
    ultimas = {}
    for nino_id, nucleo_id, fecha in [*por_nucleo, *por_oa]:
        clave = (nino_id, nucleo_id)
        if clave not in ultimas or fecha > ultimas[clave]:
            ultimas[clave] = fecha
    return ultimas


def tabla_del_curso(curso, hoy=None):
    """TablaCurso con los niños del curso, todos los núcleos y la rúbrica de su nivel educativo.

    Hace una cantidad fija de consultas, sin importar cuántos niños,
    validaciones u observaciones haya.
    """
    hoy = hoy or timezone.localdate()
    nivel_educativo = curso.nivel_educativo
    nucleos = list(Nucleo.objects.all())
    ninos = list(curso.ninos.all())
    niveles = {}
    filas = (
        NivelValidado.objects.filter(nino__curso=curso)
        .order_by("nino_id", "nucleo_id", "-fecha", "-creado", "-id")
        .values_list("nino_id", "nucleo_id", "nivel")
    )
    for nino_id, nucleo_id, nivel in filas:
        niveles.setdefault((nino_id, nucleo_id), nivel)  # el primero es el más reciente
    return calcular_tabla(
        ninos=ninos,
        nucleos=nucleos,
        niveles=niveles,
        ultimas_fechas=_ultimas_fechas(curso),
        metas=dict(curso.metas.values_list("semestre_permanencia", "nivel_esperado")),
        semestres=list(Semestre.objects.all()),
        nivel_maximo=Rubrica.nivel_maximo(nivel_educativo),
        hoy=hoy,
        nombres=DescriptorNivel.nombres_por_nucleo(nivel_educativo),
    )


# --- Comparación de salas del jardín (Task 12) -------------------------------------------

# Provisorio (PLAN.md, Task 12): una sala 2 o más niveles bajo el promedio de las
# demás salas de su nivel educativo genera una sugerencia de revisión.
UMBRAL_SALA_BAJO = 2


def promedio(niveles):
    """Promedio exacto (Fraction) de los niveles, ignorando los vacíos. None si no hay niveles.

    Exacto para que el borde del umbral no dependa del redondeo de los
    decimales (16/3 − 10/3 es justo 2).
    """
    valores = [n for n in niveles if n is not None]
    if not valores:
        return None
    return Fraction(sum(valores), len(valores))


def _texto_decimal(valor):
    """Con 1 decimal, redondeando la mitad hacia arriba, y coma decimal: 14/3 → "4,7"; 3 → "3"."""
    redondeado = Fraction(math.floor(Fraction(valor) * 10 + Fraction(1, 2)), 10)
    return _numero(float(redondeado))


def _texto_niveles(valor):
    texto = _texto_decimal(valor)
    return f"{texto} nivel" if texto == "1" else f"{texto} niveles"


@dataclass(frozen=True)
class CeldaSala:
    """Una sala en un núcleo: su promedio y el de las demás salas de su nivel educativo."""

    curso: object
    nucleo: object
    promedio: Fraction | None
    promedio_demas: Fraction | None  # None si no hay otra sala con datos con quién comparar
    umbral: object

    @property
    def diferencia(self):
        """Cuánto queda la sala bajo el promedio de las demás (negativo si queda sobre él)."""
        if self.promedio is None or self.promedio_demas is None:
            return None
        return self.promedio_demas - self.promedio

    @property
    def alerta(self):
        return self.diferencia is not None and self.diferencia >= self.umbral

    @property
    def texto_promedio(self):
        return "–" if self.promedio is None else _texto_decimal(self.promedio)

    @property
    def texto_alerta(self):
        """Sugerencia de revisión para la lista de la directora, o "" si no hay alerta."""
        if not self.alerta:
            return ""
        return (
            f"Revisar: {self.curso.nombre}, {_texto_niveles(self.diferencia)} "
            f"bajo el resto del jardín en {self.nucleo.nombre}"
        )

    @property
    def texto_celda(self):
        """Texto corto de la celda (la tabla ya dice la sala y el núcleo), o "" si no hay alerta."""
        if not self.alerta:
            return ""
        return f"Revisar: {_texto_niveles(self.diferencia)} bajo el resto"


@dataclass(frozen=True)
class FilaNucleo:
    nucleo: object
    celdas: list  # una por sala, en el orden de GrupoSalas.cursos


@dataclass(frozen=True)
class GrupoSalas:
    """Las salas de un mismo nivel educativo: solo se comparan entre ellas."""

    nivel_educativo: str
    nombre: str
    cursos: list
    filas: list  # una por núcleo

    @property
    def comparable(self):
        return len(self.cursos) > 1


@dataclass(frozen=True)
class ResumenJardin:
    grupos: list
    alertas: list  # CeldaSala con alerta, la mayor diferencia primero
    umbral: object

    @property
    def texto_umbral(self):
        return _texto_niveles(self.umbral)


def comparar_salas(cursos, nucleos, niveles, umbral=UMBRAL_SALA_BAJO):
    """Compara las salas del jardín por núcleo. Pura: no consulta la base.

    - cursos: objetos con `pk`, `nombre` y `nivel_educativo`, en el orden de
      las columnas.
    - nucleos: objetos con `pk` y `nombre`, en el orden de las filas.
    - niveles: {(id del curso, id del núcleo): [nivel actual de cada niño]}.

    El promedio de las demás es la media simple de los promedios de las otras
    salas del mismo nivel educativo que tienen datos en el núcleo: cada sala
    pesa lo mismo, como en el ejemplo de Integra (dos salas en 6 y una en 3).
    Una sala sin datos en un núcleo no tiene alerta ni entra en el promedio de
    las demás. Las alertas van de mayor a menor diferencia; si empatan, por
    núcleo y luego por sala. Nada supone una cantidad de niveles ni de núcleos.
    """
    orden_niveles = [valor for valor, _ in NivelEducativo.choices]
    nombres = dict(NivelEducativo.choices)
    por_nivel = {}
    for curso in cursos:
        por_nivel.setdefault(curso.nivel_educativo, []).append(curso)
    claves = sorted(
        por_nivel, key=lambda v: (orden_niveles.index(v) if v in orden_niveles else len(orden_niveles), v)
    )
    posicion_curso = {curso.pk: i for i, curso in enumerate(cursos)}

    grupos, alertas = [], []
    for nivel_educativo in claves:
        salas = por_nivel[nivel_educativo]
        filas = []
        for orden_nucleo, nucleo in enumerate(nucleos):
            promedios = {c.pk: promedio(niveles.get((c.pk, nucleo.pk), [])) for c in salas}
            celdas = []
            for curso in salas:
                otros = [p for pk, p in promedios.items() if pk != curso.pk and p is not None]
                demas = sum(otros, Fraction(0)) / len(otros) if otros else None
                celda = CeldaSala(curso, nucleo, promedios[curso.pk], demas, umbral)
                celdas.append(celda)
                if celda.alerta:
                    alertas.append((-celda.diferencia, orden_nucleo, posicion_curso[curso.pk], celda))
            filas.append(FilaNucleo(nucleo, celdas))
        grupos.append(GrupoSalas(nivel_educativo, nombres.get(nivel_educativo, nivel_educativo), salas, filas))
    alertas.sort(key=lambda a: a[:3])
    return ResumenJardin(grupos=grupos, alertas=[a[3] for a in alertas], umbral=umbral)


def resumen_del_jardin(jardin, umbral=UMBRAL_SALA_BAJO):
    """ResumenJardin con las salas del jardín y todos los núcleos.

    El nivel actual de cada niño en un núcleo es su NivelValidado más
    reciente, igual que en la tabla del curso. Cada curso trae
    `cantidad_ninos`. Hace una cantidad fija de consultas.
    """
    cursos = list(jardin.cursos.annotate(cantidad_ninos=Count("ninos")))
    nucleos = list(Nucleo.objects.all())
    actuales = {}
    filas = (
        NivelValidado.objects.filter(nino__curso__jardin=jardin)
        .order_by("nino_id", "nucleo_id", "-fecha", "-creado", "-id")
        .values_list("nino__curso_id", "nino_id", "nucleo_id", "nivel")
    )
    for curso_id, nino_id, nucleo_id, nivel in filas:
        actuales.setdefault((curso_id, nino_id, nucleo_id), nivel)  # el primero es el más reciente
    niveles = {}
    for (curso_id, _nino_id, nucleo_id), nivel in actuales.items():
        niveles.setdefault((curso_id, nucleo_id), []).append(nivel)
    return comparar_salas(cursos, nucleos, niveles, umbral=umbral)
