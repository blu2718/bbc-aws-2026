"""Mantener las salas de un jardín (`salas.py`).

- `sala_nueva` y `sala_editar`: solo la directora del jardín. Crea una sala o cambia su
  nombre, nivel educativo y equipo (educadora y asistentes).
- `ninos_sala`, `nino_nuevo` y `nino_editar`: la directora y la educadora de la sala.
  Las asistentes y el resto reciben 404, como en toda la app.

No se borran salas ni niños desde aquí: tienen observaciones, niveles e historial. Eso
queda en el panel de administración.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .permisos import (
    cursos_con_lista_editable,
    cursos_que_administra,
    jardines_que_dirige,
    ninos_con_datos_editables,
    puede_administrar,
)
from .salas import NinoForm, SalaForm, nombre_de


def _render(request, plantilla, contexto, form):
    return render(request, plantilla, contexto, status=400 if form.errors else 200)


@login_required
@require_http_methods(["GET", "POST"])
def sala_nueva(request, jardin_id):
    jardin = get_object_or_404(jardines_que_dirige(request.user), pk=jardin_id)
    form = SalaForm(request.POST or None, jardin=jardin)
    if request.method == "POST" and form.is_valid():
        curso = form.save()
        messages.success(request, f"Sala {curso.nombre} creada. Ahora agrega a sus niños y niñas.")
        return redirect("ninos_sala", curso_id=curso.pk)
    return _render(request, "registro/sala_form.html", {"jardin": jardin, "form": form, "sala": None}, form)


@login_required
@require_http_methods(["GET", "POST"])
def sala_editar(request, curso_id):
    curso = get_object_or_404(cursos_que_administra(request.user).select_related("jardin", "educadora"), pk=curso_id)
    educadora_antes = curso.educadora
    form = SalaForm(request.POST or None, instance=curso, jardin=curso.jardin)
    if request.method == "POST" and form.is_valid():
        curso = form.save()
        mensaje = f"Se guardaron los cambios de {curso.nombre}."
        if curso.educadora_id != educadora_antes.pk:
            mensaje += (f" Ahora {nombre_de(curso.educadora)} revisa sus observaciones y fija los niveles;"
                        f" {nombre_de(educadora_antes)} ya no ve la sala, salvo que esté en otra.")
        messages.success(request, mensaje)
        return redirect("jardin", jardin_id=curso.jardin_id)
    return _render(request, "registro/sala_form.html", {"jardin": curso.jardin, "form": form, "sala": curso}, form)


@login_required
@require_GET
def ninos_sala(request, curso_id):
    curso = get_object_or_404(cursos_con_lista_editable(request.user).select_related("jardin", "educadora"), pk=curso_id)
    return render(request, "registro/ninos_sala.html", {
        "curso": curso, "ninos": curso.ninos.all(), "puede_administrar": puede_administrar(request.user, curso),
    })


@login_required
@require_http_methods(["GET", "POST"])
def nino_nuevo(request, curso_id):
    curso = get_object_or_404(cursos_con_lista_editable(request.user).select_related("jardin"), pk=curso_id)
    form = NinoForm(request.POST or None, curso=curso)
    if request.method == "POST" and form.is_valid():
        nino = form.save()
        messages.success(request, f"{nino.nombre} quedó en {curso.nombre}, en nivel 1 en todos los núcleos.")
        if "otro" in request.POST:
            return redirect("nino_nuevo", curso_id=curso.pk)
        return redirect("ninos_sala", curso_id=curso.pk)
    return _render(request, "registro/nino_form.html", {"curso": curso, "form": form, "nino": None}, form)


@login_required
@require_http_methods(["GET", "POST"])
def nino_editar(request, nino_id):
    nino = get_object_or_404(ninos_con_datos_editables(request.user).select_related("curso__jardin"), pk=nino_id)
    form = NinoForm(request.POST or None, instance=nino, curso=nino.curso)
    if request.method == "POST" and form.is_valid():
        nino = form.save()
        messages.success(request, f"Se guardaron los datos de {nino.nombre}.")
        return redirect("ninos_sala", curso_id=nino.curso_id)
    return _render(request, "registro/nino_form.html", {"curso": nino.curso, "form": form, "nino": nino}, form)
