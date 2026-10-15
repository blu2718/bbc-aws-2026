"""Carga de la rúbrica oficial de Integra desde `datos/rubrica_integra.json`.

Hoy trae solo Identidad y Autonomía (IA), en sala cuna, medio y transición
(PLAN.md, "Rúbrica de Integra"). En los núcleos que trae, sus descriptores
reemplazan a los provisorios. Los demás núcleos siguen con la rúbrica
provisoria. Cuando Integra entregue más núcleos u orientaciones, basta con
actualizar el JSON y volver a correr `cargar_demo`, sin cambiar código.
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import DescriptorNivel, NivelEducativo, Nucleo, Rubrica

RUTA_RUBRICA_INTEGRA = Path(settings.DATOS_DIR) / "rubrica_integra.json"


def leer_rubrica_integra(ruta=RUTA_RUBRICA_INTEGRA):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _orientaciones(valor):
    """Las orientaciones (pasos a seguir) vienen en null por ahora. Se acepta texto o lista de textos."""
    if valor is None:
        return None
    if isinstance(valor, list):
        return "\n".join(str(v) for v in valor)
    return str(valor)


@transaction.atomic
def cargar_rubrica_integra(datos):
    """Crea o actualiza los descriptores de los núcleos que trae la rúbrica de Integra.

    Se puede repetir sin duplicar. Por cada bloque (nivel educativo y núcleo):
    - crea la `Rubrica` del nivel educativo si falta, con tantos niveles como
      trae el bloque;
    - si la `Rubrica` ya existe con otra cantidad de niveles, falla sin cambiar
      nada, para no dejar niveles a medias;
    - no crea núcleos: si la sigla no existe, omite el bloque y lo informa;
    - deja los descriptores como no provisorios, con nombre, descripción,
      conducta y ejemplos. Las orientaciones van a `pasos_sugeridos`; si
      vienen vacías, no se pisan los pasos cargados desde el panel.

    Devuelve los bloques omitidos como [(nivel educativo, sigla)].
    Lanza ValidationError si los datos no calzan con la app.
    """
    nucleos = {n.sigla: n for n in Nucleo.objects.all()}
    omitidos = []
    for bloque in datos["rubricas"]:
        nivel_educativo, sigla, niveles = bloque["nivel_educativo"], bloque["sigla"], bloque["niveles"]
        donde = f"{sigla} en {nivel_educativo}"
        if nivel_educativo not in NivelEducativo.values:
            raise ValidationError(f"{donde}: nivel educativo desconocido.")
        nucleo = nucleos.get(sigla)
        if nucleo is None:
            omitidos.append((nivel_educativo, sigla))
            continue

        cantidad = len(niveles)
        if sorted(n["nivel"] for n in niveles) != list(range(1, cantidad + 1)):
            raise ValidationError(f"{donde}: los niveles deben ir de 1 a {cantidad}, sin saltos ni repetidos.")
        rubrica, _ = Rubrica.objects.get_or_create(
            nivel_educativo=nivel_educativo,
            # Provisoria mientras Integra no entregue todos los núcleos.
            defaults={"cantidad_niveles": cantidad, "provisoria": True},
        )
        if rubrica.cantidad_niveles != cantidad:
            raise ValidationError(
                f"{donde}: la rúbrica de Integra trae {cantidad} niveles y la de la app tiene "
                f"{rubrica.cantidad_niveles}. Hay que igualarlas (en el panel o en el JSON) antes de cargar."
            )

        for n in niveles:
            valores = {
                "nombre": n["nombre"],
                "descripcion": n["descripcion"],
                "conducta": n.get("conducta") or "",
                "ejemplos": list(n.get("ejemplos") or []),
                "provisorio": False,
            }
            pasos = _orientaciones(n.get("orientaciones"))
            if pasos is not None:
                valores["pasos_sugeridos"] = pasos
            DescriptorNivel.objects.update_or_create(
                nivel_educativo=nivel_educativo, nucleo=nucleo, nivel=n["nivel"], defaults=valores
            )
    return omitidos
