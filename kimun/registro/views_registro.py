"""Pantallas I y II del boceto (diseno-interfaz.jpg): registrar un suceso y ver cómo quedó ordenado.

- `registrar`: "¿Qué quieres registrar?". La educadora y las asistentes del
  curso escriben, adjuntan una foto o graban un audio (`cursos_donde_registra`).
- `captura`: la nota como burbuja y, debajo, una tarjeta por niño. La ven
  quienes ven el curso (`cursos_de`); solo la educadora acepta, edita o
  descarta (con las vistas de `views_revision.py`).
- `estado`: la página de la captura lo consulta con HTMX cada pocos segundos
  hasta que `manage.py procesar_capturas`, en segundo plano, la deja ordenada.
  La petición web nunca llama a Bedrock.
- `views_captura.capturar` (Task 5) sigue disponible como formulario solo de texto.

Un curso o una captura ajenos responden 404, como en el resto de la app.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import procesamiento
from .forms_registro import RegistroForm
from .models import Captura, Observacion
from .pantallas import ninos_mencionados, observaciones_para_tarjetas, resumen_captura, tarjetas_suceso
from .permisos import avisos_que_ve, cursos_de, cursos_donde_registra, puede_validar

RECIENTES = 3
LARGO_CONTEXTO = 1000
# Errores que indican que este servidor no está conectado a Bedrock (no un problema de la nota).
PISTAS_SIN_CONEXION = (
    "Unable to locate credentials", "No module named 'boto3'", "ExpiredToken", "security token",
    "AccessDenied", "Could not connect to the endpoint",
)


def _es_htmx(request):
    return request.headers.get("HX-Request") == "true"


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
    form = RegistroForm(request.POST if request.method == "POST" else None, request.FILES or None)
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
    del_curso = [t for t in tarjetas if t.obs.nombre_detectado == procesamiento.NOMBRE_TODO_EL_CURSO and not t.obs.grupal]
    individuales = [t for t in tarjetas if not t.obs.grupal and t not in del_curso]
    grupales = [t for t in tarjetas if t.obs.grupal]
    return {
        "captura": captura,
        "curso": curso,
        "tarjetas": individuales,
        # Lo que hizo todo el curso: una observación por niño, que se muestra junta en una sola tarjeta.
        "del_curso": del_curso,
        "del_curso_pendientes": sum(1 for t in del_curso if t.obs.estado == Observacion.Estado.PENDIENTE),
        "grupales": grupales,
        # "De esta nota saqué…": a quién corresponde cada observación y en qué núcleos, con enlaces a las tarjetas.
        "resumen": resumen_captura(individuales, del_curso, grupales),
        # La revisión agrupa por captura solo las observaciones individuales (incluidas las de todo el curso).
        "hay_pendientes": any(t.obs.estado == Observacion.Estado.PENDIENTE for t in tarjetas if not t.obs.grupal),
        "puede_agregar_contexto": puede_agregar_contexto(captura),
        "puede_validar": puede_validar(request.user, curso),
        "puede_registrar": cursos_donde_registra(request.user).filter(pk=curso.pk).exists(),
        "ninos": list(curso.ninos.all()),
        "vista": "suceso",
        "atascada": procesamiento.esta_atascada(captura),
        "sin_conexion_ia": captura.estado == Captura.Estado.ERROR and any(
            pista in captura.error for pista in PISTAS_SIN_CONEXION
        ),
        # Posible vulneración (Task 13): el texto y el aviso solo los ven la educadora y la directora.
        "en_resguardo": captura.estado == Captura.Estado.EN_RESGUARDO,
        "aviso_visible": (
            avisos_que_ve(request.user).filter(captura=captura).first()
            if captura.estado == Captura.Estado.EN_RESGUARDO else None
        ),
        # Mientras no hay tarjetas (procesando, error o audio), se muestran igual los niños nombrados.
        "mencionados": [] if captura.estado in (Captura.Estado.PROCESADA, Captura.Estado.EN_RESGUARDO) else ninos_mencionados(
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
@require_GET
def estado(request, captura_id):
    """Estado de la captura para la página, que lo consulta cada pocos segundos (HTMX) mientras se ordena.

    No llama a Bedrock: eso lo hace `procesar_capturas` en segundo plano. Leer una foto
    y separarla puede tardar más que los timeouts de CloudFront (30 s) y Gunicorn (60 s).
    """
    captura = _captura(request.user, captura_id, cursos_de)
    if not _es_htmx(request):
        return redirect("captura", captura_id=captura.pk)
    contexto = _contexto_captura(request, captura)
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


def puede_agregar_contexto(captura):
    """Se puede responder la pregunta de Claude mientras ninguna observación de la captura se aceptó."""
    return captura.estado == Captura.Estado.PROCESADA and not captura.observaciones.filter(
        estado=Observacion.Estado.ACEPTADA
    ).exists()


@login_required
@require_POST
def agregar_contexto(request, captura_id):
    """Responde la pregunta de Claude: suma el contexto a la nota y la vuelve a ordenar.

    Las observaciones pendientes de la captura se reemplazan por las nuevas. Si alguna
    ya se aceptó, no se toca nada: el contexto se registra como una nota nueva.
    """
    captura = _captura(request.user, captura_id, cursos_donde_registra)
    contexto = " ".join((request.POST.get("contexto") or "").split())[:LARGO_CONTEXTO]
    if not contexto:
        messages.error(request, "Escribe el contexto que falta antes de enviarlo.")
    elif not puede_agregar_contexto(captura):
        messages.error(request, "Esta nota ya tiene observaciones aceptadas: registra el contexto como una nota nueva.")
    else:
        with transaction.atomic():
            captura.observaciones.filter(estado=Observacion.Estado.PENDIENTE).delete()
            captura.texto_original = f"{captura.texto_original}\n\nContexto agregado: {contexto}".strip()
            captura.pregunta = ""
            captura.estado = Captura.Estado.PENDIENTE
            captura.save(update_fields=["texto_original", "pregunta", "estado", "actualizada"])
    return redirect("captura", captura_id=captura.pk)
