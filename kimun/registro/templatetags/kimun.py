"""Etiquetas de plantilla de la interfaz: avatar, edad y menú lateral (diseno-interfaz.jpg).

    {% load kimun %}
    {{ nino.nombre|iniciales }}  {{ nino.nombre|color_avatar }}  {{ nino|edad }}
    {% menu_lateral %}
"""
from django import template
from django.utils import timezone

from ..alertas import TablaCurso, tabla_del_curso
from ..pantallas import para_tener_presentes, texto_edad
from ..permisos import cursos_de, cursos_donde_registra, puede_validar

register = template.Library()

# Fondos suaves para el avatar, todos con contraste de al menos 7:1 con el texto oscuro (#14313d).
PALETA_AVATAR = ("#cdeefb", "#ffe3b0", "#d3f0dc", "#f8d9e6", "#e2dbf7", "#ffdccc", "#e8f1c4")


@register.filter
def iniciales(nombre):
    """'Sofía Rojas' -> 'SR'."""
    partes = (nombre or "").split()
    return "".join(p[0] for p in partes[:2]).upper()


@register.filter
def color_avatar(nombre):
    """Un color de PALETA_AVATAR que depende solo del nombre, para que cada niño tenga siempre el mismo."""
    return PALETA_AVATAR[sum(ord(c) for c in nombre or "") % len(PALETA_AVATAR)]


@register.filter
def edad(nino):
    return texto_edad(getattr(nino, "fecha_nacimiento", None), timezone.localdate())


@register.inclusion_tag("registro/_menu_lateral.html", takes_context=True)
def menu_lateral(context):
    """Menú lateral (pantalla III): el curso, los niños para tener presentes y la lista con buscador.

    Usa el `curso` de la página. Si la página no tiene uno y la usuaria ve un solo
    curso, usa ese; si ve varios, muestra la lista de cursos. Reutiliza la `tabla`
    de la vista del curso cuando está, para no calcularla dos veces.
    """
    request = context["request"]
    usuario = request.user
    curso = context.get("curso")
    datos = {
        "request": request,
        "user": usuario,
        "csrf_token": context.get("csrf_token"),
        "cursos_por_revisar": context.get("cursos_por_revisar", []),
    }
    if curso is None:
        visibles = list(cursos_de(usuario).select_related("jardin")[:2])
        if len(visibles) != 1:
            datos["cursos"] = cursos_de(usuario).select_related("jardin")
            return datos
        curso = visibles[0]
    tabla = context.get("tabla")
    if not isinstance(tabla, TablaCurso):
        tabla = tabla_del_curso(curso)
    datos.update(
        curso=curso,
        ninos=[fila.nino for fila in tabla.filas],
        presentes=para_tener_presentes(tabla),
        puede_validar=puede_validar(usuario, curso),
        puede_registrar=cursos_donde_registra(usuario).filter(pk=curso.pk).exists(),
    )
    return datos
