"""Formularios de la Task 3 (fijar el nivel de un niño y editar la tabla de metas)
y de las Tasks 5 y 9 (registrar una nota escrita o un audio).

Las opciones de nivel van del 1 al máximo de la rúbrica del nivel educativo
(`Rubrica.nivel_maximo`); nunca se asume una cantidad fija. El nivel se valida
aquí y otra vez al guardar (`ValidaNivelMixin`).
"""
import uuid
from dataclasses import dataclass

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .ia.transcripcion import formato_audio
from .models import NIVEL_MIN, MetaSemestre, NivelValidado, texto_nivel

# Valores por defecto de la tabla de metas (PLAN.md, "Nivel esperado").
METAS_POR_DEFECTO = {1: 1, 2: 3, 3: 5, 4: 7}
SEMESTRES_CON_META = len(METAS_POR_DEFECTO)
LARGO_COMENTARIO = 500


def _mensaje_rango(nivel_maximo):
    return f"Elige un nivel entre {NIVEL_MIN} y {nivel_maximo}."


def etiqueta_nivel(nivel, descriptor=None):
    """ "3 · Desarrollando" si el descriptor es oficial y tiene nombre; si no, "3".

    Igual que `DescriptorNivel.nombres_por_nucleo`: el nombre provisorio
    ("Nivel 3") repetiría el número.
    """
    nombre = descriptor.nombre if descriptor is not None and not descriptor.provisorio else ""
    return texto_nivel(nivel, nombre)


def nombres_comunes(nombres_por_nucleo):
    """{nivel: nombre} con los nombres que comparten todos los núcleos con rúbrica oficial.

    - nombres_por_nucleo: {sigla: {nivel: nombre}}, como lo entrega
      `DescriptorNivel.nombres_por_nucleo`.

    Un nivel lleva nombre solo si todos los núcleos lo nombran igual. Sirve
    para la tabla de metas, que es del curso y no de un núcleo.
    """
    tablas = list(nombres_por_nucleo.values())
    if not tablas:
        return {}
    niveles = set().union(*tablas)
    comunes = {}
    for nivel in sorted(niveles):
        nombres = {tabla.get(nivel) for tabla in tablas}
        if len(nombres) == 1 and None not in nombres:
            comunes[nivel] = nombres.pop()
    return comunes


def _opciones_de_nivel(nivel_maximo, etiqueta):
    return [(n, etiqueta(n)) for n in range(NIVEL_MIN, nivel_maximo + 1)]


@dataclass(frozen=True)
class Opcion:
    """Una opción del formulario de nivel, para dibujar el radio con su descripción."""

    valor: int
    texto: str        # "3 · Desarrollando" o "3"
    descripcion: str  # del descriptor; "" si no hay
    marcada: bool


class FijarNivelForm(forms.Form):
    """Fija el nivel de un niño en un núcleo. Usar la sigla del núcleo como `prefix`."""

    nivel = forms.TypedChoiceField(coerce=int, empty_value=None, widget=forms.RadioSelect, label="Nivel")
    comentario = forms.CharField(
        required=False, max_length=LARGO_COMENTARIO, label="Comentario (opcional)",
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, nivel_maximo, descriptores, **kwargs):
        """
        - nivel_maximo: el de la rúbrica del nivel educativo del curso.
        - descriptores: {nivel: DescriptorNivel} del núcleo; puede faltar alguno.
        """
        super().__init__(*args, **kwargs)
        self.nivel_maximo = nivel_maximo
        self.descriptores = descriptores
        campo = self.fields["nivel"]
        campo.choices = _opciones_de_nivel(nivel_maximo, lambda n: etiqueta_nivel(n, descriptores.get(n)))
        mensaje = _mensaje_rango(nivel_maximo)
        campo.error_messages = {**campo.error_messages, "required": mensaje, "invalid_choice": mensaje}

    @property
    def opciones(self):
        """[Opcion] del 1 al máximo, con la elegida (o el nivel actual) marcada."""
        elegido = str(self["nivel"].value() or "")
        return [
            Opcion(
                valor=valor,
                texto=texto,
                descripcion=getattr(self.descriptores.get(valor), "descripcion", ""),
                marcada=str(valor) == elegido,
            )
            for valor, texto in self.fields["nivel"].choices
        ]

    def guardar(self, nino, nucleo, usuaria, hoy):
        """Crea el NivelValidado. La fecha y la usuaria vienen del servidor, nunca del POST.

        Devuelve el NivelValidado, o None si el modelo lo rechazó (el error
        queda en el formulario).
        """
        try:
            return NivelValidado.objects.create(
                nino=nino, nucleo=nucleo, nivel=self.cleaned_data["nivel"], fecha=hoy,
                validado_por=usuaria, comentario=self.cleaned_data["comentario"],
            )
        except ValidationError as error:
            self.add_error(None, error.messages)
            return None


LARGO_NOTA = 5000


class CapturaTextoForm(forms.Form):
    """Nota escrita por la educadora o una asistente. El curso y la autora los pone la vista."""

    texto = forms.CharField(
        label="Nota", max_length=LARGO_NOTA,
        help_text="Escribe lo que observaste. Puedes nombrar a varios niños y niñas en la misma nota.",
        widget=forms.Textarea(attrs={"rows": 6, "aria-describedby": "id_texto-ayuda"}),
    )


# 2 minutos en WAV sin comprimir (48 kHz, 16 bits, mono) son unos 11,5 MB; WebM o MP4, 1 a 2 MB.
MAX_BYTES_AUDIO = 15 * 1024 * 1024
FORMATOS_AUDIO = "WebM, MP4, M4A, Ogg, WAV, MP3, FLAC o AMR"


class CapturaAudioForm(forms.Form):
    """Audio dictado (Task 9). El formato se revisa por los primeros bytes, no por el nombre."""

    audio = forms.FileField(
        label="O elige un audio grabado en el teléfono",
        help_text="Máximo 2 minutos.",
        widget=forms.FileInput(attrs={"accept": "audio/*", "capture": "", "aria-describedby": "id_audio-ayuda"}),
    )

    def clean_audio(self):
        archivo = self.cleaned_data["audio"]
        if archivo.size > MAX_BYTES_AUDIO:
            raise ValidationError(f"El audio pesa más de {MAX_BYTES_AUDIO // (1024 * 1024)} MB. Graba uno más corto.")
        cabecera = archivo.read(12)
        archivo.seek(0)
        formato = formato_audio(cabecera)
        if formato is None:
            raise ValidationError(f"El archivo no es un audio compatible ({FORMATOS_AUDIO}).")
        # Nombre propio: el del teléfono puede traer datos personales o caracteres raros.
        archivo.name = f"audio-{uuid.uuid4().hex}.{formato}"
        return archivo


class MetasForm(forms.Form):
    """Tabla de metas del curso: nivel esperado por semestre de permanencia (1 a 4).

    Desde el semestre 5 se espera el máximo de la rúbrica; eso no se edita aquí.
    Un formulario de campos fijos en vez de un formset: no permite filas
    repetidas, borradas ni semestres fuera de rango.
    """

    def __init__(self, *args, curso, nivel_maximo, nombres, **kwargs):
        """
        - nombres: {nivel: nombre} comunes a los núcleos (ver `nombres_comunes`).
        """
        super().__init__(*args, **kwargs)
        self.curso = curso
        self.nivel_maximo = nivel_maximo
        guardadas = dict(curso.metas.values_list("semestre_permanencia", "nivel_esperado"))
        opciones = _opciones_de_nivel(nivel_maximo, lambda n: texto_nivel(n, nombres.get(n, "")))
        mensaje = _mensaje_rango(nivel_maximo)
        for semestre in range(1, SEMESTRES_CON_META + 1):
            inicial = guardadas.get(semestre, min(METAS_POR_DEFECTO[semestre], nivel_maximo))
            self.fields[self.nombre_campo(semestre)] = forms.TypedChoiceField(
                label=f"Semestre {semestre}", choices=opciones, coerce=int, initial=inicial,
                error_messages={"required": mensaje, "invalid_choice": mensaje},
            )

    @staticmethod
    def nombre_campo(semestre):
        return f"semestre_{semestre}"

    def guardar(self):
        """Crea o actualiza una MetaSemestre por semestre, todo o nada.

        Devuelve la lista de metas, o None si el modelo rechazó alguna (el
        error queda en el formulario y no se guarda ninguna).
        """
        try:
            with transaction.atomic():
                return [
                    MetaSemestre.objects.update_or_create(
                        curso=self.curso, semestre_permanencia=semestre,
                        defaults={"nivel_esperado": self.cleaned_data[self.nombre_campo(semestre)]},
                    )[0]
                    for semestre in range(1, SEMESTRES_CON_META + 1)
                ]
        except ValidationError as error:
            self.add_error(None, error.messages)
            return None
