"""Integración con Bedrock: funciones puras, sin dependencia de Django."""

from .bedrock import ClienteBedrock, ErrorBedrock
from .separacion import ErrorSeparacion, separar
from .seudonimo import MARCADOR_AMBIGUO, Seudonimizador, seudonimizar_texto
from .propuesta import ErrorConfiguracionPropuesta, ErrorPropuesta, proponer

__all__ = [
    "ClienteBedrock", "ErrorBedrock", "ErrorSeparacion", "separar",
    "MARCADOR_AMBIGUO", "Seudonimizador", "seudonimizar_texto",
    "ErrorConfiguracionPropuesta", "ErrorPropuesta", "proponer",
]
