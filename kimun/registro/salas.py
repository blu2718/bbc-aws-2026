"""Salas del jardín: el panel con que la directora monitorea cada sala y los formularios para mantenerlas.

Un jardín tiene varias salas (cursos) de uno o más niveles educativos. La directora las ve
todas; la educadora y las asistentes, solo las suyas (`permisos.cursos_de`).

- `panel_del_jardin`: por sala, su equipo y lo que necesita atención: observaciones por
  revisar, propuestas de nivel por decidir, avisos de protección pendientes, niños con
  señales «Revisar» o con pocas observaciones, y núcleos sin observaciones en la quincena.
  Son sugerencias de revisión, igual que en la tabla del curso; no comparan a los niños.
  La comparación de niveles entre salas sigue en `alertas.resumen_del_jardin`.
- `SalaForm`: la directora crea una sala o cambia su nombre, nivel educativo y equipo.
- `NinoForm`: la directora o la educadora de la sala agregan un niño o editan sus datos.

El equipo se elige entre quienes ya trabajan en el jardín y las cuentas sin asignar: así
la directora no ve el personal de otros jardines. Las cuentas se crean en el panel de
administración.
"""
from dataclasses import dataclass, field

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .alertas import tabla_del_curso
from .cobertura import cobertura_quincena_del_curso, quincena_de
from .forms import METAS_POR_DEFECTO
from .frecuencia import frecuencia_del_curso
from .models import AvisoProteccion, Captura, Curso, MetaSemestre, NivelEducativo, Nino, PropuestaNivel, Rubrica
from .revision import resumen_pendientes

MAX_ALIAS = 10
LARGO_ALIAS = 40


def nombre_de(usuario):
    return (usuario.get_full_name() or usuario.username) if usuario else ""


# --- Panel del jardín ---------------------------------------------------------------


@dataclass(frozen=True)
class EstadoSala:
    curso: Curso
    asistentes: list            # nombres
    ninos: int
    por_revisar: int            # observaciones individuales pendientes de revisión
    propuestas: int             # propuestas de nivel listas para decidir
    avisos: int                 # avisos de protección pendientes
    con_revisar: list           # niños con al menos una señal «Revisar» en la tabla del curso
    pocas_observaciones: list   # niños con pocas o muy pocas observaciones (frecuencia.py)
    nucleos_sin_observaciones: list
    observaciones_14_dias: int  # aceptadas y por revisar, sin grupales ni de todo el curso
    ultimo_registro: object     # fecha y hora de la última captura, o None

    @property
    def educadora(self):
        return nombre_de(self.curso.educadora)

    @property
    def atencion(self):
        """Lo que la sala tiene pendiente, para mostrar arriba de su tarjeta: [(estado, texto)].
        El estado elige el color del chip (docs/diseno.md): los avisos de protección en rojo, lo
        pendiente de decidir en amarillo."""
        pendientes = []
        if self.avisos:
            pendientes.append(("error", f"{self.avisos} aviso{'s' if self.avisos != 1 else ''} de protección por atender"))
        if self.por_revisar:
            pendientes.append(("pendiente", f"{self.por_revisar} observaci{'ones' if self.por_revisar != 1 else 'ón'} por revisar"))
        if self.propuestas:
            pendientes.append(("pendiente", f"{self.propuestas} propuesta{'s' if self.propuestas != 1 else ''} de nivel por decidir"))
        return pendientes


@dataclass(frozen=True)
class PanelJardin:
    salas: list                     # [EstadoSala], en el orden de los niveles educativos y luego por nombre
    sin_salas: bool = field(default=False)

    @property
    def total_ninos(self):
        return sum(s.ninos for s in self.salas)


def _orden_nivel(curso):
    orden = [valor for valor, _ in NivelEducativo.choices]
    return (orden.index(curso.nivel_educativo) if curso.nivel_educativo in orden else len(orden), curso.nombre)


def estado_de_sala(curso, hoy):
    tabla = tabla_del_curso(curso, hoy=hoy)
    ninos = [fila.nino for fila in tabla.filas]
    frecuencia = frecuencia_del_curso(curso, hoy=hoy, ninos=ninos)
    cobertura = cobertura_quincena_del_curso(curso, quincena_de(hoy), nucleos=tabla.nucleos)
    ultima = Captura.objects.filter(curso=curso).order_by("-creada").values_list("creada", flat=True).first()
    return EstadoSala(
        curso=curso,
        asistentes=[nombre_de(a) for a in curso.asistentes.all()],
        ninos=len(ninos),
        por_revisar=resumen_pendientes(curso)["individuales"],
        propuestas=PropuestaNivel.objects.filter(nino__curso=curso, estado=PropuestaNivel.Estado.LISTA).count(),
        avisos=AvisoProteccion.objects.filter(
            captura__curso=curso, estado=AvisoProteccion.Estado.PENDIENTE,
        ).count(),
        con_revisar=[f.nino for f in tabla.filas if f.alertas],
        pocas_observaciones=[f.nino for f in frecuencia.con_senal],
        nucleos_sin_observaciones=[c.nucleo for c in cobertura if c.sin_observaciones] if ninos else [],
        observaciones_14_dias=sum(f.dos_semanas for f in frecuencia.filas),
        ultimo_registro=ultima,
    )


def panel_del_jardin(jardin, hoy=None):
    """PanelJardin con el estado de cada sala. Unas 15 consultas por sala, sin importar cuántos niños tenga."""
    hoy = hoy or timezone.localdate()
    cursos = sorted(
        jardin.cursos.select_related("educadora", "jardin").prefetch_related("asistentes"), key=_orden_nivel,
    )
    return PanelJardin([estado_de_sala(c, hoy) for c in cursos], sin_salas=not cursos)


# --- Formularios --------------------------------------------------------------------


def equipo_disponible(jardin):
    """Cuentas que se pueden asignar a una sala del jardín: su equipo actual, su directora y las
    cuentas activas sin sala ni jardín. No incluye al personal de otros jardines ni a los superusuarios."""
    Usuario = get_user_model()
    del_jardin = Q(cursos__jardin=jardin) | Q(cursos_asistidos__jardin=jardin) | Q(jardines_dirigidos=jardin)
    sin_asignar = Q(cursos__isnull=True, cursos_asistidos__isnull=True, jardines_dirigidos__isnull=True)
    ids = Usuario.objects.filter(is_active=True, is_superuser=False).filter(del_jardin | sin_asignar).values("pk")
    return Usuario.objects.filter(pk__in=ids).order_by("first_name", "last_name", "username")


def _etiqueta_persona(usuario):
    """Nombre y usuario: dos personas pueden llamarse igual (en la demo hay dos «Daniela Demo»)."""
    completo = usuario.get_full_name()
    return f"{completo} ({usuario.username})" if completo else usuario.username


class _Persona(forms.ModelChoiceField):
    def label_from_instance(self, usuario):
        return _etiqueta_persona(usuario)


class _Personas(forms.ModelMultipleChoiceField):
    def label_from_instance(self, usuario):
        return _etiqueta_persona(usuario)


class SalaForm(forms.ModelForm):
    """Nombre, nivel educativo y equipo de una sala. El nivel educativo no cambia si la sala ya tiene
    niños: sus niveles y observaciones son de la rúbrica de ese nivel."""

    class Meta:
        model = Curso
        fields = ["nombre", "nivel_educativo", "educadora", "asistentes"]
        labels = {"nombre": "Nombre de la sala", "nivel_educativo": "Nivel educativo"}
        help_texts = {"nombre": "Por ejemplo «Transición Mayor B» o «Medio Menor A»."}
        field_classes = {"educadora": _Persona, "asistentes": _Personas}
        widgets = {"asistentes": forms.CheckboxSelectMultiple}

    def __init__(self, *args, jardin, **kwargs):
        super().__init__(*args, **kwargs)
        self.jardin = jardin
        equipo = equipo_disponible(jardin)
        self.fields["educadora"].queryset = equipo
        self.fields["educadora"].label = "Educadora de la sala"
        self.fields["educadora"].help_text = "Revisa las observaciones y fija los niveles."
        self.fields["educadora"].empty_label = "Elige a la educadora"
        self.fields["asistentes"].queryset = equipo
        self.fields["asistentes"].required = False
        self.fields["asistentes"].label = "Asistentes de párvulo"
        self.fields["asistentes"].help_text = "Registran observaciones; no las revisan ni fijan niveles."
        self.tiene_ninos = bool(self.instance.pk) and self.instance.ninos.exists()
        if self.tiene_ninos:
            self.fields["nivel_educativo"].disabled = True
            self.fields["nivel_educativo"].help_text = (
                "No se puede cambiar: la sala ya tiene niños y niñas con niveles de esta rúbrica."
            )

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        repetida = Curso.objects.filter(jardin=self.jardin, nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetida.exists():
            raise forms.ValidationError("Ya hay una sala con ese nombre en el jardín.")
        return nombre

    def clean(self):
        datos = super().clean()
        educadora, asistentes = datos.get("educadora"), datos.get("asistentes") or []
        if educadora is not None and educadora in asistentes:
            self.add_error("asistentes", f"{nombre_de(educadora)} ya es la educadora de la sala.")
        return datos

    @transaction.atomic
    def save(self, commit=True):
        nueva = self.instance.pk is None
        self.instance.jardin = self.jardin
        curso = super().save(commit=commit)
        if nueva:
            # La tabla de metas parte con los valores por defecto, sin pasar el máximo de la rúbrica.
            maximo = Rubrica.nivel_maximo(curso.nivel_educativo)
            MetaSemestre.objects.bulk_create(
                MetaSemestre(curso=curso, semestre_permanencia=s, nivel_esperado=min(n, maximo))
                for s, n in METAS_POR_DEFECTO.items()
            )
        return curso


class NinoForm(forms.ModelForm):
    """Nombre, apodos y fechas de un niño. Al crearlo parte en nivel 1 en todos los núcleos (Nino.save)."""

    alias = forms.CharField(
        required=False, label="Apodos o variantes de escritura (opcional)",
        help_text="Separados por coma, por ejemplo «Nayara, Naia». Kimün los usa para reconocerlo en las notas "
                  "y para ocultar su nombre en el informe de otros niños.",
    )

    class Meta:
        model = Nino
        fields = ["nombre", "alias", "fecha_ingreso", "fecha_nacimiento"]
        labels = {
            "nombre": "Nombre y apellido",
            "fecha_ingreso": "Fecha de ingreso a la sala",
            "fecha_nacimiento": "Fecha de nacimiento (opcional)",
        }
        help_texts = {
            "nombre": "Si hay otro niño o niña con el mismo nombre de pila, el apellido ayuda a distinguirlos.",
            "fecha_nacimiento": "Solo para mostrar la edad. No se envía a Bedrock.",
        }
        widgets = {
            "fecha_ingreso": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, curso, **kwargs):
        super().__init__(*args, **kwargs)
        self.curso = curso
        if self.instance.pk:
            self.initial["alias"] = ", ".join(self.instance.alias or [])
            # Cambiarla movería el nivel inicial y el semestre de permanencia: se corrige en el admin.
            self.fields["fecha_ingreso"].disabled = True
            self.fields["fecha_ingreso"].help_text = "Ya tiene niveles desde esa fecha; se corrige en el panel de administración."
        else:
            self.initial.setdefault("fecha_ingreso", timezone.localdate())

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        repetido = Nino.objects.filter(curso=self.curso, nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetido.exists():
            raise forms.ValidationError("Ya hay un niño o niña con ese nombre en la sala.")
        return nombre

    def clean_alias(self):
        partes, vistos = [], set()
        for parte in (self.cleaned_data.get("alias") or "").split(","):
            parte = " ".join(parte.split())
            if parte and parte.casefold() not in vistos:
                if len(parte) > LARGO_ALIAS:
                    raise forms.ValidationError(f"Cada apodo puede tener hasta {LARGO_ALIAS} caracteres.")
                vistos.add(parte.casefold())
                partes.append(parte)
        if len(partes) > MAX_ALIAS:
            raise forms.ValidationError(f"Hasta {MAX_ALIAS} apodos.")
        return partes

    def clean(self):
        datos = super().clean()
        hoy = timezone.localdate()
        ingreso, nacimiento = datos.get("fecha_ingreso"), datos.get("fecha_nacimiento")
        if ingreso and ingreso > hoy and not self.fields["fecha_ingreso"].disabled:
            self.add_error("fecha_ingreso", "La fecha de ingreso no puede ser futura.")
        if nacimiento and nacimiento > hoy:
            self.add_error("fecha_nacimiento", "La fecha de nacimiento no puede ser futura.")
        elif nacimiento and ingreso and nacimiento > ingreso:
            self.add_error("fecha_nacimiento", "La fecha de nacimiento es posterior al ingreso.")
        return datos

    def save(self, commit=True):
        self.instance.curso = self.curso
        return super().save(commit=commit)
