"""Instrumentos estandarizados en la ficha (Task 14) y correcciones con historial.

- Ver un resultado: la educadora del curso y la directora del jardín (`resultados_que_ve`).
  Las asistentes y las demás educadoras reciben 404.
- Cargar, revisar, confirmar, corregir y descartar: solo la educadora (`resultados_que_edita`).
- La hoja (foto o PDF) la lee `manage.py procesar_capturas` en segundo plano y se borra
  apenas se lee; la página consulta el estado con HTMX, igual que una captura.
- Corregir o retirar una observación ya aceptada: solo la educadora, con motivo.

Todo cambio queda en el historial (`historial.py`), que cada pantalla muestra con el
resultado de verificar su cadena de hashes.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import resultados as servicio
from .historial import ConflictoHistorial, historial_legible, verificar
from .instrumentos import etiquetador, reintentar_lectura, resumir
from .models import Instrumento, Observacion, ResultadoInstrumento
from .permisos import (
    cursos_de, cursos_que_valida, ninos_que_valida, puede_validar, puede_ver_instrumentos, resultados_que_edita,
    resultados_que_ve,
)

PENDIENTES = (ResultadoInstrumento.Estado.POR_LEER, ResultadoInstrumento.Estado.LEYENDO)


def _es_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _resultado(request, resultado_id, editable=False):
    qs = resultados_que_edita(request.user) if editable else resultados_que_ve(request.user)
    return get_object_or_404(qs.select_related("nino__curso__jardin", "instrumento", "registrado_por"), pk=resultado_id)


# --- En la ficha --------------------------------------------------------------------------


def resultados_de_la_ficha(nino, usuario):
    """Para la sección de la ficha: None si el usuario no los ve; si no, confirmados agrupados y pendientes."""
    if not puede_ver_instrumentos(usuario, nino.curso):
        return None
    todos = list(resultados_que_ve(usuario).filter(nino=nino).select_related("instrumento", "nino")
                 .exclude(estado=ResultadoInstrumento.Estado.DESCARTADO))
    grupos = {}
    for r in todos:
        if r.estado == ResultadoInstrumento.Estado.CONFIRMADO:
            grupos.setdefault(r.instrumento, []).append((r, resumir(r)))
    for lista in grupos.values():
        lista.sort(key=lambda par: par[0].fecha_aplicacion, reverse=True)
    return {
        "grupos": sorted(grupos.items(), key=lambda par: (par[0].orden, par[0].codigo)),
        "pendientes": [r for r in todos if r.estado != ResultadoInstrumento.Estado.CONFIRMADO],
        "puede_editar": puede_validar(usuario, nino.curso),
    }


# --- Cargar -------------------------------------------------------------------------------


@login_required
@require_http_methods(["GET", "POST"])
def nuevo(request, nino_id):
    """Elegir cómo cargar: subir la hoja (Kimün la lee) o ingresar los datos a mano."""
    nino = get_object_or_404(ninos_que_valida(request.user).select_related("curso__jardin"), pk=nino_id)
    form = servicio.SubirHojaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        resultado = servicio.subir_hoja(nino, request.user, form)
        return redirect("resultado_instrumento", resultado_id=resultado.pk)
    return render(request, "registro/instrumento_nuevo.html", {
        "nino": nino, "curso": nino.curso, "form": form, "instrumentos": Instrumento.objects.all(),
    })


@login_required
@require_http_methods(["GET", "POST"])
def nuevo_manual(request, nino_id, codigo):
    nino = get_object_or_404(ninos_que_valida(request.user).select_related("curso__jardin"), pk=nino_id)
    instrumento = get_object_or_404(Instrumento, codigo=codigo)
    form = servicio.ResultadoForm(request.POST or None, instrumento=instrumento, nacimiento=nino.fecha_nacimiento,
                                  initial={"origen": ResultadoInstrumento.Origen.JARDIN if instrumento.ambito == "educativo"
                                           else ResultadoInstrumento.Origen.SALUD})
    if request.method == "POST" and form.is_valid():
        resultado = servicio.crear_manual(nino, request.user, form)
        messages.success(request, f"Se guardó el resultado de {instrumento.codigo}.")
        return redirect("resultado_instrumento", resultado_id=resultado.pk)
    return render(request, "registro/instrumento_editar.html", {
        "nino": nino, "curso": nino.curso, "form": form, "instrumento": instrumento, "modo": "manual",
    })


# --- Ver ----------------------------------------------------------------------------------


def _contexto(request, resultado):
    puede_editar = puede_validar(request.user, resultado.nino.curso)
    return {
        "resultado": resultado, "nino": resultado.nino, "curso": resultado.nino.curso,
        "resumen": resumir(resultado), "puede_editar": puede_editar,
        "historial": historial_legible(resultado, etiquetador(resultado.instrumento)),
        "integridad": verificar(resultado), "pendiente": resultado.estado in PENDIENTES,
    }


@login_required
@require_GET
def resultado(request, resultado_id):
    return render(request, "registro/instrumento_resultado.html", _contexto(request, _resultado(request, resultado_id)))


@login_required
@require_GET
def estado(request, resultado_id):
    r = _resultado(request, resultado_id)
    if not _es_htmx(request):
        return redirect("resultado_instrumento", resultado_id=r.pk)
    if r.estado in PENDIENTES:
        return render(request, "registro/_instrumento_leyendo.html", {"resultado": r})
    # Terminó de leer: la página completa se vuelve a cargar con lo leído.
    respuesta = render(request, "registro/_instrumento_leyendo.html", {"resultado": r})
    respuesta["HX-Refresh"] = "true"
    return respuesta


# --- Revisar, confirmar, corregir, descartar ----------------------------------------------


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, resultado_id):
    r = _resultado(request, resultado_id, editable=True)
    if r.estado not in (ResultadoInstrumento.Estado.POR_REVISAR, ResultadoInstrumento.Estado.CONFIRMADO):
        messages.info(request, "Este resultado no se puede editar en su estado actual.")
        return redirect("resultado_instrumento", resultado_id=r.pk)
    confirmado = r.estado == ResultadoInstrumento.Estado.CONFIRMADO
    instrumento = r.instrumento
    codigo = request.POST.get("instrumento") or request.GET.get("instrumento")
    if codigo and not confirmado:
        instrumento = get_object_or_404(Instrumento, codigo=codigo)
    if instrumento is None:
        instrumento = get_object_or_404(Instrumento, codigo="OTRO")
    form = servicio.ResultadoForm(request.POST or None, instrumento=instrumento, resultado=r,
                                  requiere_motivo=confirmado, nacimiento=r.nino.fecha_nacimiento)
    if request.method == "POST" and form.is_valid():
        try:
            _, cambio = servicio.guardar(r, request.user, form, confirmar="confirmar" in request.POST)
        except (ValidationError, ConflictoHistorial) as error:
            form.add_error(None, error.messages if isinstance(error, ValidationError) else str(error))
        else:
            if not cambio:
                messages.info(request, "No había cambios que guardar.")
            elif confirmado:
                messages.success(request, "Se guardó la corrección. Queda en el historial.")
            elif "confirmar" in request.POST:
                messages.success(request, "Resultado confirmado: ya aparece en la ficha.")
            else:
                messages.success(request, "Se guardaron los cambios. Falta confirmarlo.")
            return redirect("resultado_instrumento", resultado_id=r.pk)
    return render(request, "registro/instrumento_editar.html", {
        "nino": r.nino, "curso": r.nino.curso, "form": form, "instrumento": instrumento, "resultado": r,
        "modo": "corregir" if confirmado else "revisar", "instrumentos": Instrumento.objects.all(),
        "resumen": resumir(r),
    })


@login_required
@require_POST
def descartar(request, resultado_id):
    r = _resultado(request, resultado_id, editable=True)
    try:
        servicio.descartar(r, request.user, request.POST.get("motivo"))
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, "Resultado descartado. Queda en el historial y ya no aparece en la ficha.")
    return redirect("resultado_instrumento", resultado_id=r.pk)


@login_required
@require_POST
def reintentar(request, resultado_id):
    r = _resultado(request, resultado_id, editable=True)
    if not reintentar_lectura(r):
        messages.error(request, "La hoja ya no está guardada: ingresa los datos a mano o súbela de nuevo.")
    return redirect("resultado_instrumento", resultado_id=r.pk)


# --- Observaciones aceptadas: corregir, retirar, historial ---------------------------------


def _aceptada(request, obs_id, editable):
    cursos = cursos_que_valida(request.user) if editable else cursos_de(request.user)
    return get_object_or_404(
        Observacion.objects.filter(captura__curso__in=cursos).select_related("captura__curso", "nino"),
        pk=obs_id,
    )


def _volver_a_ficha(obs):
    if obs.nino_id:
        return f"{reverse('ficha', args=[obs.nino_id])}#titulo-historial"
    return reverse("captura", args=[obs.captura_id])


@login_required
@require_http_methods(["GET", "POST"])
def corregir_observacion(request, obs_id):
    obs = _aceptada(request, obs_id, editable=True)
    if obs.estado != Observacion.Estado.ACEPTADA:
        messages.info(request, "Solo se corrigen observaciones aceptadas.")
        return redirect(_volver_a_ficha(obs))
    nino_antes = obs.nino_id
    form = servicio.CorregirObservacionForm(request.POST or None, instance=obs, curso=obs.captura.curso,
                                            prefix=f"obs{obs.pk}")
    if request.method == "POST" and form.is_valid():
        if not form.cleaned_data.get("grupal") and form.cleaned_data.get("nino") is None:
            form.add_error("nino", "Una observación aceptada debe tener niño o niña, o ser una nota del grupo.")
        else:
            try:
                obs, cambio = servicio.corregir_observacion(obs, request.user, form)
            except (ValidationError, ConflictoHistorial) as error:
                form.add_error(None, error.messages if isinstance(error, ValidationError) else str(error))
            else:
                messages.success(request, "Se guardó la corrección. Queda en el historial." if cambio
                                 else "No había cambios que guardar.")
                destino = obs if obs.nino_id else Observacion(nino_id=nino_antes, captura_id=obs.captura_id)
                return redirect(_volver_a_ficha(destino))
    return render(request, "registro/observacion_corregir.html", {
        "obs": obs, "curso": obs.captura.curso, "form": form,
        "historial": historial_legible(obs), "integridad": verificar(obs),
    })


@login_required
@require_POST
def retirar_observacion(request, obs_id):
    obs = _aceptada(request, obs_id, editable=True)
    try:
        servicio.retirar_observacion(obs, request.user, request.POST.get("motivo"))
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
        return redirect("observacion_corregir", obs_id=obs.pk)
    messages.success(request, "La observación se retiró de la ficha. Queda en el historial.")
    return redirect(_volver_a_ficha(obs))


@login_required
@require_GET
def historial_observacion(request, obs_id):
    obs = _aceptada(request, obs_id, editable=False)
    return render(request, "registro/observacion_historial.html", {
        "obs": obs, "curso": obs.captura.curso, "historial": historial_legible(obs), "integridad": verificar(obs),
        "puede_editar": puede_validar(request.user, obs.captura.curso),
    })
