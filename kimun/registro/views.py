"""Vistas de la app. Toda consulta de un curso o niño pasa por `permisos.py`.

La tabla del curso con alertas, distribución y quincena es la Task 2; aquí
solo muestra el nivel actual con su nombre y enlaza a la ficha (Task 3).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .ficha import armar_ficha, descriptores_del_nucleo
from .forms import SEMESTRES_CON_META, FijarNivelForm, MetasForm, etiqueta_nivel, nombres_comunes
from .models import DescriptorNivel, Nucleo, Rubrica, texto_nivel
from .permisos import cursos_de, cursos_que_valida, ninos_de, ninos_que_valida, puede_validar


def _es_htmx(request):
    return request.headers.get("HX-Request") == "true"


@login_required
def inicio(request):
    cursos = cursos_de(request.user).select_related("jardin")
    if len(cursos) == 1:
        return redirect("curso", curso_id=cursos[0].pk)
    return render(request, "registro/inicio.html", {"cursos": cursos})


@login_required
def curso(request, curso_id):
    curso = get_object_or_404(cursos_de(request.user).select_related("jardin"), pk=curso_id)
    nucleos = list(Nucleo.objects.all())
    nombres = DescriptorNivel.nombres_por_nucleo(curso.nivel_educativo)
    filas = []
    for nino in curso.ninos.all():
        actuales = nino.niveles_actuales()
        niveles = []
        for n in nucleos:
            nv = actuales.get(n.sigla)
            niveles.append(texto_nivel(nv.nivel, nombres.get(n.sigla, {}).get(nv.nivel, "")) if nv else None)
        filas.append({"nino": nino, "niveles": niveles})
    contexto = {
        "curso": curso, "nucleos": nucleos, "filas": filas,
        "puede_validar": puede_validar(request.user, curso),
    }
    return render(request, "registro/curso.html", contexto)


def _pagina_ficha(request, nino, formularios=None):
    ficha = armar_ficha(nino, request.user, formularios=formularios)
    return render(request, "registro/ficha.html", {"ficha": ficha, "curso": nino.curso})


def _parcial_nucleo(request, nino, sigla, mensaje="", formularios=None):
    ficha = armar_ficha(nino, request.user, formularios=formularios)
    contexto = {"nf": ficha.nucleo(sigla), "ficha": ficha, "mensaje": mensaje}
    return render(request, "registro/_nucleo_ficha.html", contexto)


@login_required
def ficha(request, nino_id):
    nino = get_object_or_404(ninos_de(request.user).select_related("curso__jardin"), pk=nino_id)
    return _pagina_ficha(request, nino)


@login_required
@require_POST
def fijar_nivel(request, nino_id, sigla):
    nino = get_object_or_404(ninos_que_valida(request.user).select_related("curso__jardin"), pk=nino_id)
    nucleo = get_object_or_404(Nucleo, sigla=sigla)
    nivel_educativo = nino.curso.nivel_educativo
    descriptores = descriptores_del_nucleo(nivel_educativo, nucleo)
    form = FijarNivelForm(
        request.POST, prefix=nucleo.sigla,
        nivel_maximo=Rubrica.nivel_maximo(nivel_educativo), descriptores=descriptores,
    )
    guardado = None
    if form.is_valid():
        guardado = form.guardar(nino, nucleo, request.user, timezone.localdate())

    if guardado is None:
        if _es_htmx(request):
            # 200 y no 4xx: HTMX 2 no reemplaza el contenido con errores HTTP por defecto.
            return _parcial_nucleo(request, nino, nucleo.sigla, formularios={nucleo.sigla: form})
        return _pagina_ficha(request, nino, formularios={nucleo.sigla: form})

    mensaje = f"Nivel guardado: {etiqueta_nivel(guardado.nivel, descriptores.get(guardado.nivel))}."
    if _es_htmx(request):
        return _parcial_nucleo(request, nino, nucleo.sigla, mensaje=mensaje)
    messages.success(request, mensaje)
    return redirect(f"{reverse('ficha', args=[nino.pk])}#nucleo-{nucleo.sigla}")


@login_required
@require_http_methods(["GET", "POST"])
def metas(request, curso_id):
    curso = get_object_or_404(cursos_que_valida(request.user).select_related("jardin"), pk=curso_id)
    nivel_educativo = curso.nivel_educativo
    nivel_maximo = Rubrica.nivel_maximo(nivel_educativo)
    nombres = nombres_comunes(DescriptorNivel.nombres_por_nucleo(nivel_educativo))
    opciones = {"curso": curso, "nivel_maximo": nivel_maximo, "nombres": nombres}
    if request.method == "POST":
        form = MetasForm(request.POST, **opciones)
        if form.is_valid() and form.guardar() is not None:
            messages.success(request, "Metas guardadas.")
            return redirect("curso", curso_id=curso.pk)
    else:
        form = MetasForm(**opciones)
    contexto = {
        "curso": curso, "form": form,
        "texto_maximo": texto_nivel(nivel_maximo, nombres.get(nivel_maximo, "")),
        "semestre_siguiente": SEMESTRES_CON_META + 1,
    }
    return render(request, "registro/metas.html", contexto)
