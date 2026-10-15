"""Filtros de acceso. Toda vista que muestre datos de un curso pasa por aquí.

- Educadora y asistentes ven sus cursos; la directora, los cursos de su jardín.
- Solo la educadora del curso revisa observaciones y valida niveles.

Usar `get_object_or_404(cursos_de(request.user), pk=...)` para que un curso
ajeno responda 404 y no revele que existe. Para acciones de revisión o
validación, usar `cursos_que_valida`.
"""
from django.db.models import Q

from .models import Curso, Nino


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
    """Cursos donde el usuario puede registrar capturas (educadora o asistente)."""
    if not usuario.is_authenticated:
        return Curso.objects.none()
    return Curso.objects.filter(Q(educadora=usuario) | Q(asistentes=usuario)).distinct()


def puede_validar(usuario, curso):
    return usuario.is_authenticated and curso.educadora_id == usuario.pk


def ninos_de(usuario):
    return Nino.objects.filter(curso__in=cursos_de(usuario))


def ninos_que_valida(usuario):
    """Niños de los cursos donde el usuario valida niveles (solo la educadora del curso)."""
    return Nino.objects.filter(curso__in=cursos_que_valida(usuario))
