"""Pantallas I y II del boceto (diseno-interfaz.jpg): registrar un suceso y ver cómo quedó ordenado.

- `registrar`: "¿Qué quieres registrar?". La educadora y las asistentes del
  curso escriben, adjuntan una foto o graban un audio (`cursos_donde_registra`).
- `captura`: la nota como burbuja y, debajo, una tarjeta por niño. La ven
  quienes ven el curso (`cursos_de`); solo la educadora acepta, edita o
  descarta (con las vistas de `views_revision.py`).
- `procesar`: la página de la captura lo llama con HTMX al abrirse y espera
  ahí el resultado de Bedrock. `manage.py procesar_capturas` hace lo mismo en
  segundo plano; `procesamiento.tomar` evita que los dos procesen la misma.
- `views_captura.capturar` (Task 5) sigue disponible como formulario solo de texto.

Un curso o una captura ajenos responden 404, como en el resto de la app.
"""
import os

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import procesamiento
from .forms_registro import RegistroForm
from .ia import ClienteBedrock
from .models import Captura, Observacion
from .pantallas import ninos_mencionados, observaciones_para_tarjetas, tarjetas_suceso
from .permisos import cursos_de, cursos_donde_registra, puede_validar
from .views_captura import respuesta_audio

RECIENTES = 3
# Errores que indican que este servidor no está conectado a Bedrock (no un problema de la nota).
PISTAS_SIN_CONEXION = (
    "Unable to locate credentials", "No module named 'boto3'", "ExpiredToken", "security token",
    "AccessDenied", "Could not connect to the endpoint",
)
TIPOS_MIME = {
    ".jpg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
    ".webm": "audio/webm", ".ogg": "audio/ogg", ".m4a": "audio/mp4", ".wav": "audio/wav", ".mp3": "audio/mpeg",
}


def _es_htmx(request):
    return request.headers.get("HX-Request") == "true"


def crear_cliente():
    """Cliente de Bedrock real. Los tests lo reemplazan por uno falso."""
    return ClienteBedrock()


def _recientes(curso, usuario):
    """Las últimas capturas del curso: todas para la educadora, las propias para una asistente."""
    qs = Captura.objects.filter(curso=curso).select_related("autora")
    if not puede_validar(usuario, curso):
        qs = qs.filter(autora=usuario)
    return list(qs.order_by("-creada", "-id")[:RECIENTES])


@login_required
@require_http_methods(["GET", "POST"])
def registrar(request, curso_id):
    curso = get_object_or_404(cursos_donde_registra(request.user).select_related("jardin"), pk=curso_id)
    form = RegistroForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        captura = form.guardar(curso, request.user)
        return redirect("captura", captura_id=captura.pk)
    return render(request, "registro/registrar.html", {
        "curso": curso,
        "form": form,
        "recientes": _recientes(curso, request.user),
    }, status=400 if form.errors else 200)


def _contexto_captura(request, captura):
    curso = captura.curso
    observaciones = observaciones_para_tarjetas(
        captura.observaciones.exclude(estado=Observacion.Estado.DESCARTADA)
    ).order_by("grupal", "nino__nombre", "fecha", "id")
    tarjetas = tarjetas_suceso(observaciones, timezone.localdate())
    return {
        "captura": captura,
        "curso": curso,
        "tarjetas": [t for t in tarjetas if not t.obs.grupal],
        "grupales": [t for t in tarjetas if t.obs.grupal],
        "puede_validar": puede_validar(request.user, curso),
        "puede_registrar": cursos_donde_registra(request.user).filter(pk=curso.pk).exists(),
        "ninos": list(curso.ninos.all()),
        "vista": "suceso",
        "atascada": procesamiento.esta_atascada(captura),
        "sin_conexion_ia": captura.estado == Captura.Estado.ERROR and any(
            pista in captura.error for pista in PISTAS_SIN_CONEXION
        ),
        # Mientras no hay tarjetas (procesando, error o audio), se muestran igual los niños nombrados.
        "mencionados": [] if captura.estado == Captura.Estado.PROCESADA else ninos_mencionados(
            f"{captura.texto_original} {captura.texto_extraido}", curso.ninos.all(), timezone.localdate()
        ),
    }


def _captura(usuario, captura_id, cursos):
    return get_object_or_404(
        Captura.objects.filter(curso__in=cursos(usuario)).select_related("curso__jardin", "autora"), pk=captura_id
    )


@login_required
@require_GET
def captura(request, captura_id):
    captura = _captura(request.user, captura_id, cursos_de)
    contexto = _contexto_captura(request, captura)
    contexto["form"] = RegistroForm()
    return render(request, "registro/captura.html", contexto)


@login_required
@require_POST
def procesar(request, captura_id):
    """Procesa la captura si está pendiente y devuelve su estado (HTMX) o vuelve a la página."""
    captura = _captura(request.user, captura_id, cursos_donde_registra)
    procesada_aqui = procesamiento.procesar_si_pendiente(captura, cliente=crear_cliente())
    if not _es_htmx(request):
        return redirect("captura", captura_id=captura.pk)
    captura.refresh_from_db()
    contexto = _contexto_captura(request, captura)
    # Si otro proceso la está ordenando, la página vuelve a preguntar en unos segundos.
    contexto["esperar"] = not procesada_aqui
    contexto["oob"] = True
    return render(request, "registro/_estado_captura.html", contexto)


@login_required
@require_POST
def reintentar(request, captura_id):
    captura = _captura(request.user, captura_id, cursos_donde_registra)
    procesamiento.reintentar_desde_la_pagina(captura)
    captura.refresh_from_db()
    if not _es_htmx(request):
        return redirect("captura", captura_id=captura.pk)
    return render(request, "registro/_estado_captura.html", _contexto_captura(request, captura))


@login_required
@require_GET
def original(request, captura_id):
    """La foto o el audio original, después de revisar que la usuaria ve el curso.

    En desarrollo se sirve desde el disco. Con S3 (Task 8) se reemplaza por una
    URL prefirmada de 5 minutos.
    """
    captura = _captura(request.user, captura_id, cursos_de)
    if not captura.archivo:
        raise Http404("La captura no tiene archivo.")
    if captura.tipo == Captura.Tipo.AUDIO:
        # Con rangos de bytes (206): Safari no reproduce un <audio> sin ellos.
        return respuesta_audio(request, captura)
    extension = os.path.splitext(captura.archivo.name)[1].lower()
    respuesta = FileResponse(captura.archivo.open("rb"), content_type=TIPOS_MIME.get(extension, "application/octet-stream"))
    respuesta["Content-Disposition"] = "inline"
    respuesta["Cache-Control"] = "private, max-age=300"
    return respuesta
