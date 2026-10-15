"""Integración con Bedrock: funciones puras, sin dependencia de Django."""

from .bedrock import ClienteBedrock, ErrorBedrock
from .foto import ErrorTranscripcion, ImagenInvalida, transcribir_foto, validar_imagen
from .separacion import ErrorSeparacion, separar

__all__ = [
    "ClienteBedrock",
    "ErrorBedrock",
    "ErrorSeparacion",
    "ErrorTranscripcion",
    "ImagenInvalida",
    "separar",
    "transcribir_foto",
    "validar_imagen",
]
