"""Etiquetas de plantilla de la interfaz: avatar, edad y menú lateral (diseno-interfaz.jpg).

    {% load kimun %}
    {{ nino.nombre|iniciales }}  {{ nino.nombre|color_avatar }}  {{ nino|edad }}  {{ nucleo.sigla|icono_nucleo }}
    {% menu_lateral %}
"""
from dataclasses import dataclass

from django import template
from django.urls import reverse
from django.utils import timezone

from ..alertas import TablaCurso, tabla_del_curso
from ..frecuencia import FrecuenciaCurso, frecuencia_del_curso
from ..iconos import icono_nucleo
from ..models import NivelEducativo, PropuestaNivel
from ..pantallas import para_tener_presentes, texto_edad
from ..permisos import (
    cursos_con_lista_editable, cursos_de, cursos_donde_registra, cursos_que_valida, jardines_que_dirige,
    puede_editar_lista, puede_validar,
)

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


@register.filter(name="icono_nucleo")
def filtro_icono_nucleo(sigla):
    """URL del icono del núcleo ("" si no tiene). Se usa como máscara: ver `registro/iconos.py`."""
    return icono_nucleo(sigla)


@dataclass(frozen=True)
class SalaDelSelector:
    curso: object
    url: str
    actual: bool


# Secciones de una sala que existen en todas: al cambiar de sala se queda en la misma, si la
# usuaria puede verla en la otra; si no (o si está en la ficha de un niño), va a la tabla de la sala.
_SECCIONES = {
    "registrar": cursos_donde_registra,
    "revision": cursos_que_valida,
    "metas": cursos_que_valida,
    "ninos_sala": cursos_con_lista_editable,
    "curso": cursos_de,
}


def _ordenadas(cursos):
    """Por jardín, nivel educativo (sala cuna, medio, transición) y nombre."""
    orden = [valor for valor, _ in NivelEducativo.choices]
    return sorted(cursos, key=lambda c: (
        c.jardin.nombre, orden.index(c.nivel_educativo) if c.nivel_educativo in orden else len(orden), c.nombre,
    ))


def salas_del_selector(usuario, curso, resolver_match=None):
    """[SalaDelSelector] con las salas que ve la usuaria: la educadora y las asistentes, las suyas;
    la directora, todas las de su jardín. Ordenadas por jardín, nivel educativo y nombre."""
    salas = _ordenadas(cursos_de(usuario).select_related("jardin"))
    seccion = getattr(resolver_match, "url_name", None)
    permitidas = set(_SECCIONES[seccion](usuario).values_list("pk", flat=True)) if seccion in _SECCIONES else set()
    return [
        SalaDelSelector(c, reverse(seccion if c.pk in permitidas else "curso", args=[c.pk]), c.pk == curso.pk)
        for c in salas
    ]


@register.inclusion_tag("registro/_menu_lateral.html", takes_context=True)
def menu_lateral(context):
    """Menú lateral (pantalla III): el curso, los niños para tener presentes y la lista con buscador.

    Usa el `curso` de la página. Si la página no tiene uno y la usuaria ve un solo
    curso, usa ese; si ve varios, muestra la lista de cursos. Reutiliza la `tabla`
    y la `frecuencia` de la vista del curso cuando están, para no calcularlas dos
    veces. Las muchas observaciones pendientes solo se muestran a quien revisa.
    """
    request = context["request"]
    usuario = request.user
    curso = context.get("curso")
    datos = {
        "request": request,
        "user": usuario,
        "csrf_token": context.get("csrf_token"),
        "cursos_por_revisar": context.get("cursos_por_revisar", []),
        "jardines": list(jardines_que_dirige(usuario)),
    }
    if curso is None:
        visibles = _ordenadas(cursos_de(usuario).select_related("jardin"))
        if len(visibles) != 1:
            datos["cursos"] = visibles
            # El nombre del jardín solo hace falta si las salas son de más de uno.
            datos["varios_jardines"] = len({c.jardin_id for c in visibles}) > 1
            return datos
        curso = visibles[0]
    tabla = context.get("tabla")
    if not isinstance(tabla, TablaCurso):
        tabla = tabla_del_curso(curso)
    frecuencia = context.get("frecuencia")
    if not isinstance(frecuencia, FrecuenciaCurso):
        frecuencia = frecuencia_del_curso(curso, hoy=tabla.hoy, ninos=[fila.nino for fila in tabla.filas])
    valida = puede_validar(usuario, curso)
    datos.update(
        curso=curso,
        ninos=[fila.nino for fila in tabla.filas],
        presentes=para_tener_presentes(tabla, frecuencia, ver_pendientes=valida),
        puede_validar=valida,
        puede_registrar=cursos_donde_registra(usuario).filter(pk=curso.pk).exists(),
        puede_editar_lista=puede_editar_lista(usuario, curso),
        # Selector de sala, arriba del menú: las salas que ve, cada una en la misma sección si se puede.
        salas=salas_del_selector(usuario, curso, getattr(request, "resolver_match", None)),
        # Solo la educadora decide niveles: la bandeja está en la vista del curso.
        propuestas_por_decidir=PropuestaNivel.objects.filter(
            nino__curso=curso, estado=PropuestaNivel.Estado.LISTA,
        ).count() if valida else 0,
    )
    return datos
