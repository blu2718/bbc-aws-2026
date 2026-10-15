"""Filtros de la pantalla de revisión (Task 6)."""
from django import template

from ..coincidencia import es_exacta

register = template.Library()


@register.filter
def muestra_nombre_detectado(obs):
    """Si la tarjeta debe mostrar «en la nota dice X».

    Se muestra cuando la observación no tiene niño, o cuando el niño asignado no calza
    exacto con lo que dice la nota (por ejemplo, «Emilia» asignada a Emilio por
    coincidencia aproximada). Nunca en las notas grupales.
    """
    if not obs.nombre_detectado or obs.grupal:
        return False
    return obs.nino is None or not es_exacta(obs.nombre_detectado, obs.nino)
