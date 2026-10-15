"""Integración con Bedrock: funciones puras, sin dependencia de Django."""

from .bedrock import ClienteBedrock, ErrorBedrock
from .separacion import ErrorSeparacion, separar

__all__ = ["ClienteBedrock", "ErrorBedrock", "ErrorSeparacion", "separar"]
