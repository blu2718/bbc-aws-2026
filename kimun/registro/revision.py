"""Revisión de observaciones pendientes (PLAN.md, Task 6).

Solo la educadora del curso revisa: las vistas obtienen las observaciones con
`pendientes_que_revisa(usuario)`, que ya filtra por `cursos_que_valida`.

Aceptar una observación no recalcula nada aparte: la tabla del curso, las
alertas y la cobertura se calculan cada vez que se piden (PLAN.md, "Flujo de
procesamiento", paso 7), así que la siguiente carga de la página ya la cuenta.
"""
from dataclasses import dataclass, field

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, F, Q
from django.utils import timezone

from .models import Captura, Efecto, Nino, Nucleo, ObjetivoAprendizaje, Observacion
from .permisos import cursos_que_valida
from .procesamiento import NOMBRE_TODO_EL_CURSO
from .propuestas import rubrica_completa, solicitar_propuesta

MENSAJE_SIN_NINO = "Elige a qué niño o niña corresponde antes de aceptarla."


def pendientes_que_revisa(usuario):
    """Observaciones pendientes de los cursos donde el usuario revisa."""
    return Observacion.objects.filter(
        captura__curso__in=cursos_que_valida(usuario), estado=Observacion.Estado.PENDIENTE
    )


def contar_pendientes(usuario):
    """Cantidad de observaciones pendientes que el usuario debe revisar (0 para asistentes y directoras)."""
    return pendientes_que_revisa(usuario).count()


def cursos_por_revisar(usuario):
    """Cursos donde el usuario revisa, cada uno con `pendientes`. Vacío para asistentes y directoras.

    Una sola consulta: se usa en la barra de navegación de todas las páginas.
    """
    pendiente = Q(capturas__observaciones__estado=Observacion.Estado.PENDIENTE)
    return list(
        cursos_que_valida(usuario)
        .annotate(pendientes=Count("capturas__observaciones", filter=pendiente))
        .order_by("nombre")
    )


def resumen_pendientes(curso):
    """{"individuales": n, "grupales": n} pendientes del curso."""
    return Observacion.objects.filter(captura__curso=curso, estado=Observacion.Estado.PENDIENTE).aggregate(
        individuales=Count("id", filter=Q(grupal=False)),
        grupales=Count("id", filter=Q(grupal=True)),
    )


def pendientes_del_curso(curso):
    return (
        Observacion.objects.filter(captura__curso=curso, estado=Observacion.Estado.PENDIENTE)
        .select_related("captura__autora", "nino")
        .prefetch_related("nucleos", "oas__nucleo")
        .order_by("captura__creada", "captura_id", "fecha", "id")
    )


@dataclass
class GrupoCaptura:
    """Las observaciones pendientes de una captura, separadas en individuales y grupales."""

    captura: Captura
    individuales: list = field(default_factory=list)
    grupales: list = field(default_factory=list)

    @property
    def total(self):
        return len(self.individuales) + len(self.grupales)

    @property
    def sin_nino(self):
        return sum(1 for o in self.individuales if o.nino_id is None)


@dataclass
class Revision:
    grupos: list  # [GrupoCaptura], de la captura más antigua a la más reciente

    @property
    def individuales(self):
        return sum(len(g.individuales) for g in self.grupos)

    @property
    def grupales(self):
        """[(captura, observación)] de las notas grupales, para la sección de contexto."""
        return [(g.captura, o) for g in self.grupos for o in g.grupales]

    @property
    def total(self):
        return sum(g.total for g in self.grupos)

    @property
    def grupos_con_individuales(self):
        return [g for g in self.grupos if g.individuales]


def revision_del_curso(curso):
    grupos = {}
    for obs in pendientes_del_curso(curso):
        grupo = grupos.setdefault(obs.captura_id, GrupoCaptura(obs.captura))
        (grupo.grupales if obs.grupal else grupo.individuales).append(obs)
    return Revision(list(grupos.values()))


# --- Acciones ---------------------------------------------------------------------------


def puede_aceptarse(obs):
    return obs.grupal or obs.nino_id is not None


def _aceptar(obs):
    if not puede_aceptarse(obs):
        raise ValidationError(MENSAJE_SIN_NINO)
    if obs.nino_id and obs.nino.curso_id != obs.captura.curso_id:
        raise ValidationError("El niño debe pertenecer al curso de la captura.")
    modificada = Observacion.objects.filter(pk=obs.pk, estado=Observacion.Estado.PENDIENTE,
                                            nino_id=obs.nino_id, grupal=obs.grupal).update(
        estado=Observacion.Estado.ACEPTADA, actualizada=timezone.now(),
    )
    obs.refresh_from_db()
    return bool(modificada)


def _destinos(obs):
    """(niño, núcleo) donde pedir una propuesta. Sin rúbrica completa, la propuesta fallaría siempre."""
    if obs.grupal or obs.nino_id is None:
        return []
    nivel_educativo = obs.nino.curso.nivel_educativo
    ids = set(obs.nucleos.values_list("pk", flat=True)) | set(obs.oas.filter(
        nivel_educativo=nivel_educativo,
    ).values_list("nucleo_id", flat=True))
    return [
        (obs.nino, nucleo) for nucleo in Nucleo.objects.filter(pk__in=ids).order_by("pk")
        if rubrica_completa(nivel_educativo, nucleo)
    ]


@transaction.atomic
def aceptar(obs):
    """Acepta y solicita propuestas en la misma transacción; repetir no duplica trabajos."""
    Observacion.objects.filter(pk=obs.pk).update(actualizada=F("actualizada"))
    if _aceptar(obs):
        for nino, nucleo in _destinos(obs):
            solicitar_propuesta(nino, nucleo, reintentar=True)


def descartar(obs):
    obs.estado = Observacion.Estado.DESCARTADA
    obs.save(update_fields=["estado", "actualizada"])


@transaction.atomic
def aceptar_todas(captura, solo_del_curso=False):
    """Acepta las pendientes de la captura que se pueden aceptar. Devuelve (aceptadas, sin niño).

    Con `solo_del_curso`, solo las de algo que hizo todo el curso (una por niño): las
    individuales y las notas de contexto de la misma captura se siguen revisando una a una.
    """
    Captura.objects.filter(pk=captura.pk).update(actualizada=F("actualizada"))
    pendientes = captura.observaciones.filter(estado=Observacion.Estado.PENDIENTE)
    if solo_del_curso:
        pendientes = pendientes.filter(nombre_detectado=NOMBRE_TODO_EL_CURSO, grupal=False)
    pendientes = list(pendientes)
    listas = [o for o in pendientes if puede_aceptarse(o)]
    destinos, aceptadas = {}, 0
    for obs in listas:
        if _aceptar(obs):
            aceptadas += 1
            for nino, nucleo in _destinos(obs):
                destinos[(nino.pk, nucleo.pk)] = (nino, nucleo)
    for nino, nucleo in destinos.values():
        solicitar_propuesta(nino, nucleo, reintentar=True)
    return aceptadas, len(pendientes) - len(listas)


# --- Formularios ------------------------------------------------------------------------


class AsignarNinoForm(forms.Form):
    """Valida el niño elegido en la tarjeta. Solo se aceptan niños del curso de la observación."""

    nino = forms.ModelChoiceField(queryset=Nino.objects.none(), label="Niño o niña")

    def __init__(self, *args, curso, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nino"].queryset = curso.ninos.all()


class ObservacionForm(forms.ModelForm):
    """Edición de una observación pendiente. Las opciones salen del curso y de su nivel educativo."""

    class Meta:
        model = Observacion
        fields = ["grupal", "nino", "fecha", "cita", "interpretacion", "nucleos", "oas", "apoyo", "efecto"]
        labels = {
            "grupal": "Nota sobre el grupo completo (contexto, no se usa para evaluar)",
            "nino": "Niño o niña",
            "cita": "Lo que hizo o dijo",
            "interpretacion": "Interpretación de quien registró",
            "nucleos": "Núcleos",
            "oas": "Objetivos de aprendizaje",
            "apoyo": "Nivel de apoyo",
            "efecto": "Efecto en sus OA",
        }
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "cita": forms.Textarea(attrs={"rows": 3}),
            "interpretacion": forms.Textarea(attrs={"rows": 2}),
            "nucleos": forms.CheckboxSelectMultiple,
            "oas": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, curso, **kwargs):
        super().__init__(*args, **kwargs)
        self.curso = curso
        self.fields["nino"].queryset = curso.ninos.all()
        self.fields["nino"].required = False
        self.fields["nino"].empty_label = "Sin asignar"
        self.fields["nucleos"].queryset = Nucleo.objects.all()
        self.fields["oas"].queryset = ObjetivoAprendizaje.objects.filter(
            nivel_educativo=curso.nivel_educativo
        ).select_related("nucleo")
        # Si el formulario no lo trae, se conserva el que propuso Claude.
        self.fields["efecto"].required = False

    def clean_efecto(self):
        return self.cleaned_data.get("efecto") or self.instance.efecto or Efecto.SIN_DATO

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha > timezone.localdate():
            raise ValidationError("La fecha no puede ser posterior a hoy.")
        return fecha

    def clean(self):
        datos = super().clean()
        if datos.get("grupal"):
            # Una nota grupal es contexto del curso: no queda ligada a un niño.
            datos["nino"] = None
        return datos

    def oas_por_nucleo(self):
        """[(núcleo, [(oa, marcado)], hay_marcados)] para mostrar los OA agrupados y plegables."""
        marcados = {str(v) for v in (self["oas"].value() or [])}
        grupos = {}
        for oa in self.fields["oas"].queryset:
            grupos.setdefault(oa.nucleo, []).append((oa, str(oa.pk) in marcados))
        return [(nucleo, opciones, any(m for _, m in opciones)) for nucleo, opciones in grupos.items()]
