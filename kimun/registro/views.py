"""Vistas de la app. Toda consulta de un curso o niño pasa por `permisos.py`.

- `curso`: tabla del curso con nivel esperado, brechas, distribución y quincena (Task 2).
- `ficha`, `fijar_nivel` y `metas`: ficha del niño, validación manual y tabla de metas (Task 3).
  La ficha es también el perfil de la pantalla IV de diseno-interfaz.jpg.
- `inicio` lleva a "¿Qué quieres registrar?", que está en `views_registro.py` con la captura.
- La revisión de observaciones (Task 6) está en `views_revision.py`.
"""
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .alertas import DIAS_DATOS_RECIENTES, tabla_del_curso
from .cobertura import cobertura_quincena_del_curso, quincena_de
from .ficha import armar_ficha, descriptores_del_nucleo
from .forms import SEMESTRES_CON_META, FijarNivelForm, MetasForm, etiqueta_nivel, nombres_comunes
from .models import DescriptorNivel, Nucleo, Rubrica, texto_nivel
from .permisos import (
    cursos_de,
    cursos_donde_registra,
    cursos_que_valida,
    ninos_de,
    ninos_que_valida,
    puede_validar,
)
from .pantallas import historial_del_nino, texto_edad
from .radar import radar_de_la_ficha
from .revision import resumen_pendientes


def _es_htmx(request):
    return request.headers.get("HX-Request") == "true"


@login_required
def inicio(request):
    """La pestaña de inicio es "¿Qué quieres registrar?" (diseno-interfaz.jpg, pantalla I).

    Quien registra en un solo curso (la educadora o una asistente) va directo
    ahí. Quien solo ve cursos (la directora) va a la tabla, si es uno solo.
    """
    registra = list(cursos_donde_registra(request.user))
    if len(registra) == 1:
        return redirect("registrar", curso_id=registra[0].pk)
    cursos = cursos_de(request.user).select_related("jardin")
    if not registra and len(cursos) == 1:
        return redirect("curso", curso_id=cursos[0].pk)
    return render(request, "registro/inicio.html", {"cursos": cursos, "registra": {c.pk for c in registra}})


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
    valida = puede_validar(request.user, curso)
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
        "puede_validar": valida,
        "puede_registrar": cursos_donde_registra(request.user).filter(pk=curso.pk).exists(),
        "pendientes_por_revisar": resumen_pendientes(curso)["individuales"] if valida else 0,
    })


def _pagina_ficha(request, nino, formularios=None, formularios_propuesta=None, errores_propuesta=None):
    """Perfil del niño (diseno-interfaz.jpg, pantalla IV): gráfico por núcleo, historial y detalle por núcleo."""
    hoy = timezone.localdate()
    ficha = armar_ficha(nino, request.user, hoy=hoy, formularios=formularios,
                        formularios_propuesta=formularios_propuesta, errores_propuesta=errores_propuesta)
    radar, esperado = radar_de_la_ficha(ficha, Rubrica.nivel_maximo(nino.curso.nivel_educativo))
    return render(request, "registro/ficha.html", {
        "ficha": ficha,
        "curso": nino.curso,
        "edad": texto_edad(nino.fecha_nacimiento, hoy),
        "radar": radar,
        "esperado": esperado,
        "historial": historial_del_nino(nino),
        "puede_registrar": cursos_donde_registra(request.user).filter(pk=nino.curso_id).exists(),
    })


def _parcial_nucleo(request, nino, sigla, mensaje="", formularios=None, formularios_propuesta=None, error_propuesta=""):
    ficha = armar_ficha(nino, request.user, formularios=formularios, formularios_propuesta=formularios_propuesta,
                        errores_propuesta={sigla: error_propuesta})
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
