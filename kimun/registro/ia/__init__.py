"""Integración con Bedrock y Transcribe: funciones puras, sin dependencia de Django."""

from .bedrock import ClienteBedrock, ErrorBedrock
from .lectura import ErrorLectura, leer_foto
from .separacion import ErrorSeparacion, separar
from .transcripcion import ClienteTranscribe, ErrorTranscripcion

__all__ = [
    "ClienteBedrock",
    "ClienteTranscribe",
    "ErrorBedrock",
    "ErrorLectura",
    "ErrorSeparacion",
    "ErrorTranscripcion",
    "leer_foto",
    "separar",
]
