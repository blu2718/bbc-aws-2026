"""Formulario de la pantalla "¿Qué quieres registrar?" (diseno-interfaz.jpg, pantalla I).

Una captura por envío: texto, foto (con texto opcional) o audio (con texto
opcional). El tipo del archivo se revisa por sus primeros bytes, no por el
nombre ni por lo que dice el navegador, y se guarda con un nombre al azar
para no exponer el nombre original.
"""
from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError

from .ia.lectura import formato_de_imagen
from .models import Captura

MAX_MB_FOTO = 10
MAX_MB_AUDIO = 20
LARGO_TEXTO = 4000
EXTENSIONES = {
    "jpeg": "jpg", "png": "png", "gif": "gif", "webp": "webp",
    "webm": "webm", "ogg": "ogg", "mp4": "m4a", "wav": "wav", "mp3": "mp3",
}


def formato_de_audio(cabecera):
    """'webm', 'ogg', 'mp4', 'wav' o 'mp3' según los primeros bytes; None si no es uno de esos.

    Son formatos que acepta Transcribe y que graban los navegadores (WebM/Opus en
    Android, MP4 en iPhone).
    """
    if cabecera.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    if cabecera.startswith(b"OggS"):
        return "ogg"
    if cabecera[4:8] == b"ftyp":
        return "mp4"
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WAVE":
        return "wav"
    if cabecera.startswith(b"ID3") or cabecera[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3"
    return None


def _revisar_archivo(archivo, maximo_mb, detectar, mensaje):
    if not archivo:
        return None
    if archivo.size > maximo_mb * 1024 * 1024:
        raise ValidationError(f"El archivo pesa más de {maximo_mb} MB.")
    cabecera = archivo.read(16)
    archivo.seek(0)
    formato = detectar(cabecera)
    if formato is None:
        raise ValidationError(mensaje)
    archivo.formato_detectado = formato
    return archivo


class RegistroForm(forms.Form):
    texto = forms.CharField(
        label="Lo que pasó", required=False, max_length=LARGO_TEXTO,
        widget=forms.Textarea(attrs={"rows": 1, "placeholder": "Escribe lo que pasó…"}),
    )
    foto = forms.FileField(label="Foto del cuaderno o del post-it", required=False)
    audio = forms.FileField(label="Audio", required=False)

    def clean_foto(self):
        return _revisar_archivo(
            self.cleaned_data.get("foto"), MAX_MB_FOTO, formato_de_imagen, "La foto debe ser JPEG, PNG, GIF o WebP."
        )

    def clean_audio(self):
        return _revisar_archivo(
            self.cleaned_data.get("audio"), MAX_MB_AUDIO, formato_de_audio, "El audio debe ser WebM, Ogg, MP4, WAV o MP3."
        )

    def clean(self):
        datos = super().clean()
        if self.errors:
            return datos
        foto, audio, texto = datos.get("foto"), datos.get("audio"), datos.get("texto")
        if foto and audio:
            raise ValidationError("Envía la foto y el audio por separado.")
        if not (texto or foto or audio):
            raise ValidationError("Escribe lo que pasó, adjunta una foto o graba un audio.")
        return datos

    def guardar(self, curso, autora):
        """Crea la captura pendiente con su archivo original, si lo hay."""
        foto, audio = self.cleaned_data.get("foto"), self.cleaned_data.get("audio")
        archivo = foto or audio
        tipo = Captura.Tipo.FOTO if foto else Captura.Tipo.AUDIO if audio else Captura.Tipo.TEXTO
        captura = Captura(curso=curso, autora=autora, tipo=tipo, texto_original=self.cleaned_data.get("texto", ""))
        if archivo:
            nombre = f"{uuid4().hex}.{EXTENSIONES[archivo.formato_detectado]}"
            captura.archivo.save(nombre, archivo, save=False)
        captura.save()
        return captura
