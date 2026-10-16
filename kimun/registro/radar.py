"""Gráfico del perfil: el nivel actual en cada núcleo, como una flor (diseno-interfaz.jpg, pantalla IV).

Cada núcleo es un pétalo de color suave: mientras más largo, más alto el nivel.
Los nombres de los núcleos van completos, en varias líneas, con su nivel debajo y su
icono al lado, del color del pétalo (`registro/iconos.py`).
Como referencia se marcan la mediana del curso (un punto blanco en cada pétalo)
y el nivel esperado según su semestre (un círculo punteado).

Ni la cantidad de núcleos (hoy 8, Integra tendrá 10) ni la de niveles (hoy 8,
podría ser 9) están fijas. El nivel se guarda por núcleo, no por OA: la rúbrica
no tiene niveles por OA. La ficha acompaña el gráfico con una tabla equivalente,
por accesibilidad. `svg_radar` es pura; todo el texto va escapado.
"""
import math
from dataclasses import dataclass

from django.utils.html import escape
from django.utils.safestring import mark_safe

from .iconos import icono_nucleo
from .models import NIVEL_MIN

# Pensado para el ancho de un teléfono: ahí el SVG se ve a ~75 % y la letra queda en ~11 px.
# Más ancho que alto para que quepa el icono junto a los nombres de los lados.
ANCHO, ALTO = 560, 480
CENTRO_X, CENTRO_Y = ANCHO / 2, 232
RADIO = 120
RADIO_ETIQUETA = RADIO + 24
# Aun el nivel 1 se ve como un pétalo pequeño, no como un punto.
RADIO_MINIMO = 0.2
TAMANO_LETRA = 15
ALTO_LINEA = 17
LETRAS_POR_LINEA = 13
ANCHO_MAXIMO = "36rem"
# Icono del núcleo (registro/iconos.py) junto a su nombre, del color del borde del pétalo.
ICONO = 20
SEPARACION_ICONO = 5
MINIMO_EJES = 3

# Pétalos: relleno pastel y borde del mismo tono, oscuro (al menos 3:1 sobre blanco).
# Los cuatro primeros son los colores del logo de Integra en pastel (ver registro.css).
PETALOS = (
    ("#cde3f3", "#125a91"),  # azul
    ("#fdeaaa", "#9a6508"),  # amarillo
    ("#d5ebc6", "#326412"),  # verde
    ("#fad2d1", "#a51c18"),  # rojo
    ("#e0d7f7", "#6250ad"),
    ("#ffd8c6", "#ad5426"),
    ("#dcf0c0", "#55791f"),
    ("#cfe7ef", "#2c6f86"),
    ("#f3e1c4", "#86602b"),
    ("#e6d9ec", "#7a4a8c"),
)
COLOR_MEDIANA = "#4a5160"   # 8:1 sobre blanco
COLOR_ESPERADO = "#b36b00"  # 4,2:1 sobre blanco (línea, mínimo 3:1)


@dataclass(frozen=True)
class EjeRadar:
    sigla: str
    nombre: str
    nivel: int | None
    texto: str                    # "3 · Desarrollando", o "Sin nivel validado"
    mediana: float | int | None = None
    icono: str = ""               # URL del icono del núcleo; "" si no tiene


def _numero(valor):
    return str(int(valor)) if valor == int(valor) else f"{valor:.1f}".replace(".", ",")


def _angulo(i, total):
    return -math.pi / 2 + 2 * math.pi * i / total


def _punto(angulo, radio):
    return CENTRO_X + radio * math.cos(angulo), CENTRO_Y + radio * math.sin(angulo)


def _radio(nivel, techo):
    return RADIO * (RADIO_MINIMO + (1 - RADIO_MINIMO) * max(nivel or 0, 0) / techo)


def _xy(punto):
    return "{:.1f} {:.1f}".format(*punto)


def _petalo(angulo, radio, ancho):
    """Un pétalo redondeado que sale del centro y llega a `radio` en la dirección `angulo`."""
    punta = _punto(angulo, radio)
    return (
        f"M {CENTRO_X:.1f} {CENTRO_Y:.1f} "
        f"C {_xy(_punto(angulo - ancho * 1.25, radio * 0.5))} {_xy(_punto(angulo - ancho * 0.8, radio * 1.02))} {_xy(punta)} "
        f"C {_xy(_punto(angulo + ancho * 0.8, radio * 1.02))} {_xy(_punto(angulo + ancho * 1.25, radio * 0.5))} "
        f"{CENTRO_X:.1f} {CENTRO_Y:.1f} Z"
    )


def lineas(texto, largo=LETRAS_POR_LINEA):
    """Parte un nombre en líneas de hasta `largo` letras sin cortar palabras."""
    resultado = []
    for palabra in texto.split():
        if resultado and len(resultado[-1]) + 1 + len(palabra) <= largo:
            resultado[-1] += " " + palabra
        else:
            resultado.append(palabra)
    return resultado or [""]


def descripcion_radar(ejes, esperado=None):
    """Texto equivalente al gráfico, para lectores de pantalla."""
    partes = []
    for eje in ejes:
        parte = f"{eje.nombre}: {eje.texto}"
        if eje.mediana is not None:
            parte += f" (mediana del curso {_numero(eje.mediana)})"
        partes.append(parte)
    texto = "Nivel actual en cada núcleo. " + "; ".join(partes) + "."
    if esperado is not None:
        texto += f" Nivel esperado según su semestre: {esperado}."
    return texto


def _icono(eje, indice, x, y, color):
    """Icono del núcleo con la esquina superior izquierda en (x, y), pintado de `color`.

    El PNG es una silueta clara: se usa como máscara (su transparencia) sobre un
    cuadrado del color del pétalo, así se ve sobre el fondo blanco.
    """
    id_mascara = f"radar-icono-{indice}"
    caja = f'x="{x:.1f}" y="{y:.1f}" width="{ICONO}" height="{ICONO}"'
    return (
        f'<mask id="{id_mascara}" maskUnits="userSpaceOnUse" {caja} style="mask-type: alpha">'
        f'<image href="{escape(eje.icono)}" {caja}/></mask>'
        f'<rect class="radar-icono" {caja} fill="{color}" mask="url(#{id_mascara})"/>'
    )


def _etiqueta(eje, angulo, indice=0, color="currentColor"):
    """Nombre completo del núcleo, en varias líneas, y su nivel debajo, con su icono al lado.

    A los lados, el icono va junto a la primera línea, del lado del pétalo. Arriba y
    abajo (texto centrado) va centrado sobre el nombre.
    """
    x, y = _punto(angulo, RADIO_ETIQUETA)
    coseno, seno = math.cos(angulo), math.sin(angulo)
    anclaje = "start" if coseno > 0.3 else "end" if coseno < -0.3 else "middle"
    filas = lineas(eje.nombre)
    nivel = f"nivel {eje.nivel}" if eje.nivel is not None else "sin nivel"
    total = len(filas) + 1
    if seno < -0.3:      # arriba: el bloque termina junto al pétalo
        y -= (total - 1) * ALTO_LINEA
    elif seno > 0.3:     # abajo: el bloque empieza junto al pétalo
        y += ALTO_LINEA * 0.8
    else:                # a los lados: centrado
        y -= (total - 1) * ALTO_LINEA / 2 - TAMANO_LETRA * 0.35
    icono = ""
    if eje.icono:
        # La primera línea tiene su base en y; el icono se centra en la altura de sus letras.
        arriba = y - TAMANO_LETRA * 0.35 - ICONO / 2
        if anclaje == "start":
            icono, x = _icono(eje, indice, x, arriba, color), x + ICONO + SEPARACION_ICONO
        elif anclaje == "end":
            icono, x = _icono(eje, indice, x - ICONO, arriba, color), x - ICONO - SEPARACION_ICONO
        else:
            icono = _icono(eje, indice, x - ICONO / 2, max(y - TAMANO_LETRA - ICONO, 0), color)
    tspans = "".join(
        f'<tspan x="{x:.1f}" dy="{0 if i == 0 else ALTO_LINEA}">{escape(fila)}</tspan>' for i, fila in enumerate(filas)
    )
    tspans += f'<tspan x="{x:.1f}" dy="{ALTO_LINEA}" class="radar-nivel" font-weight="700">{escape(nivel)}</tspan>'
    return icono + (
        f'<text class="radar-etiqueta" x="{x:.1f}" y="{y:.1f}" text-anchor="{anclaje}" font-size="{TAMANO_LETRA}" '
        f'fill="currentColor">{tspans}</text>'
    )


def svg_radar(ejes, nivel_maximo, esperado=None):
    """SVG listo para insertar, o "" si hay menos de 3 núcleos.

    - ejes: [EjeRadar] en el orden de los núcleos.
    - nivel_maximo: el de la rúbrica del nivel educativo; el gráfico crece si
      algún nivel lo supera (porque la rúbrica se achicó).
    - esperado: nivel esperado del niño según su semestre de permanencia, o None.
    """
    if len(ejes) < MINIMO_EJES:
        return ""
    total = len(ejes)
    # Entero hacia arriba: la mediana puede quedar en x,5 sobre el máximo si la rúbrica se achicó.
    techo = math.ceil(max([
        nivel_maximo, NIVEL_MIN + 1, esperado or 0,
        *(e.nivel for e in ejes if e.nivel), *(e.mediana for e in ejes if e.mediana),
    ]))
    ancho = min(0.5, math.pi / total * 0.95)
    accesible = escape(descripcion_radar(ejes, esperado))

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}" width="100%" '
        f'style="max-width: {ANCHO_MAXIMO}" role="img" aria-label="{accesible}" class="radar">',
        f"<title>{accesible}</title>",
    ]

    # Un círculo suave por nivel de la rúbrica.
    for nivel in range(NIVEL_MIN, techo + 1):
        borde = ' stroke-opacity="0.22"' if nivel == techo else ' stroke-opacity="0.1" stroke-dasharray="2 4"'
        partes.append(
            f'<circle class="radar-anillo" cx="{CENTRO_X:.1f}" cy="{CENTRO_Y:.1f}" r="{_radio(nivel, techo):.1f}" '
            f'fill="none" stroke="currentColor"{borde}/>'
        )

    # Los pétalos: uno por núcleo.
    for i, eje in enumerate(ejes):
        angulo = _angulo(i, total)
        relleno, borde = PETALOS[i % len(PETALOS)]
        radio = _radio(eje.nivel, techo)
        partes.append(
            f'<path class="radar-petalo" d="{_petalo(angulo, radio, ancho)}" fill="{relleno}" stroke="{borde}" '
            f'stroke-width="2" stroke-linejoin="round"><title>{escape(eje.nombre)}: {escape(eje.texto)}</title></path>'
        )
        if eje.nivel is not None:
            x, y = _punto(angulo, radio)
            partes.append(f'<circle class="radar-punto" cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{borde}"/>')
        partes.append(_etiqueta(eje, angulo, i, borde))

    # Referencias: el nivel esperado (círculo punteado) y la mediana del curso (punto blanco en cada pétalo).
    if esperado is not None:
        partes.append(
            f'<circle class="radar-esperado" cx="{CENTRO_X:.1f}" cy="{CENTRO_Y:.1f}" r="{_radio(esperado, techo):.1f}" '
            f'fill="none" stroke="{COLOR_ESPERADO}" stroke-width="2.5" stroke-dasharray="1 6" stroke-linecap="round"/>'
        )
    for i, eje in enumerate(ejes):
        if eje.mediana is None:
            continue
        x, y = _punto(_angulo(i, total), _radio(eje.mediana, techo))
        partes.append(
            f'<circle class="radar-mediana" cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#fff" stroke="{COLOR_MEDIANA}" '
            f'stroke-width="1.8"><title>Mediana del curso en {escape(eje.nombre)}: {_numero(eje.mediana)}</title></circle>'
        )
    partes.append(f'<circle cx="{CENTRO_X:.1f}" cy="{CENTRO_Y:.1f}" r="6" fill="#fff" stroke="currentColor" stroke-opacity="0.25"/>')
    partes.append("</svg>")
    return mark_safe("".join(partes))


def radar_de_la_ficha(ficha, nivel_maximo):
    """(svg, esperado) a partir de `ficha.armar_ficha`, con los mismos datos que la tabla del curso."""
    ejes = []
    esperado = None
    for nf in ficha.nucleos:
        situacion = nf.situacion
        if situacion is not None and esperado is None:
            esperado = situacion.esperado
        ejes.append(EjeRadar(
            sigla=nf.nucleo.sigla,
            nombre=nf.nucleo.nombre,
            nivel=nf.actual.nivel if nf.actual else None,
            texto=nf.texto_actual,
            mediana=situacion.mediana_curso if situacion else None,
            icono=icono_nucleo(nf.nucleo.sigla),
        ))
    return svg_radar(ejes, nivel_maximo, esperado), esperado
