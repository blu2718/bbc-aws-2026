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
niveles bajo el promedio de las demás, se sugiere revisarla. Solo entran los
niveles que fijó una educadora (`validado_por`), y solo las salas con al menos
`PROPORCION_MINIMA_VALIDADOS` de sus niños con nivel validado en el núcleo.
Los promedios se redondean a un decimal y la alerta se calcula con esos mismos
valores redondeados, para que coincida con lo que muestra la tabla.
`comparar_salas` es pura; `resumen_del_jardin` es la única que consulta.
"""
import math
import statistics
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from fractions import Fraction

from django.db.models import Count, Max
from django.utils import timezone

from .models import (
    Captura,
    NIVEL_MIN,
    DescriptorNivel,
    NivelEducativo,
    NivelValidado,
    Nino,
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

    @property
    def texto_nivel_general(self):
        """Promedio de sus núcleos, con un decimal y coma, como en la vista del jardín. Es solo una referencia:
        el nivel se decide por núcleo (FAQ de Integra). "–" si no tiene niveles."""
        return texto_nivel_general([c.nivel for c in self.celdas])


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
        Observacion.nucleos.through.objects.filter(**filtro).exclude(observacion__captura__estado=Captura.Estado.EN_RESGUARDO)
        .values_list("observacion__nino_id", "nucleo_id")
        .annotate(ultima=Max("observacion__fecha"))
    )
    por_oa = (
        Observacion.oas.through.objects.filter(**filtro).exclude(observacion__captura__estado=Captura.Estado.EN_RESGUARDO)
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

# Provisorios (PLAN.md, Task 12), configurables al llamar a `comparar_salas` y
# `resumen_del_jardin`:
# - una sala 2 o más niveles bajo el promedio de las demás salas de su nivel
#   educativo genera una sugerencia de revisión;
# - una sala entra en la comparación de un núcleo solo si al menos la mitad de
#   sus niños tiene nivel validado en ese núcleo (justo la mitad sí entra).
UMBRAL_SALA_BAJO = 2
PROPORCION_MINIMA_VALIDADOS = Fraction(1, 2)

SIN_DATOS_SUFICIENTES = "Sin datos suficientes"


def promedio(niveles):
    """Promedio exacto (Fraction) de los niveles, ignorando los vacíos. None si no hay niveles."""
    valores = [n for n in niveles if n is not None]
    if not valores:
        return None
    return Fraction(sum(valores), len(valores))


def redondear(valor):
    """Decimal con un decimal, la mitad lejos del cero (como ROUND_HALF_UP de Decimal). None si es None.

    Se calcula desde la fracción exacta, sin pasar por float ni por una
    división con precisión limitada: 76/25 (3,04) da 3.0, 61/20 (3,05) da 3.1
    y 14/3 da 4.7.
    """
    if valor is None:
        return None
    exacto = Fraction(valor)
    decimas = math.floor(abs(exacto) * 10 + Fraction(1, 2))
    return Decimal(decimas if exacto >= 0 else -decimas).scaleb(-1)


def _texto_un_decimal(valor):
    """Siempre con un decimal, para que se vea que está redondeado, y coma decimal: 3 → "3,0"; 14/3 → "4,7"."""
    return f"{redondear(valor):.1f}".replace(".", ",")


def texto_nivel_general(niveles):
    """Nivel general de un niño: promedio de sus núcleos con un decimal y coma ("4,4"). "–" si no hay niveles.

    Integra sugiere el promedio de los núcleos si se necesita un nivel general;
    se muestra marcado como referencia, porque el nivel se decide por núcleo.
    """
    valor = promedio(niveles)
    return "–" if valor is None else _texto_un_decimal(valor)


def _texto_niveles(texto):
    return f"{texto} nivel" if texto == "1" else f"{texto} niveles"


@dataclass(frozen=True)
class CeldaSala:
    """Una sala en un núcleo: su promedio y el de las demás salas de su nivel educativo, ya redondeados.

    La tabla muestra `promedio` y la alerta se decide con `diferencia`, que sale
    de los mismos valores redondeados: lo que se ve y lo que dispara la alerta
    coinciden siempre.
    """

    curso: object
    nucleo: object
    promedio: Decimal | None  # a un decimal; None si la sala no tiene datos suficientes en el núcleo
    promedio_demas: Decimal | None  # a un decimal; None si no hay otra sala con datos suficientes
    umbral: object
    validados: int = 0  # niños de la sala con nivel validado en el núcleo
    ninos: int = 0  # niños de la sala

    @property
    def suficiente(self):
        """Si la sala entra en la comparación de este núcleo (tiene el mínimo de niños con nivel validado)."""
        return self.promedio is not None

    @property
    def diferencia(self):
        """Cuánto queda la sala bajo el promedio de las demás (negativo si queda sobre él), a un decimal.

        Los dos valores ya tienen un decimal, así que la resta es exacta. Si la
        diferencia es positiva (la única que puede generar alerta), es la misma
        que redondear a un decimal la distancia entre el promedio sin redondear
        de los promedios mostrados de las demás y el promedio mostrado de la sala.
        """
        if self.promedio is None or self.promedio_demas is None:
            return None
        return self.promedio_demas - self.promedio

    @property
    def alerta(self):
        return self.diferencia is not None and Fraction(self.diferencia) >= Fraction(self.umbral)

    @property
    def texto_promedio(self):
        return SIN_DATOS_SUFICIENTES if self.promedio is None else _texto_un_decimal(self.promedio)

    @property
    def texto_alerta(self):
        """Sugerencia de revisión para la lista de la directora, o "" si no hay alerta."""
        if not self.alerta:
            return ""
        return (
            f"Revisar: {self.curso.nombre}, {_texto_niveles(_texto_un_decimal(self.diferencia))} "
            f"bajo el resto del jardín en {self.nucleo.nombre}"
        )

    @property
    def texto_celda(self):
        """Texto corto de la celda (la tabla ya dice la sala y el núcleo), o "" si no hay alerta."""
        if not self.alerta:
            return ""
        return f"Revisar: {_texto_niveles(_texto_un_decimal(self.diferencia))} bajo el resto"


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
    proporcion_minima: object = PROPORCION_MINIMA_VALIDADOS

    @property
    def texto_umbral(self):
        return _texto_niveles(_numero(redondear(self.umbral)))

    @property
    def texto_minimo(self):
        """El mínimo de niños con nivel validado, en palabras: "la mitad", "3 de cada 4"."""
        minimo = Fraction(self.proporcion_minima)
        if minimo == Fraction(1, 2):
            return "la mitad"
        return f"{minimo.numerator} de cada {minimo.denominator}"


def _suficiente(validados, ninos, proporcion_minima):
    """Si `validados` de `ninos` alcanza el mínimo. Exacto (Fraction): justo la mitad alcanza la mitad."""
    return validados > 0 and Fraction(validados, ninos) >= Fraction(proporcion_minima)


def comparar_salas(cursos, nucleos, niveles, umbral=UMBRAL_SALA_BAJO, proporcion_minima=PROPORCION_MINIMA_VALIDADOS):
    """Compara las salas del jardín por núcleo. Pura: no consulta la base.

    - cursos: objetos con `pk`, `nombre` y `nivel_educativo`, en el orden de
      las columnas.
    - nucleos: objetos con `pk` y `nombre`, en el orden de las filas.
    - niveles: {(id del curso, id del núcleo): [nivel actual validado de cada
      niño de la sala, o None si no tiene]}. Una entrada por niño: el largo de
      la lista es el total de niños de la sala para el mínimo.
    - proporcion_minima: fracción de los niños de la sala que debe tener nivel
      validado en el núcleo para que la sala entre en la comparación (por
      defecto la mitad; justo la mitad entra). Se compara de forma exacta.

    El promedio de cada sala se redondea a un decimal (`redondear`). El
    promedio de las demás es la media simple de esos promedios redondeados de
    las otras salas del mismo nivel educativo con datos suficientes en el
    núcleo, redondeada también a un decimal: cada sala pesa lo mismo, como en
    el ejemplo de Integra (dos salas en 6 y una en 3). La alerta se decide con
    la diferencia entre esos valores redondeados, así que coincide con lo que
    muestra la tabla.

    Una sala sin datos suficientes en un núcleo muestra "Sin datos
    suficientes", no tiene alerta y no entra en el promedio de las demás. Las
    alertas van de mayor a menor diferencia; si empatan, por núcleo y luego
    por sala. Nada supone una cantidad de niveles ni de núcleos.
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
            datos = {}  # {id del curso: (promedio redondeado o None, validados, niños)}
            for c in salas:
                lista = niveles.get((c.pk, nucleo.pk), [])
                validados = sum(1 for n in lista if n is not None)
                suficiente = _suficiente(validados, len(lista), proporcion_minima)
                datos[c.pk] = (redondear(promedio(lista)) if suficiente else None, validados, len(lista))
            celdas = []
            for curso in salas:
                propio, validados, total = datos[curso.pk]
                otros = [p for pk, (p, _, _) in datos.items() if pk != curso.pk and p is not None]
                demas = redondear(Fraction(sum(otros, Decimal(0))) / len(otros)) if otros else None
                celda = CeldaSala(curso, nucleo, propio, demas, umbral, validados, total)
                celdas.append(celda)
                if celda.alerta:
                    alertas.append((-celda.diferencia, orden_nucleo, posicion_curso[curso.pk], celda))
            filas.append(FilaNucleo(nucleo, celdas))
        grupos.append(GrupoSalas(nivel_educativo, nombres.get(nivel_educativo, nivel_educativo), salas, filas))
    alertas.sort(key=lambda a: a[:3])
    return ResumenJardin(
        grupos=grupos, alertas=[a[3] for a in alertas], umbral=umbral, proporcion_minima=proporcion_minima
    )


def resumen_del_jardin(jardin, umbral=UMBRAL_SALA_BAJO, proporcion_minima=PROPORCION_MINIMA_VALIDADOS):
    """ResumenJardin con las salas del jardín y todos los núcleos.

    El nivel actual de cada niño en un núcleo es su NivelValidado más reciente
    entre los que fijó una educadora (`validado_por` no vacío), con el mismo
    orden que la tabla del curso. El nivel inicial automático de `Nino.save()`
    no tiene `validado_por` y no cuenta: un niño sin niveles validados en un
    núcleo queda sin dato. El total de niños para el mínimo son todos los
    niños de la sala, los mismos que muestra la tabla del curso. Cada curso
    trae `cantidad_ninos`. Hace una cantidad fija de consultas.
    """
    cursos = list(jardin.cursos.annotate(cantidad_ninos=Count("ninos")))
    nucleos = list(Nucleo.objects.all())
    ninos = Nino.objects.filter(curso__jardin=jardin).values_list("pk", "curso_id")
    actuales = {}
    filas = (
        NivelValidado.objects.filter(nino__curso__jardin=jardin, validado_por__isnull=False)
        .order_by("nino_id", "nucleo_id", "-fecha", "-creado", "-id")
        .values_list("nino_id", "nucleo_id", "nivel")
    )
    for nino_id, nucleo_id, nivel in filas:
        actuales.setdefault((nino_id, nucleo_id), nivel)  # el primero es el validado más reciente
    niveles = {}
    for nino_id, curso_id in ninos:
        for nucleo in nucleos:
            niveles.setdefault((curso_id, nucleo.pk), []).append(actuales.get((nino_id, nucleo.pk)))
    return comparar_salas(cursos, nucleos, niveles, umbral=umbral, proporcion_minima=proporcion_minima)
