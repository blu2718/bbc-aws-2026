from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .alertas import DIAS_DATOS_RECIENTES, tabla_del_curso
from .cobertura import cobertura_quincena_del_curso, quincena_de
from .permisos import cursos_de


@login_required
def inicio(request):
    cursos = cursos_de(request.user).select_related("jardin")
    if len(cursos) == 1:
        return redirect("curso", curso_id=cursos[0].pk)
    return render(request, "registro/inicio.html", {"cursos": cursos})


def _quincena_pedida(valor, hoy):
    """La quincena de `?quincena=AAAA-MM-DD`, o la actual si falta, no es válida o es futura."""
    actual = quincena_de(hoy)
    try:
        pedida = quincena_de(date.fromisoformat(valor or ""))
    except ValueError:
        return actual
    return pedida if pedida.inicio <= actual.inicio else actual


@login_required
def curso(request, curso_id):
    """Tabla del curso por núcleo: nivel actual, comparación con pares, nivel esperado y alertas (Task 2)."""
    curso = get_object_or_404(cursos_de(request.user).select_related("jardin"), pk=curso_id)
    hoy = timezone.localdate()
    tabla = tabla_del_curso(curso, hoy=hoy)
    quincena = _quincena_pedida(request.GET.get("quincena"), hoy)
    actual = quincena_de(hoy)
    cobertura = cobertura_quincena_del_curso(curso, quincena, nucleos=tabla.nucleos)
    return render(request, "registro/curso.html", {
        "curso": curso,
        "tabla": tabla,
        "quincena": quincena,
        "es_quincena_actual": quincena == actual,
        "quincena_anterior": quincena.anterior(),
        "quincena_siguiente": None if quincena == actual else quincena.siguiente(),
        "cobertura_quincena": cobertura,
        "nucleos_sin_observaciones": [c.nucleo for c in cobertura if c.sin_observaciones],
        "dias_datos_recientes": DIAS_DATOS_RECIENTES,
    })
