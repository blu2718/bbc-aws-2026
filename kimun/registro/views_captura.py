"""Registro de notas escritas y audios (PLAN.md, Tasks 5 y 9).

Registran la educadora y las asistentes del curso (`cursos_donde_registra`). La
directora o una educadora de otro curso reciben 404. La nota o el audio quedan
pendientes y `manage.py procesar_capturas` los separa en observaciones para la
revisión (el audio, después de transcribirlo).

Debajo del formulario va la lista de las últimas capturas de la usuaria en el curso,
con su estado. Mientras alguna esté pendiente o procesando (y no atascada), la lista se
refresca sola con HTMX; las que quedaron con error se pueden reintentar (solo su autora).
El detalle del error no se muestra aquí: queda en el log y en el admin.

El audio original lo puede escuchar quien ve el curso (`cursos_de`), en `original_captura`.
"""
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import CapturaAudioForm, CapturaTextoForm
from .ia.transcripcion import TIPOS_MIME, formato_audio
from .models import Captura
from .permisos import cursos_de, cursos_donde_registra
from .procesamiento import esta_atascada, reintentar

CAPTURAS_RECIENTES = 5
SEGUNDOS_REFRESCO = 5
EN_CURSO = (Captura.Estado.PENDIENTE, Captura.Estado.PROCESANDO)
MENSAJE_NO_REINTENTABLE = "Solo se pueden reintentar las notas que quedaron con error."


def _es_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _curso(request, curso_id):
    return get_object_or_404(cursos_donde_registra(request.user).select_related("jardin"), pk=curso_id)


def _contexto_recientes(curso, usuario, aviso=""):
    """Últimas capturas de la usuaria en el curso, con cuántas observaciones generó cada una."""
    recientes = list(
        curso.capturas.filter(autora=usuario).annotate(cantidad_observaciones=Count("observaciones"))
        [:CAPTURAS_RECIENTES]
    )
    return {
        "curso": curso,
        "recientes": recientes,
        # Las atascadas en "procesando" no van a cambiar solas: no vale la pena seguir consultando.
        "refrescar": any(c.estado in EN_CURSO and not esta_atascada(c) for c in recientes),
        "segundos_refresco": SEGUNDOS_REFRESCO,
        "aviso": aviso,
    }


@login_required
@require_http_methods(["GET", "POST"])
def capturar(request, curso_id):
    curso = _curso(request, curso_id)
    form = CapturaTextoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        Captura.objects.create(
            curso=curso, autora=request.user, tipo=Captura.Tipo.TEXTO, texto_original=form.cleaned_data["texto"]
        )
        messages.success(request, "Nota guardada. Se separará en observaciones para revisarlas.")
        return redirect("capturar", curso_id=curso.pk)
    contexto = _contexto_recientes(curso, request.user) | {"form": form, "form_audio": CapturaAudioForm()}
    return render(request, "registro/capturar.html", contexto)


@login_required
@require_POST
def capturar_audio(request, curso_id):
    """Guarda un audio dictado (Task 9). `procesar_capturas` lo transcribe y lo separa."""
    curso = _curso(request, curso_id)
    form_audio = CapturaAudioForm(request.POST, request.FILES)
    if form_audio.is_valid():
        Captura.objects.create(
            curso=curso, autora=request.user, tipo=Captura.Tipo.AUDIO, archivo=form_audio.cleaned_data["audio"]
        )
        messages.success(request, "Audio guardado. Se transcribirá y se separará en observaciones para revisarlas.")
        return redirect("capturar", curso_id=curso.pk)
    contexto = _contexto_recientes(curso, request.user) | {"form": CapturaTextoForm(), "form_audio": form_audio}
    return render(request, "registro/capturar.html", contexto)


_RANGO = re.compile(r"^bytes=(\d*)-(\d*)$")


def _rango_pedido(encabezado, tamano):
    """(inicio, fin) de un `Range: bytes=...` simple; None si no hay; "invalido" si no se puede servir."""
    coincide = _RANGO.match((encabezado or "").strip())
    if not coincide or coincide.groups() == ("", ""):
        return None
    inicio, fin = coincide.groups()
    if inicio == "":  # "bytes=-500": los últimos 500 bytes
        inicio, fin = max(tamano - int(fin), 0), tamano - 1
    else:
        inicio, fin = int(inicio), min(int(fin), tamano - 1) if fin else tamano - 1
    if inicio >= tamano or inicio > fin:
        return "invalido"
    return inicio, fin


@login_required
@require_GET
def original_captura(request, captura_id):
    """Audio original de una captura, para quien puede ver el curso.

    Responde rangos de bytes (206) porque Safari no reproduce un <audio> sin ellos.
    """
    captura = get_object_or_404(
        Captura.objects.filter(curso__in=cursos_de(request.user), tipo=Captura.Tipo.AUDIO).exclude(archivo=""),
        pk=captura_id,
    )
    almacen, nombre = captura.archivo.storage, captura.archivo.name
    tamano = almacen.size(nombre)
    with almacen.open(nombre, "rb") as archivo:
        tipo = TIPOS_MIME.get(formato_audio(archivo.read(12)), "application/octet-stream")
    rango = _rango_pedido(request.headers.get("Range"), tamano)
    if rango == "invalido":
        respuesta = HttpResponse(status=416)
        respuesta["Content-Range"] = f"bytes */{tamano}"
    elif rango:
        inicio, fin = rango
        with almacen.open(nombre, "rb") as archivo:
            archivo.seek(inicio)
            respuesta = HttpResponse(archivo.read(fin - inicio + 1), status=206, content_type=tipo)
        respuesta["Content-Range"] = f"bytes {inicio}-{fin}/{tamano}"
    else:
        respuesta = FileResponse(almacen.open(nombre, "rb"), content_type=tipo)
    respuesta["Accept-Ranges"] = "bytes"
    respuesta["Cache-Control"] = "private, max-age=300"
    return respuesta


@login_required
@require_GET
def capturas_recientes(request, curso_id):
    """Parcial de la lista, para el refresco con HTMX."""
    curso = _curso(request, curso_id)
    return render(request, "registro/_capturas_recientes.html", _contexto_recientes(curso, request.user))


@login_required
@require_POST
def reintentar_captura(request, captura_id):
    """Devuelve a pendiente una captura con error. Solo su autora, en un curso donde registra."""
    captura = get_object_or_404(
        Captura.objects.filter(curso__in=cursos_donde_registra(request.user), autora=request.user)
        .select_related("curso"),
        pk=captura_id,
    )
    aviso = "" if reintentar(captura) else MENSAJE_NO_REINTENTABLE
    if _es_htmx(request):
        # 200 y no 4xx: HTMX 2 no reemplaza el contenido con errores HTTP por defecto.
        return render(request, "registro/_capturas_recientes.html", _contexto_recientes(captura.curso, request.user, aviso))
    if aviso:
        messages.error(request, aviso)
    else:
        messages.success(request, "La nota volvió a la cola y se procesará de nuevo.")
    return redirect("capturar", curso_id=captura.curso_id)
