"""Filtros de acceso. Toda vista que muestre datos de un curso pasa por aquí.

- Educadora y asistentes ven sus cursos; la directora, los cursos de su jardín.
- Educadora, asistentes y la directora (en los cursos de su jardín) registran
  observaciones; solo la educadora del curso revisa observaciones y valida niveles.
- Solo la directora del jardín ve el resumen del jardín (`jardines_que_dirige`), crea
  salas y les asigna el equipo (`cursos_que_administra`). La lista de niños de una sala
  la mantienen la directora y la educadora de la sala (`cursos_con_lista_editable`).

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


# --- Salas del jardín: crear, editar y mantener la lista de niños -----------------------
# La directora crea las salas de su jardín y les asigna educadora y asistentes. La lista de
# niños de una sala la mantienen la directora y la educadora de esa sala (es quien conoce
# los apodos con que se escriben en las notas). Las asistentes no editan.


def cursos_que_administra(usuario):
    """Salas que el usuario puede editar (nombre, nivel educativo y equipo): las de los jardines que dirige."""
    if not usuario.is_authenticated:
        return Curso.objects.none()
    return Curso.objects.filter(jardin__directora=usuario)


def cursos_con_lista_editable(usuario):
    """Salas donde el usuario agrega niños y edita sus datos: la directora del jardín y la educadora de la sala."""
    if not usuario.is_authenticated:
        return Curso.objects.none()
    return Curso.objects.filter(Q(educadora=usuario) | Q(jardin__directora=usuario)).distinct()


def ninos_con_datos_editables(usuario):
    return Nino.objects.filter(curso__in=cursos_con_lista_editable(usuario))


def puede_administrar(usuario, curso):
    return usuario.is_authenticated and curso.jardin.directora_id == usuario.pk


def puede_editar_lista(usuario, curso):
    return usuario.is_authenticated and usuario.pk in (curso.educadora_id, curso.jardin.directora_id)


def ninos_que_valida(usuario):
    """Niños de los cursos donde el usuario valida niveles (solo la educadora del curso)."""
    return Nino.objects.filter(curso__in=cursos_que_valida(usuario))


# --- Instrumentos estandarizados (Task 14) -------------------------------------------
# Un resultado de un instrumento es un dato sensible (puede ser de salud): lo ven solo la
# educadora del curso y la directora del jardín. Lo carga, corrige y confirma la educadora.
# Las asistentes no lo ven, aunque vean la ficha.


def cursos_que_ven_instrumentos(usuario):
    if not usuario.is_authenticated:
        return Curso.objects.none()
    return Curso.objects.filter(Q(educadora=usuario) | Q(jardin__directora=usuario)).distinct()


def resultados_que_ve(usuario):
    from .models import ResultadoInstrumento

    return ResultadoInstrumento.objects.filter(nino__curso__in=cursos_que_ven_instrumentos(usuario))


def resultados_que_edita(usuario):
    from .models import ResultadoInstrumento

    return ResultadoInstrumento.objects.filter(nino__curso__in=cursos_que_valida(usuario))


def puede_ver_instrumentos(usuario, curso):
    return cursos_que_ven_instrumentos(usuario).filter(pk=curso.pk).exists()

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
