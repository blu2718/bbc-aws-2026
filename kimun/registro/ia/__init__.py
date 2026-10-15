"""Integración con Bedrock y Transcribe: funciones puras, sin dependencia de Django."""

from .bedrock import ClienteBedrock, ErrorBedrock
from .foto import ImagenInvalida, transcribir_foto, validar_imagen
from .separacion import ErrorSeparacion, separar, separar_con_pregunta
from .transcripcion import ClienteTranscribe, ErrorTranscripcion

__all__ = [
    "ClienteBedrock",
    "ClienteTranscribe",
    "ErrorBedrock",
    "ErrorSeparacion",
    "ErrorTranscripcion",
    "ImagenInvalida",
    "separar",
    "separar_con_pregunta",
    "transcribir_foto",
    "validar_imagen",
]
