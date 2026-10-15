"""Formularios de captura (Task 8: foto).

El navegador achica la foto antes de subirla (`static/registro/captura_foto.js`),
pero el servidor no confía en eso: revisa el formato por la firma del archivo
(no por la extensión ni por el tipo que manda el navegador) y el tamaño máximo
que acepta Bedrock.
"""
from django import forms

from .ia import ImagenInvalida, validar_imagen
from .ia.foto import EXTENSIONES, TAMANO_MAXIMO, mensaje_demasiado_grande


class FotoForm(forms.Form):
    foto = forms.FileField(
        label="Foto de la nota",
        error_messages={"required": "Toma o elige una foto.", "empty": "El archivo está vacío."},
        # capture="environment" abre la cámara trasera en el teléfono; en el computador, el selector de archivos.
        widget=forms.FileInput(
            attrs={"accept": "image/*", "capture": "environment", "aria-describedby": "ayuda-foto estado-foto"}
        ),
    )

    def clean_foto(self):
        archivo = self.cleaned_data["foto"]
        # Primero el tamaño declarado, para no leer en memoria un archivo enorme.
        if archivo.size > TAMANO_MAXIMO:
            raise forms.ValidationError(mensaje_demasiado_grande(archivo.size))
        contenido = archivo.read()
        try:
            formato = validar_imagen(contenido)
        except ImagenInvalida as error:
            raise forms.ValidationError(str(error)) from error
        self.contenido = contenido
        self.extension = EXTENSIONES[formato]
        return archivo
