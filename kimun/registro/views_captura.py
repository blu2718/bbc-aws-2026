"""Registro de notas escritas (PLAN.md, Task 5).

Registran la educadora, las asistentes del curso y la directora del jardín
(`cursos_donde_registra`). Una educadora de otro curso o la directora de otro
jardín reciben 404. La revisión sigue siendo solo de la educadora del curso. La nota queda pendiente y
`manage.py procesar_capturas` la separa en observaciones para la revisión.

Debajo del formulario va la lista de las últimas capturas de la usuaria en el curso,
con su estado. Mientras alguna esté pendiente o procesando (y no atascada), la lista se
refresca sola con HTMX; las que quedaron con error se pueden reintentar (solo su autora).
El detalle del error no se muestra aquí: queda en el log y en el admin.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import CapturaTextoForm
from .models import Captura
from .permisos import cursos_donde_registra
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
    contexto = _contexto_recientes(curso, request.user) | {"form": form}
    return render(request, "registro/capturar.html", contexto)


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
