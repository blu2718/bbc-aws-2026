"""Datos de las pantallas del boceto de interfaz (`diseno-interfaz.jpg`).

- Pantalla II (el suceso): `tarjetas_suceso`, una tarjeta por observación con
  la edad del niño, los núcleos y OA identificados, su nivel actual, el efecto
  y una sugerencia de qué observar después (de la rúbrica, no generada con IA).
- Pantalla III (menú lateral): `para_tener_presentes`, los niños con más
  señales de revisión de la tabla del curso (`alertas.tabla_del_curso`), con
  pocas observaciones o con muchas pendientes (`frecuencia.py`).
- Pantalla IV (perfil): `historial_del_nino`, sus sucesos aceptados y los
  niveles que validó la educadora, del más reciente al más antiguo.

Las plantillas solo muestran. Cada función hace una cantidad fija de consultas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .alertas import Gravedad
from .avanzar import anio_del_nivel, conductas_de_oas, manifestaciones_por_oa
from .coincidencia import claves, normalizar
from .forms import etiqueta_nivel
from .models import DescriptorNivel, NivelValidado, Nucleo, Observacion, Rubrica, texto_nivel

SIN_NIVEL = "Sin nivel validado"
LIMITE_PRESENTES = 8  # alcanza para las señales por núcleo y las de frecuencia de un curso típico


def texto_edad(fecha_nacimiento, hoy):
    """'5 años y 3 meses', '6 años' o '11 meses'. "" si falta la fecha o es posterior a hoy."""
    if not fecha_nacimiento or fecha_nacimiento > hoy:
        return ""
    meses = (hoy.year - fecha_nacimiento.year) * 12 + hoy.month - fecha_nacimiento.month
    if hoy.day < fecha_nacimiento.day:
        meses -= 1
    anios, meses = divmod(meses, 12)
    partes = []
    if anios:
        partes.append(f"{anios} año{'s' if anios != 1 else ''}")
    if meses or not anios:
        partes.append(f"{meses} mes{'es' if meses != 1 else ''}")
    return " y ".join(partes)


# --- Pantalla II: el suceso ------------------------------------------------------------


@dataclass(frozen=True)
class NucleoSuceso:
    nucleo: Nucleo
    texto_nivel: str                       # nivel actual validado: "3 · Desarrollando"
    siguiente: DescriptorNivel | None      # qué observar después, de la rúbrica
    texto_siguiente: str = ""              # "4 · Afianzando", o "4" si es provisorio
    conductas: list = field(default_factory=list)  # [avanzar.ConductasOA] del año del nivel siguiente
    anio: str = ""                         # "NT1" o "NT2" si hay conductas


@dataclass(frozen=True)
class TarjetaSuceso:
    obs: Observacion
    edad: str
    nucleos: list = field(default_factory=list)  # [NucleoSuceso], en el orden de Nucleo
    oas: list = field(default_factory=list)

    @property
    def sugerencia(self):
        """El primer núcleo con un nivel siguiente en la rúbrica, o None.

        Se prefiere uno con conductas del Programa para los OA del suceso, que es más concreto.
        """
        con_siguiente = [n for n in self.nucleos if n.siguiente is not None]
        return next((n for n in con_siguiente if n.conductas), None) or next(iter(con_siguiente), None)


def _nucleos_de(obs, orden):
    """Núcleos etiquetados y los de sus OA, sin repetir y en el orden de Nucleo."""
    vistos = {n.pk: n for n in obs.nucleos.all()}
    for oa in obs.oas.all():
        vistos.setdefault(oa.nucleo_id, oa.nucleo)
    return sorted(vistos.values(), key=lambda n: orden.get(n.pk, 0))


def tarjetas_suceso(observaciones, hoy):
    """[TarjetaSuceso] de observaciones de un mismo curso (por ejemplo, las de una captura)."""
    observaciones = list(observaciones)
    if not observaciones:
        return []
    nivel_educativo = observaciones[0].captura.curso.nivel_educativo
    maximo = Rubrica.nivel_maximo(nivel_educativo)
    descriptores = {
        (d.nucleo_id, d.nivel): d for d in DescriptorNivel.objects.filter(nivel_educativo=nivel_educativo)
    }
    niveles = {}
    filas = (
        NivelValidado.objects.filter(nino_id__in={o.nino_id for o in observaciones if o.nino_id})
        .order_by("nino_id", "nucleo_id", "-fecha", "-creado", "-id")
        .values_list("nino_id", "nucleo_id", "nivel")
    )
    for nino_id, nucleo_id, nivel in filas:
        niveles.setdefault((nino_id, nucleo_id), nivel)  # el primero es el más reciente
    orden = {pk: i for i, pk in enumerate(Nucleo.objects.values_list("pk", flat=True))}
    provisorios = {d.nucleo_id for d in descriptores.values() if d.provisorio}
    manifestaciones = manifestaciones_por_oa(oa_ids={oa.pk for o in observaciones for oa in o.oas.all()})

    tarjetas = []
    for obs in observaciones:
        nucleos = []
        for nucleo in _nucleos_de(obs, orden):
            nivel = niveles.get((obs.nino_id, nucleo.pk)) if obs.nino_id else None
            if nivel is None:
                nucleos.append(NucleoSuceso(nucleo, SIN_NIVEL if obs.nino_id else "", None))
                continue
            siguiente = descriptores.get((nucleo.pk, nivel + 1)) if nivel < maximo else None
            # En la rúbrica provisoria, el nivel siguiente se describe con las conductas del Programa
            # de los OA de este suceso, del año que le corresponde (avanzar.py).
            anio = anio_del_nivel(siguiente.nivel) if siguiente and nucleo.pk in provisorios else ""
            conductas = conductas_de_oas([oa for oa in obs.oas.all() if oa.nucleo_id == nucleo.pk], manifestaciones, anio)
            nucleos.append(NucleoSuceso(
                nucleo, etiqueta_nivel(nivel, descriptores.get((nucleo.pk, nivel))), siguiente,
                texto_siguiente=etiqueta_nivel(siguiente.nivel, siguiente) if siguiente else "",
                conductas=conductas, anio=anio if conductas else "",
            ))
        edad = texto_edad(obs.nino.fecha_nacimiento, hoy) if obs.nino else ""
        tarjetas.append(TarjetaSuceso(obs=obs, edad=edad, nucleos=nucleos, oas=list(obs.oas.all())))
    return tarjetas


@dataclass(frozen=True)
class LineaResumen:
    """Una línea del resumen de la nota: a quién corresponde una observación y en qué núcleos."""

    obs: Observacion
    nucleos: list  # [Nucleo]


@dataclass(frozen=True)
class ResumenCaptura:
    """"De esta nota saqué N observaciones, para estos niños, en estos núcleos".

    No muestra el estado de cada observación (pendiente o aceptada) porque las
    tarjetas se actualizan solas con HTMX y el resumen quedaría desfasado.
    """

    lineas: list            # [LineaResumen], una por niño (asignado o no), en el orden de las tarjetas
    del_curso: int          # niños que reciben lo que hizo todo el curso
    nucleos_del_curso: list  # núcleos de lo que hizo todo el curso
    grupales: int           # notas de contexto del curso
    nucleos: list           # todos los núcleos distintos, en el orden de Nucleo

    @property
    def observaciones(self):
        return len(self.lineas) + self.del_curso

    @property
    def vacio(self):
        return not (self.lineas or self.del_curso or self.grupales)


def resumen_captura(tarjetas, del_curso, grupales):
    """`ResumenCaptura` a partir de las tarjetas que ya arma la pantalla II. Pura."""
    lineas = [LineaResumen(t.obs, [n.nucleo for n in t.nucleos]) for t in tarjetas]
    nucleos_del_curso = [n.nucleo for n in del_curso[0].nucleos] if del_curso else []
    vistos = {}
    for nucleo in [n for linea in lineas for n in linea.nucleos] + nucleos_del_curso:
        vistos.setdefault(nucleo.pk, nucleo)
    return ResumenCaptura(
        lineas=lineas, del_curso=len(del_curso), nucleos_del_curso=nucleos_del_curso, grupales=len(grupales),
        nucleos=sorted(vistos.values(), key=lambda n: (n.orden, n.sigla)),
    )


def observaciones_para_tarjetas(queryset):
    """Las relaciones que usan las tarjetas, para no consultar por cada una."""
    return queryset.select_related("captura__curso", "captura__autora", "nino").prefetch_related(
        "nucleos", "oas__nucleo"
    )


@dataclass(frozen=True)
class PerfilBreve:
    """Resumen del perfil de un niño nombrado en la nota, para mostrarlo aunque la IA no haya respondido."""

    nino: object
    edad: str


def ninos_mencionados(texto, ninos, hoy):
    """[PerfilBreve] de los niños del curso cuyo nombre, nombre de pila o alias aparece tal cual en el texto.

    Solo coincidencias exactas (sin tildes ni mayúsculas), para no mostrar a un niño
    que no se nombró. No reemplaza a la separación con Claude: es lo que se puede
    mostrar mientras tanto, o si Bedrock no responde.
    """
    sin_puntuacion = re.sub(r"[^\w]+", " ", texto or "")
    palabras = f" {normalizar(sin_puntuacion)} "
    encontrados = []
    for nino in ninos:
        if any(f" {clave} " in palabras for clave in claves(nino)):
            encontrados.append(PerfilBreve(nino=nino, edad=texto_edad(nino.fecha_nacimiento, hoy)))
    return encontrados


# --- Propuestas de nivel por decidir (vista del curso) -----------------------------------------


@dataclass(frozen=True)
class PropuestaPorDecidir:
    propuesta: object       # PropuestaNivel en estado "lista"
    texto_actual: str       # nivel validado actual: "3 · Desarrollando"
    texto_propuesto: str    # "" si la evidencia no alcanzó para proponer


@dataclass(frozen=True)
class BandejaPropuestas:
    por_decidir: list       # [PropuestaPorDecidir], de la más antigua a la más reciente
    en_preparacion: int     # solicitadas o procesando: las está generando el proceso de fondo


def propuestas_por_decidir(curso, tabla=None):
    """Las propuestas listas del curso, para que la educadora no tenga que abrir cada ficha.

    Solo hay una lista por niño y núcleo (pedir otra deja la anterior obsoleta).
    No se comprueba aquí si siguen vigentes: la ficha lo hace al decidir. Usa la
    `tabla` del curso, si se pasa, para el nivel actual; si no, lo consulta.
    """
    from .models import PropuestaNivel

    propuestas = list(
        PropuestaNivel.objects.filter(nino__curso=curso, estado=PropuestaNivel.Estado.LISTA)
        .select_related("nino", "nucleo").order_by("creada", "pk")
    )
    en_preparacion = PropuestaNivel.objects.filter(
        nino__curso=curso, estado__in=[PropuestaNivel.Estado.SOLICITADA, PropuestaNivel.Estado.PROCESANDO],
    ).count()
    if not propuestas:
        return BandejaPropuestas([], en_preparacion)
    nombres = DescriptorNivel.nombres_por_nucleo(curso.nivel_educativo)
    if tabla is not None:
        actuales = {(f.nino.pk, c.nucleo.pk): c.texto_nivel for f in tabla.filas for c in f.celdas}
    else:
        actuales = {}
        filas = (
            NivelValidado.objects.filter(nino__curso=curso)
            .order_by("nino_id", "nucleo_id", "-fecha", "-creado", "-id")
            .values_list("nino_id", "nucleo_id", "nivel", "nucleo__sigla")
        )
        for nino_id, nucleo_id, nivel, sigla in filas:
            actuales.setdefault((nino_id, nucleo_id), texto_nivel(nivel, nombres.get(sigla, {}).get(nivel, "")))
    por_decidir = []
    for p in propuestas:
        propuesto = ""
        if p.nivel is not None:
            nombre = "" if p.rubrica_provisoria else nombres.get(p.nucleo.sigla, {}).get(p.nivel, "")
            propuesto = texto_nivel(p.nivel, nombre)
        por_decidir.append(PropuestaPorDecidir(p, actuales.get((p.nino_id, p.nucleo_id), SIN_NIVEL), propuesto))
    return BandejaPropuestas(por_decidir, en_preparacion)


# --- Pantalla III: el menú lateral -----------------------------------------------------------


@dataclass(frozen=True)
class NinoPresente:
    nino: object
    revisar: list   # núcleos con alerta ("Revisar")
    observar: list  # núcleos con aviso ("Observar")
    frecuencia: object = None  # frecuencia.FrecuenciaNino, si tiene pocas observaciones o muchas pendientes
    ver_pendientes: bool = False

    @property
    def pocas_observaciones(self):
        return self.frecuencia is not None and self.frecuencia.gravedad != Gravedad.NORMAL

    @property
    def muchas_pendientes(self):
        return self.ver_pendientes and self.frecuencia is not None and self.frecuencia.pendientes_gravedad != Gravedad.NORMAL

    @property
    def alertas(self):
        return len(self.revisar) + (self.pocas_observaciones and self.frecuencia.gravedad == Gravedad.ALERTA)

    @property
    def avisos(self):
        aviso = self.pocas_observaciones and self.frecuencia.gravedad == Gravedad.AVISO
        return len(self.observar) + aviso + self.muchas_pendientes


def para_tener_presentes(tabla, frecuencia=None, ver_pendientes=False, limite=LIMITE_PRESENTES):
    """Los niños con más señales en el curso: primero alertas, luego avisos.

    Cuentan las señales de cada núcleo de la tabla del curso, las pocas
    observaciones de `frecuencia` (`frecuencia.frecuencia_del_curso`) y, si
    `ver_pendientes` (quien revisa), las muchas observaciones pendientes.
    """
    por_nino = {fr.nino.pk: fr for fr in frecuencia.filas} if frecuencia else {}
    presentes = []
    for f in tabla.filas:
        p = NinoPresente(
            nino=f.nino,
            revisar=[c.nucleo for c in f.celdas if c.gravedad == Gravedad.ALERTA],
            observar=[c.nucleo for c in f.celdas if c.gravedad == Gravedad.AVISO],
            frecuencia=por_nino.get(f.nino.pk),
            ver_pendientes=ver_pendientes,
        )
        if p.alertas or p.avisos:
            presentes.append(p)
    presentes.sort(key=lambda p: (-p.alertas, -p.avisos, p.nino.nombre))
    return presentes[:limite]


# --- Pantalla IV: el perfil ------------------------------------------------------------------


@dataclass(frozen=True)
class Evento:
    """Una entrada del historial: un suceso aceptado o una revisión de niveles."""

    fecha: date
    tipo: str                      # "suceso" o "niveles"
    texto: str = ""                # la cita del suceso
    detalle: str = ""              # interpretación del suceso o comentario de la revisión
    nucleos: list = field(default_factory=list)
    efecto: str = ""
    efecto_texto: str = ""
    captura_id: int | None = None
    niveles: list = field(default_factory=list)  # [(Nucleo, "3 · Desarrollando")]
    autora: str = ""


def _nombre(usuario):
    return (usuario.get_full_name() or usuario.username) if usuario else ""


def historial_del_nino(nino):
    """[Evento] del niño, del más reciente al más antiguo.

    Los sucesos son sus observaciones aceptadas (no las grupales). Los niveles
    son los que fijó la educadora, agrupados por fecha y comentario; el nivel 1
    automático del ingreso no se muestra.
    """
    nombres = DescriptorNivel.nombres_por_nucleo(nino.curso.nivel_educativo)
    orden = {pk: i for i, pk in enumerate(Nucleo.objects.values_list("pk", flat=True))}
    eventos = []
    observaciones = (
        Observacion.objects.filter(nino=nino, estado=Observacion.Estado.ACEPTADA, grupal=False)
        .prefetch_related("nucleos", "oas__nucleo")
        .order_by("-fecha", "-creada", "-id")
    )
    for obs in observaciones:
        eventos.append(Evento(
            fecha=obs.fecha, tipo="suceso", texto=obs.cita, detalle=obs.interpretacion,
            nucleos=_nucleos_de(obs, orden), efecto=obs.efecto, efecto_texto=obs.get_efecto_display(),
            captura_id=obs.captura_id,
        ))

    revisiones = {}
    validaciones = (
        NivelValidado.objects.filter(nino=nino, validado_por__isnull=False)
        .select_related("nucleo", "validado_por")
        .order_by("-fecha", "nucleo__orden", "nucleo__sigla", "-creado", "-id")
    )
    for nv in validaciones:
        clave = (nv.fecha, nv.comentario, nv.validado_por_id)
        revision = revisiones.setdefault(clave, {"niveles": {}, "autora": _nombre(nv.validado_por)})
        # Si se fijó dos veces el mismo día con el mismo comentario, vale la última.
        revision["niveles"].setdefault(nv.nucleo.pk, (nv.nucleo, texto_nivel(nv.nivel, nombres.get(nv.nucleo.sigla, {}).get(nv.nivel, ""))))
    for (fecha, comentario, _), revision in revisiones.items():
        niveles = sorted(revision["niveles"].values(), key=lambda par: orden.get(par[0].pk, 0))
        eventos.append(Evento(fecha=fecha, tipo="niveles", detalle=comentario, niveles=niveles, autora=revision["autora"]))

    # Estable: el mismo día, los sucesos quedan antes que las revisiones.
    return sorted(eventos, key=lambda e: e.fecha, reverse=True)
