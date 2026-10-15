"""Context processors de la app (registrados en config/settings.py)."""
from .revision import cursos_por_revisar


def revision(request):
    """`cursos_por_revisar` para el contador de pendientes de la barra de navegación (Task 6)."""
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    return {"cursos_por_revisar": cursos_por_revisar(usuario)}
