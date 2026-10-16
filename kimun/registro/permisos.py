"""Filtros de acceso. Toda vista que muestre datos de un curso pasa por aquí.

- Educadora y asistentes ven sus cursos; la directora, los cursos de su jardín.
- Educadora, asistentes y la directora (en los cursos de su jardín) registran
  observaciones; solo la educadora del curso revisa observaciones y valida niveles.
- Solo la directora del jardín ve el resumen del jardín (`jardines_que_dirige`).

Usar `get_object_or_404(cursos_de(request.user), pk=...)` para que un curso
ajeno responda 404 y no revele que existe. Para acciones de revisión o
validación, usar `cursos_que_valida`.
"""
from django.db.models import Q

from .models import Curso, Jardin, Nino


def jardines_que_dirige(usuario):
    """Jardines de los que el usuario es directora (vista del jardín, Task 12)."""
    if not usuario.is_authenticated:
        return Jardin.objects.none()
    return Jardin.objects.filter(directora=usuario)


def cursos_de(usuario):
    """Cursos que el usuario puede ver."""
    if not usuario.is_authenticated:
        return Curso.objects.none()
    return Curso.objects.filter(
        Q(educadora=usuario) | Q(asistentes=usuario) | Q(jardin__directora=usuario)
    ).distinct()


def cursos_que_valida(usuario):
    """Cursos donde el usuario puede revisar observaciones y validar niveles."""
    if not usuario.is_authenticated:
        return Curso.objects.none()
    return Curso.objects.filter(educadora=usuario)


def cursos_donde_registra(usuario):
    """Cursos donde el usuario puede registrar capturas (educadora, asistente o directora del jardín)."""
    if not usuario.is_authenticated:
        return Curso.objects.none()
    return Curso.objects.filter(
        Q(educadora=usuario) | Q(asistentes=usuario) | Q(jardin__directora=usuario)
    ).distinct()


def puede_validar(usuario, curso):
    return usuario.is_authenticated and curso.educadora_id == usuario.pk


def ninos_de(usuario):
    return Nino.objects.filter(curso__in=cursos_de(usuario))


def ninos_que_valida(usuario):
    """Niños de los cursos donde el usuario valida niveles (solo la educadora del curso)."""
    return Nino.objects.filter(curso__in=cursos_que_valida(usuario))


def avisos_que_ve(usuario):
    """Avisos de protección (Task 13) que el usuario puede ver: los de la educadora del curso
    y los de la directora del jardín. Las asistentes, incluida quien registró, no los ven.
    Quién los recibe sale de `datos/protocolo_proteccion.json` ("destinatarios").
    """
    from .models import AvisoProteccion
    from .protocolo import leer_protocolo

    if not usuario.is_authenticated:
        return AvisoProteccion.objects.none()
    destinatarios = leer_protocolo().destinatarios
    filtro = Q(pk__in=[])
    if "educadora" in destinatarios:
        filtro |= Q(captura__curso__educadora=usuario)
    if "directora" in destinatarios:
        filtro |= Q(captura__curso__jardin__directora=usuario)
    return AvisoProteccion.objects.filter(filtro).distinct()
