"""Gráfico de la evolución de los niveles validados (PLAN.md, Task 3).

Un SVG simple por núcleo, generado en el servidor y sin librerías nuevas. La
ficha lo acompaña con una tabla equivalente (`registro/_evolucion.html`), por
accesibilidad.

El nivel se dibuja en escalones: se mantiene desde que se valida hasta la
validación siguiente, porque solo la educadora lo cambia. El eje vertical va
de 1 al máximo de la rúbrica (hoy 8, podría ser 9); no asume una cantidad.

`puntos_evolucion` y `svg_evolucion` son puras. `evolucion_del_nino` es la
única que consulta la base.
"""
from dataclasses import dataclass
from datetime import date

from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .models import NIVEL_MIN, DescriptorNivel, NivelValidado, Nucleo, Rubrica, texto_nivel

# Medidas en unidades del viewBox. El SVG se escala al ancho disponible, hasta
# ANCHO_MAXIMO. El ancho se eligió cerca del de un teléfono, para que ahí una
# unidad sea más o menos un píxel y las etiquetas se lean a 12 px.
ANCHO, ALTO = 300, 170
MARGEN_IZQ, MARGEN_DER, MARGEN_SUP, MARGEN_INF = 24, 10, 10, 26
TAMANO_LETRA = 12
ANCHO_MAXIMO = "28rem"
FORMATO_FECHA = "%d-%m-%Y"


@dataclass(frozen=True)
class Punto:
    fecha: date
    nivel: int
    comentario: str = ""
    nombre: str = ""  # nombre del nivel en la rúbrica, por ejemplo "Desarrollando"

    @property
    def texto(self):
        """Cómo se muestra el nivel: "3 · Desarrollando", o "3" si no tiene nombre."""
        return texto_nivel(self.nivel, self.nombre)


@dataclass(frozen=True)
class Evolucion:
    """Evolución de un núcleo: los puntos para la tabla y el SVG para el gráfico."""

    nucleo: Nucleo
    puntos: list
    svg: str

    @property
    def actual(self):
        return self.puntos[-1] if self.puntos else None


def puntos_evolucion(niveles, nombres=None):
    """[Punto] en orden de fecha, con un solo punto por día.

    - niveles: objetos con `fecha`, `nivel` y, si hay, `comentario` (por
      ejemplo NivelValidado), en el orden en que se registraron. Si hay varios
      el mismo día, vale el último registrado, igual que en `Nino.nivel_actual`.
    - nombres: {nivel: nombre del nivel} de la rúbrica del núcleo, si existe.
    """
    nombres = nombres or {}
    por_dia = {}
    for n in sorted(niveles, key=lambda n: n.fecha):  # sorted es estable
        por_dia[n.fecha] = Punto(n.fecha, n.nivel, getattr(n, "comentario", "") or "", nombres.get(n.nivel, ""))
    return list(por_dia.values())


def _fecha(f):
    return f.strftime(FORMATO_FECHA)


def _texto(x, y, contenido, clase, anclaje="start"):
    return (
        f'<text class="{clase}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anclaje}" '
        f'font-size="{TAMANO_LETRA}" fill="currentColor">{escape(contenido)}</text>'
    )


def svg_evolucion(puntos, nivel_maximo, hasta=None, etiqueta=""):
    """SVG con la evolución de un núcleo, listo para insertar en la plantilla.

    - puntos: [Punto] en orden de fecha (ver `puntos_evolucion`).
    - nivel_maximo: el de la rúbrica del nivel educativo. Si algún punto lo
      supera (porque la rúbrica se achicó), el eje crece para que quepa.
    - hasta: fecha hasta donde se prolonga el último nivel (por ejemplo, hoy).
      Si falta, el gráfico termina en el último punto.
    - etiqueta: nombre del núcleo, para el texto accesible.

    Devuelve "" si no hay puntos. Todo el texto va escapado. Usa
    `currentColor`, así que toma el color del texto de la página.
    """
    if not puntos:
        return ""
    techo = max(nivel_maximo, NIVEL_MIN + 1, *(p.nivel for p in puntos))
    inicio, actual = puntos[0].fecha, puntos[-1]
    fin = max(hasta or actual.fecha, actual.fecha)
    dias = (fin - inicio).days
    izq, der, sup, inf = MARGEN_IZQ, ANCHO - MARGEN_DER, MARGEN_SUP, ALTO - MARGEN_INF

    def x(fecha):
        if not dias:
            return (izq + der) / 2
        return izq + (der - izq) * (fecha - inicio).days / dias

    def y(nivel):
        return inf - (inf - sup) * (nivel - NIVEL_MIN) / (techo - NIVEL_MIN)

    resumen = ", ".join(f"nivel {p.texto} el {_fecha(p.fecha)}" for p in puntos)
    accesible = f"{resumen}. Nivel actual: {actual.texto} (de {nivel_maximo} niveles)."
    if etiqueta:
        accesible = f"{etiqueta}: {accesible}"
    accesible = escape(accesible)

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}" width="100%" '
        f'style="max-width: {ANCHO_MAXIMO}" role="img" aria-label="{accesible}" class="evolucion-grafico">',
        f"<title>{accesible}</title>",
    ]

    # Eje vertical: una línea guía y una marca por nivel de la rúbrica.
    for nivel in range(NIVEL_MIN, techo + 1):
        yn = y(nivel)
        partes.append(
            f'<line x1="{izq}" y1="{yn:.1f}" x2="{der}" y2="{yn:.1f}" '
            f'stroke="currentColor" stroke-opacity="0.15"/>'
        )
        partes.append(_texto(izq - 6, yn + TAMANO_LETRA * 0.35, str(nivel), "eje-y", "end"))

    # Escalones: horizontal hasta la fecha de la validación siguiente, luego vertical.
    trazo = [f"M {x(inicio):.1f} {y(puntos[0].nivel):.1f}"]
    for p in puntos[1:]:
        trazo.append(f"H {x(p.fecha):.1f} V {y(p.nivel):.1f}")
    if fin > actual.fecha:
        trazo.append(f"H {x(fin):.1f}")
    d = " ".join(trazo)
    partes.append(
        f'<path class="evolucion-linea" d="{d}" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linejoin="round"/>'
    )
    for p in puntos:
        partes.append(
            f'<circle class="evolucion-punto" cx="{x(p.fecha):.1f}" cy="{y(p.nivel):.1f}" r="3.5" '
            f'fill="currentColor"><title>Nivel {escape(p.texto)}, {_fecha(p.fecha)}</title></circle>'
        )

    # Eje horizontal: fecha de inicio y de término.
    base = ALTO - 6
    if dias:
        partes.append(_texto(izq, base, _fecha(inicio), "eje-x"))
        partes.append(_texto(der, base, _fecha(fin), "eje-x", "end"))
    else:
        partes.append(_texto((izq + der) / 2, base, _fecha(inicio), "eje-x", "middle"))

    partes.append("</svg>")
    return mark_safe("".join(partes))


def evolucion_del_nino(nino, hasta=None, nombres=None):
    """{sigla del núcleo: Evolucion}, con todos los núcleos en su orden.

    El último nivel se prolonga hasta `hasta` (por defecto, hoy). Un núcleo sin
    niveles validados queda con `puntos` vacío y sin gráfico. Hace una cantidad
    fija de consultas, sin importar cuántas validaciones haya.

    - nombres: {sigla del núcleo: {nivel: nombre}}, para mostrar "3 ·
      Desarrollando" (PLAN.md, Task 3). Si falta, se lee de los descriptores
      oficiales con `DescriptorNivel.nombres_por_nucleo`; los núcleos con
      rúbrica provisoria se muestran solo con el número. Se puede pasar si la
      vista ya los tiene, para ahorrar la consulta.
    """
    nivel_educativo = nino.curso.nivel_educativo
    if nombres is None:
        nombres = DescriptorNivel.nombres_por_nucleo(nivel_educativo)
    hasta = hasta or timezone.localdate()
    nivel_maximo = Rubrica.nivel_maximo(nivel_educativo)
    por_nucleo = {}
    for nv in NivelValidado.objects.filter(nino=nino).order_by("fecha", "creado", "id"):
        por_nucleo.setdefault(nv.nucleo_id, []).append(nv)
    evoluciones = {}
    for nucleo in Nucleo.objects.all():
        puntos = puntos_evolucion(por_nucleo.get(nucleo.pk, []), nombres.get(nucleo.sigla))
        svg = svg_evolucion(puntos, nivel_maximo, hasta=hasta, etiqueta=nucleo.nombre)
        evoluciones[nucleo.sigla] = Evolucion(nucleo, puntos, svg)
    return evoluciones
