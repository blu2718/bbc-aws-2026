"""Pantalla de revisión (PLAN.md, Task 6).

Solo la educadora del curso revisa. Una asistente, la directora o una
educadora de otro curso reciben 404, igual que con un curso que no existe.

Cada acción funciona con HTMX (devuelve el fragmento que reemplaza a la
observación) y también sin JavaScript (redirige a la pantalla de revisión).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .models import Captura
from .permisos import cursos_que_valida
from .revision import (
    AsignarNinoForm,
    ObservacionForm,
    aceptar,
    aceptar_todas,
    descartar,
    pendientes_que_revisa,
    resumen_pendientes,
    revision_del_curso,
)


def _es_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _observacion(request, obs_id):
    """La observación pendiente, si el usuario revisa su curso; si no, 404."""
    return get_object_or_404(
        pendientes_que_revisa(request.user).select_related("captura__curso", "captura__autora", "nino"),
        pk=obs_id,
    )


def _url_revision(curso, obs=None):
    url = reverse("revision", args=[curso.pk])
    return f"{url}#obs-{obs.pk}" if obs else url


def _contexto_revision(curso):
    return {
        "curso": curso,
        "revision": revision_del_curso(curso),
        "resumen": resumen_pendientes(curso),
        "ninos": list(curso.ninos.all()),
    }


def _tarjeta(request, obs, *, resuelta="", error=""):
    """Fragmento de una observación, con el resumen de pendientes fuera de banda."""
    curso = obs.captura.curso
    return render(request, "registro/_tarjeta_revision.html", {
        "obs": obs,
        "curso": curso,
        "ninos": list(curso.ninos.all()),
        "resuelta": resuelta,
        "error": error,
        "resumen": resumen_pendientes(curso),
        "oob": True,
    })


@login_required
@require_GET
def revision(request, curso_id):
    curso = get_object_or_404(cursos_que_valida(request.user).select_related("jardin"), pk=curso_id)
    return render(request, "registro/revision.html", _contexto_revision(curso))


@login_required
@require_GET
def observacion(request, obs_id):
    """La observación sin formulario de edición (para "Cancelar")."""
    obs = _observacion(request, obs_id)
    if not _es_htmx(request):
        return redirect(_url_revision(obs.captura.curso, obs))
    return _tarjeta(request, obs)


@login_required
def editar(request, obs_id):
    obs = _observacion(request, obs_id)
    curso = obs.captura.curso
    form = ObservacionForm(request.POST or None, instance=obs, curso=curso, prefix=f"obs{obs.pk}")
    if request.method == "POST" and form.is_valid():
        obs = form.save()
        if _es_htmx(request):
            return _tarjeta(request, obs)
        messages.success(request, "Se guardaron los cambios de la observación.")
        return redirect(_url_revision(curso, obs))
    plantilla = "registro/_form_observacion.html" if _es_htmx(request) else "registro/revision_editar.html"
    return render(request, plantilla, {"obs": obs, "curso": curso, "form": form})


@login_required
@require_POST
def asignar(request, obs_id):
    """Elige o cambia el niño de una observación pendiente."""
    obs = _observacion(request, obs_id)
    curso = obs.captura.curso
    form = AsignarNinoForm(request.POST, curso=curso)
    error = ""
    if form.is_valid():
        obs.nino = form.cleaned_data["nino"]
        obs.grupal = False
        obs.save(update_fields=["nino", "grupal", "actualizada"])
    else:
        error = "Elige un niño o niña de la lista."
    if _es_htmx(request):
        return _tarjeta(request, obs, error=error)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, f"Observación asignada a {obs.nino}.")
    return redirect(_url_revision(curso, obs))


@login_required
@require_POST
def aceptar_observacion(request, obs_id):
    obs = _observacion(request, obs_id)
    curso = obs.captura.curso
    try:
        aceptar(obs)
    except ValidationError as e:
        if _es_htmx(request):
            return _tarjeta(request, obs, error=e.messages[0])
        messages.error(request, e.messages[0])
        return redirect(_url_revision(curso, obs))
    if _es_htmx(request):
        return _tarjeta(request, obs, resuelta="aceptada")
    messages.success(request, "Observación aceptada.")
    return redirect(_url_revision(curso))


@login_required
@require_POST
def descartar_observacion(request, obs_id):
    obs = _observacion(request, obs_id)
    descartar(obs)
    if _es_htmx(request):
        return _tarjeta(request, obs, resuelta="descartada")
    messages.success(request, "Observación descartada.")
    return redirect(_url_revision(obs.captura.curso))


@login_required
@require_POST
def aceptar_todas_captura(request, captura_id):
    captura = get_object_or_404(Captura.objects.filter(curso__in=cursos_que_valida(request.user)), pk=captura_id)
    aceptadas, sin_nino = aceptar_todas(captura)
    texto = "Se aceptó 1 observación." if aceptadas == 1 else f"Se aceptaron {aceptadas} observaciones."
    if sin_nino == 1:
        texto += " 1 queda pendiente porque no tiene niño o niña asignado."
    elif sin_nino:
        texto += f" {sin_nino} quedan pendientes porque no tienen niño o niña asignado."
    messages.success(request, texto)
    if _es_htmx(request):
        # Se vuelve a dibujar toda la revisión: la captura puede tener notas en la sección de contexto.
        contexto = _contexto_revision(captura.curso) | {"parcial": True}
        return render(request, "registro/_revision_contenido.html", contexto)
    return redirect(_url_revision(captura.curso))
