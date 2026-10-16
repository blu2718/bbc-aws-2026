"""Context processors de la app (registrados en config/settings.py)."""
from .models import AvisoProteccion
from .permisos import avisos_que_ve
from .revision import cursos_por_revisar


def revision(request):
    """`cursos_por_revisar` para el contador de pendientes de la barra de navegación (Task 6)."""
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    return {
        "cursos_por_revisar": cursos_por_revisar(usuario),
        # Avisos de protección por atender (Task 13): solo la cantidad, sin nombres ni texto.
        "avisos_pendientes": avisos_que_ve(usuario).filter(estado=AvisoProteccion.Estado.PENDIENTE).count(),
    }
