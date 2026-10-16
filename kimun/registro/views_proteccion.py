"""Avisos ante posibles vulneraciones de derechos (PLAN.md, Task 13).

Kimün no detecta ni califica: si al separar una nota Claude la marca, la captura queda en
resguardo (sin observaciones y fuera de toda evaluación) y se crea un `AvisoProteccion`.
Lo ven solo la educadora del curso y la directora del jardín (`avisos_que_ve`); para el
resto, 404. El texto de la nota se muestra tal cual, sin resumirlo ni reescribirlo, y nunca
se escribe en los registros del servidor.

Los pasos del aviso son los del protocolo del jardín, que carga su directora en
`protocolo_jardin`; si no lo ha cargado, los provisorios (ver `registro/protocolo.py`).

Cada aviso se resuelve de una de dos formas, con usuaria y fecha:
- "Informé a la directora / activé el protocolo": la captura sigue en resguardo.
- "No es una vulneración", con un motivo: la captura vuelve a la cola y se procesa como cualquier otra.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import AvisoProteccion, Captura, ProtocoloJardin
from .permisos import avisos_que_ve, jardines_que_dirige
from .protocolo import leer_protocolo, protocolo_para

LARGO_MOTIVO = 500


MAX_PASOS = 20


def _avisos(usuario):
    return avisos_que_ve(usuario).select_related(
        "captura__curso__jardin__protocolo_proteccion__actualizado_por", "captura__autora", "resuelto_por",
    )


def _contexto_aviso(aviso, usuario, **extra):
    jardin = aviso.captura.curso.jardin
    protocolo, referencia = protocolo_para(jardin)
    return {
        "aviso": aviso, "protocolo": protocolo, "referencia": referencia,
        "es_directora": jardin.directora_id == usuario.pk, **extra,
    }


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
    aviso = get_object_or_404(_avisos(request.user), pk=aviso_id)
    return render(request, "registro/aviso.html", _contexto_aviso(aviso, request.user))


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
        return render(request, "registro/aviso.html", _contexto_aviso(
            aviso, request.user, error_motivo="Escribe brevemente por qué no es una vulneración.",
        ), status=400)
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


class ProtocoloJardinForm(forms.ModelForm):
    class Meta:
        model = ProtocoloJardin
        fields = ["nombre_documento", "pasos"]
        labels = {
            "nombre_documento": "Nombre del documento (opcional)",
            "pasos": "Pasos del protocolo, uno por línea",
        }
        widgets = {
            "pasos": forms.Textarea(attrs={"rows": 10, "aria-describedby": "ayuda-pasos", "maxlength": 5000}),
        }
        error_messages = {"pasos": {"required": "Escribe al menos un paso."}}

    def clean_pasos(self):
        pasos = self.cleaned_data["pasos"]
        lista = ProtocoloJardin(pasos=pasos).lista_de_pasos()
        if not lista:
            raise forms.ValidationError("Escribe al menos un paso.")
        if len(lista) > MAX_PASOS:
            raise forms.ValidationError(f"Resume el protocolo en {MAX_PASOS} pasos como máximo.")
        if any(len(p) > 500 for p in lista):
            raise forms.ValidationError("Cada paso puede tener hasta 500 caracteres.")
        return pasos


@login_required
@require_http_methods(["GET", "POST"])
def protocolo_jardin(request, jardin_id):
    """La directora carga o actualiza el protocolo de su jardín. Solo ella; para el resto, 404."""
    jardin = get_object_or_404(jardines_que_dirige(request.user), pk=jardin_id)
    actual = ProtocoloJardin.objects.filter(jardin=jardin).first()
    form = ProtocoloJardinForm(request.POST or None, instance=actual)
    if request.method == "POST" and form.is_valid():
        protocolo = form.save(commit=False)
        protocolo.jardin = jardin
        protocolo.actualizado_por = request.user
        protocolo.save()
        messages.success(request, "Protocolo guardado. Los avisos de protección del jardín mostrarán estos pasos.")
        return redirect("protocolo_jardin", jardin_id=jardin.pk)
    return render(request, "registro/protocolo_jardin.html", {
        "jardin": jardin, "form": form, "actual": actual, "provisorio": leer_protocolo(),
    }, status=400 if form.errors else 200)
