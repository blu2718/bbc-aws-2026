"""Iconos de los núcleos (`static/registro/img/nucleos/`).

Son siluetas claras sobre fondo transparente: no se muestran tal cual, se usan como
máscara y toman el color de quien las dibuja (el borde del pétalo en el gráfico del
perfil, rojo o naranjo en "Para tener presentes" del menú). Un núcleo sin icono
(Integra podría sumar otros) se muestra con su nombre o su sigla.
"""
from django.templatetags.static import static

ARCHIVOS = {
    "IA": "identidadautonomia.png",
    "CC": "convivenciaciudadania.png",
    "CM": "corporalidadmovimiento.png",
    "LV": "lenguajeverbal.png",
    "LA": "lenguajesartisticos.png",
    "EEN": "exploracionentornonatural.png",
    "CES": "comprensionentornosociocultural.png",
    "PM": "pensamientomatematico.png",
}


def icono_nucleo(sigla):
    """URL del icono del núcleo, o "" si no tiene."""
    archivo = ARCHIVOS.get(sigla)
    return static(f"registro/img/nucleos/{archivo}") if archivo else ""
