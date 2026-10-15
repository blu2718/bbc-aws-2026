"""Integración con Bedrock y Transcribe: funciones puras, sin dependencia de Django."""

from .bedrock import ClienteBedrock, ErrorBedrock
from .separacion import ErrorSeparacion, separar
from .transcripcion import ClienteTranscribe, ErrorTranscripcion

__all__ = [
    "ClienteBedrock",
    "ClienteTranscribe",
    "ErrorBedrock",
    "ErrorSeparacion",
    "ErrorTranscripcion",
    "separar",
]
