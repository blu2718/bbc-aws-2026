"""Avisos ante posibles vulneraciones de derechos (PLAN.md, Task 13).

Kimün no detecta ni califica: si al separar una nota Claude la marca, la captura queda en
resguardo (sin observaciones y fuera de toda evaluación) y se crea un `AvisoProteccion`.
Lo ven solo la educadora del curso y la directora del jardín (`avisos_que_ve`); para el
resto, 404. El texto de la nota se muestra tal cual, sin resumirlo ni reescribirlo, y nunca
se escribe en los registros del servidor.

Cada aviso se resuelve de una de dos formas, con usuaria y fecha:
- "Informé a la directora / activé el protocolo": la captura sigue en resguardo.
- "No es una vulneración", con un motivo: la captura vuelve a la cola y se procesa como cualquier otra.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import AvisoProteccion, Captura
from .permisos import avisos_que_ve

LARGO_MOTIVO = 500


def _avisos(usuario):
    return avisos_que_ve(usuario).select_related("captura__curso__jardin", "captura__autora", "resuelto_por")


@login_required
@require_GET
def avisos(request):
    lista = list(_avisos(request.user))
    return render(request, "registro/avisos.html", {
        "pendientes": [a for a in lista if a.estado == AvisoProteccion.Estado.PENDIENTE],
        "resueltos": [a for a in lista if a.estado != AvisoProteccion.Estado.PENDIENTE][:20],
    })


@login_required
@require_GET
def aviso(request, aviso_id):
    return render(request, "registro/aviso.html", {"aviso": get_object_or_404(_avisos(request.user), pk=aviso_id)})


@login_required
@require_POST
def resolver_aviso(request, aviso_id):
    aviso = get_object_or_404(_avisos(request.user), pk=aviso_id)
    accion = request.POST.get("accion")
    motivo = (request.POST.get("motivo") or "").strip()[:LARGO_MOTIVO]
    if aviso.estado != AvisoProteccion.Estado.PENDIENTE:
        messages.error(request, "Este aviso ya se resolvió.")
        return redirect("aviso", aviso_id=aviso.pk)
    if accion == "no_es" and not motivo:
        return render(request, "registro/aviso.html", {
            "aviso": aviso, "error_motivo": "Escribe brevemente por qué no es una vulneración.",
        }, status=400)
    if accion not in ("protocolo", "no_es"):
        return redirect("aviso", aviso_id=aviso.pk)

    with transaction.atomic():
        aviso.estado = AvisoProteccion.Estado.PROTOCOLO if accion == "protocolo" else AvisoProteccion.Estado.NO_ES
        aviso.motivo = motivo if accion == "no_es" else ""
        aviso.resuelto_por = request.user
        aviso.resuelto_en = timezone.now()
        aviso.save(update_fields=["estado", "motivo", "resuelto_por", "resuelto_en"])
        if accion == "no_es":
            # Vuelve a la cola: procesar_capturas la separa como cualquier otra y ya no la marca.
            Captura.objects.filter(pk=aviso.captura_id, estado=Captura.Estado.EN_RESGUARDO).update(
                estado=Captura.Estado.PENDIENTE, actualizada=timezone.now()
            )
    if accion == "protocolo":
        messages.success(request, "Quedó registrado. La nota sigue en resguardo y fuera de la evaluación.")
    else:
        messages.success(request, "Quedó registrado. La nota se ordenará como cualquier otra.")
    return redirect("avisos")
