"""Solicitudes manuales y reintentos de propuestas, solo para la educadora."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .models import Nucleo, PropuestaNivel, Rubrica
from .ficha import armar_ficha, descriptores_del_nucleo
from .forms import FijarNivelForm
from .permisos import ninos_que_valida
from .propuestas import solicitar_propuesta as encolar
from .propuestas import resolver_propuesta, rubrica_completa
from .views import _es_htmx, _pagina_ficha, _parcial_nucleo

MENSAJE_SIN_RUBRICA = "Este núcleo aún no tiene una rúbrica completa para su nivel educativo: no se pueden proponer niveles."


def _encolar_si_hay_rubrica(nino, nucleo, **opciones):
    """(propuesta, creada), o (None, False) si la rúbrica del núcleo está incompleta y la propuesta fallaría."""
    if not rubrica_completa(nino.curso.nivel_educativo, nucleo):
        return None, False
    return encolar(nino, nucleo, **opciones)


def _respuesta(request, nino, nucleo, propuesta, creada):
    mensaje = "Se solicitó una propuesta de nivel." if creada else "La propuesta ya está solicitada o disponible."
    if propuesta is None:
        mensaje = MENSAJE_SIN_RUBRICA
    elif propuesta.estado == PropuestaNivel.Estado.ERROR:
        mensaje = "La propuesta tiene un error. Usa Reintentar propuesta para volver a solicitarla."
    if _es_htmx(request):
        return _parcial_nucleo(request, nino, nucleo.sigla, mensaje=mensaje)
    messages.info(request, mensaje)
    return redirect(f"{reverse('ficha', args=[nino.pk])}#nucleo-{nucleo.sigla}")


@login_required
@require_POST
def solicitar_propuesta(request, nino_id, sigla):
    nino = get_object_or_404(ninos_que_valida(request.user).select_related("curso__jardin"), pk=nino_id)
    nucleo = get_object_or_404(Nucleo, sigla=sigla)
    propuesta, creada = _encolar_si_hay_rubrica(nino, nucleo)
    return _respuesta(request, nino, nucleo, propuesta, creada)


@login_required
@require_POST
def reintentar_propuesta(request, propuesta_id):
    anterior = get_object_or_404(PropuestaNivel.objects.select_related("nino__curso__jardin", "nucleo").filter(
        nino__in=ninos_que_valida(request.user), estado=PropuestaNivel.Estado.ERROR,
    ), pk=propuesta_id)
    propuesta, creada = _encolar_si_hay_rubrica(anterior.nino, anterior.nucleo, reintentar=True)
    return _respuesta(request, anterior.nino, anterior.nucleo, propuesta, creada)


@login_required
@require_GET
def estado_propuesta(request, nino_id, sigla):
    nino = get_object_or_404(ninos_que_valida(request.user).select_related("curso__jardin"), pk=nino_id)
    nucleo = get_object_or_404(Nucleo, sigla=sigla)
    if not _es_htmx(request):
        return redirect(f"{reverse('ficha', args=[nino.pk])}#nucleo-{sigla}")
    ficha = armar_ficha(nino, request.user)
    return render(request, "registro/_propuesta_nivel.html", {"ficha": ficha, "nf": ficha.nucleo(nucleo.sigla)})


def _decidir(request, propuesta_id, accion):
    propuesta = get_object_or_404(PropuestaNivel.objects.select_related("nino__curso__jardin", "nucleo").filter(
        nino__in=ninos_que_valida(request.user),
    ), pk=propuesta_id)
    nino, nucleo = propuesta.nino, propuesta.nucleo
    form, resultado, error = None, None, ""
    if accion == "ajustar":
        form = FijarNivelForm(request.POST, prefix=f"propuesta-{propuesta.pk}",
                              nivel_maximo=Rubrica.nivel_maximo(nino.curso.nivel_educativo),
                              descriptores=descriptores_del_nucleo(nino.curso.nivel_educativo, nucleo))
    if form is None or form.is_valid():
        try:
            datos = {"nivel": form.cleaned_data["nivel"], "comentario": form.cleaned_data["comentario"]} if form else {}
            resultado = resolver_propuesta(propuesta, request.user, accion=accion, **datos)
        except ValidationError as fallo:
            error = " ".join(fallo.messages)
            if form:
                form.add_error(None, fallo.messages)
                # El formulario ya muestra el error, sin duplicarlo en el panel. La ficha solo dibuja ese
                # formulario si la propuesta tiene evidencia suficiente; si no, el error va en el panel.
                if PropuestaNivel.objects.filter(pk=propuesta.pk, estado=PropuestaNivel.Estado.LISTA,
                                                 evidencia_suficiente=True).exists():
                    error = ""
    if resultado is None:
        formularios = {propuesta.pk: form} if form else {}
        if _es_htmx(request):
            return _parcial_nucleo(request, nino, nucleo.sigla, formularios_propuesta=formularios, error_propuesta=error)
        return _pagina_ficha(request, nino, formularios_propuesta=formularios, errores_propuesta={nucleo.sigla: error})
    mensaje = {"aceptar": "Propuesta aceptada.", "ajustar": "Se guardó el nivel elegido por la educadora.",
               "rechazar": "Propuesta rechazada."}[accion] if resultado.realizada else "La propuesta ya estaba resuelta."
    if _es_htmx(request):
        return _parcial_nucleo(request, nino, nucleo.sigla, mensaje=mensaje)
    messages.success(request, mensaje)
    return redirect(f"{reverse('ficha', args=[nino.pk])}#nucleo-{nucleo.sigla}")


@login_required
@require_POST
def aceptar_propuesta(request, propuesta_id):
    return _decidir(request, propuesta_id, "aceptar")


@login_required
@require_POST
def ajustar_propuesta(request, propuesta_id):
    return _decidir(request, propuesta_id, "ajustar")


@login_required
@require_POST
def rechazar_propuesta(request, propuesta_id):
    return _decidir(request, propuesta_id, "rechazar")
