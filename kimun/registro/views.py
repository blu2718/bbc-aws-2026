"""Vistas mínimas del esqueleto. La tabla del curso con alertas es la Task 2."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Nucleo
from .permisos import cursos_de


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
    filas = []
    for nino in curso.ninos.all():
        actuales = nino.niveles_actuales()
        filas.append({"nino": nino, "niveles": [actuales.get(n.sigla) for n in nucleos]})
    return render(request, "registro/curso.html", {"curso": curso, "nucleos": nucleos, "filas": filas})
