"""Datos de las pantallas del boceto de interfaz (`diseno-interfaz.jpg`).

- Pantalla II (el suceso): `tarjetas_suceso`, una tarjeta por observación con
  la edad del niño, los núcleos y OA identificados, su nivel actual, el efecto
  y una sugerencia de qué observar después (de la rúbrica, no generada con IA).
- Pantalla III (menú lateral): `para_tener_presentes`, los niños con más
  señales de revisión de la tabla del curso (`alertas.tabla_del_curso`).
- Pantalla IV (perfil): `historial_del_nino`, sus sucesos aceptados y los
  niveles que validó la educadora, del más reciente al más antiguo.

Las plantillas solo muestran. Cada función hace una cantidad fija de consultas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .alertas import Gravedad
from .coincidencia import claves, normalizar
from .forms import etiqueta_nivel
from .models import DescriptorNivel, NivelValidado, Nucleo, Observacion, Rubrica, texto_nivel

SIN_NIVEL = "Sin nivel validado"
LIMITE_PRESENTES = 5


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


@dataclass(frozen=True)
class TarjetaSuceso:
    obs: Observacion
    edad: str
    nucleos: list = field(default_factory=list)  # [NucleoSuceso], en el orden de Nucleo
    oas: list = field(default_factory=list)

    @property
    def sugerencia(self):
        """El primer núcleo con un nivel siguiente en la rúbrica, o None."""
        return next((n for n in self.nucleos if n.siguiente is not None), None)


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

    tarjetas = []
    for obs in observaciones:
        nucleos = []
        for nucleo in _nucleos_de(obs, orden):
            nivel = niveles.get((obs.nino_id, nucleo.pk)) if obs.nino_id else None
            if nivel is None:
                nucleos.append(NucleoSuceso(nucleo, SIN_NIVEL if obs.nino_id else "", None))
                continue
            siguiente = descriptores.get((nucleo.pk, nivel + 1)) if nivel < maximo else None
            nucleos.append(NucleoSuceso(nucleo, etiqueta_nivel(nivel, descriptores.get((nucleo.pk, nivel))), siguiente))
        edad = texto_edad(obs.nino.fecha_nacimiento, hoy) if obs.nino else ""
        tarjetas.append(TarjetaSuceso(obs=obs, edad=edad, nucleos=nucleos, oas=list(obs.oas.all())))
    return tarjetas


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


# --- Pantalla III: el menú lateral -----------------------------------------------------------


@dataclass(frozen=True)
class NinoPresente:
    nino: object
    revisar: list   # núcleos con alerta ("Revisar")
    observar: list  # núcleos con aviso ("Observar")


def para_tener_presentes(tabla, limite=LIMITE_PRESENTES):
    """Los niños con más señales de revisión en la tabla del curso: primero alertas, luego avisos."""
    filas = sorted(
        (f for f in tabla.filas if f.alertas or f.avisos),
        key=lambda f: (-f.alertas, -f.avisos, f.nino.nombre),
    )
    return [
        NinoPresente(
            nino=f.nino,
            revisar=[c.nucleo for c in f.celdas if c.gravedad == Gravedad.ALERTA],
            observar=[c.nucleo for c in f.celdas if c.gravedad == Gravedad.AVISO],
        )
        for f in filas[:limite]
    ]


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
