"""Context processors de la app (registrados en config/settings.py)."""
from dataclasses import dataclass

from .permisos import cursos_de
from .revision import cursos_por_revisar

# Sección del menú lateral que se marca como actual, según el nombre de la URL (registro/urls.py).
SECCIONES = {
    "inicio": "inicio",
    "curso": "curso",
    "metas": "metas",
    "ficha": "ficha",
    "fijar_nivel": "ficha",
    "revision": "revision",
    "observacion": "revision",
    "observacion_editar": "revision",
    "observacion_asignar": "revision",
    "observacion_aceptar": "revision",
    "observacion_descartar": "revision",
    "captura_aceptar_todas": "revision",
}


@dataclass(frozen=True)
class CursoMenu:
    """Un curso en el menú lateral, con lo que el usuario puede hacer en él."""

    curso: object
    valida: bool   # educadora del curso: revisa observaciones y edita metas
    ninos: list


def revision(request):
    """`cursos_por_revisar` para el contador de pendientes del menú (Task 6)."""
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    return {"cursos_por_revisar": cursos_por_revisar(usuario)}


def _rol(usuario, cursos):
    """Texto del rol para el pie del menú: "Educadora", "Asistente de párvulos", "Directora" o varios."""
    roles = []
    if any(c.educadora_id == usuario.pk for c in cursos):
        roles.append("Educadora")
    if any(c.educadora_id != usuario.pk and c.jardin.directora_id != usuario.pk for c in cursos):
        roles.append("Asistente de párvulos")
    if any(c.jardin.directora_id == usuario.pk for c in cursos):
        roles.append("Directora")
    return " · ".join(roles)


def navegacion(request):
    """Datos del menú lateral: los cursos que el usuario ve y la sección actual.

    Los cursos salen de `cursos_de`, el mismo filtro de las vistas, así que el menú
    nunca enlaza a un curso ajeno. Las respuestas parciales de HTMX no dibujan el
    menú: solo reciben `menu_seccion`, que usa el contador de pendientes.
    """
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    coincidencia = getattr(request, "resolver_match", None)
    contexto = {"menu_seccion": SECCIONES.get(getattr(coincidencia, "url_name", None), "")}
    if request.headers.get("HX-Request") == "true":
        return contexto

    cursos = list(
        cursos_de(usuario).select_related("jardin").prefetch_related("ninos").order_by("nombre")
    )
    contexto["menu_cursos"] = [
        CursoMenu(curso=c, valida=c.educadora_id == usuario.pk, ninos=list(c.ninos.all())) for c in cursos
    ]
    contexto["menu_rol"] = _rol(usuario, cursos)
    return contexto
