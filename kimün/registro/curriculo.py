"""Carga del currículo y la rúbrica provisoria desde `datos/`."""
import json
from pathlib import Path

from django.conf import settings
from django.db import transaction

from .models import DescriptorNivel, Manifestacion, NivelEducativo, Nucleo, ObjetivoAprendizaje, Rubrica
from .rubrica import NIVELES_PROVISORIOS, descriptores_provisorios

RUTA_CURRICULO_TRANSICION = Path(settings.DATOS_DIR) / "curriculo_transicion.json"


def leer_curriculo(ruta=RUTA_CURRICULO_TRANSICION):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


@transaction.atomic
def cargar_curriculo(datos, nivel_educativo=NivelEducativo.TRANSICION):
    """Crea o actualiza núcleos, OA, conductas y rúbrica. Se puede repetir sin duplicar.

    La cantidad de niveles de la rúbrica solo se fija al crearla: si alguien la
    cambió en el panel (por ejemplo a 9), volver a cargar no la pisa. Tampoco se
    pisan descriptores no provisorios ni los pasos sugeridos.
    """
    rubrica, _ = Rubrica.objects.get_or_create(
        nivel_educativo=nivel_educativo,
        defaults={"cantidad_niveles": NIVELES_PROVISORIOS, "provisoria": True},
    )
    for orden, n in enumerate(datos["nucleos"], start=1):
        nucleo, _ = Nucleo.objects.update_or_create(
            sigla=n["sigla"],
            defaults={
                "nombre": n["nombre"],
                "orden": orden,
                "esperado_inicio_nt1": n.get("esperado_inicio_nt1", ""),
                "continuidad_basica": n.get("continuidad_basica", ""),
            },
        )
        for o in n["oas"]:
            oa, _ = ObjetivoAprendizaje.objects.update_or_create(
                nivel_educativo=nivel_educativo, nucleo=nucleo, numero=o["numero"],
                defaults={"texto": o["texto"]},
            )
            for anio in (Manifestacion.Anio.NT1, Manifestacion.Anio.NT2):
                conductas = o["conductas"].get(anio, [])
                for i, texto in enumerate(conductas):
                    Manifestacion.objects.update_or_create(oa=oa, anio=anio, orden=i, defaults={"texto": texto})
                # Si el JSON ahora trae menos conductas, se borran las sobrantes.
                Manifestacion.objects.filter(oa=oa, anio=anio, orden__gte=len(conductas)).delete()

        if nivel_educativo == NivelEducativo.TRANSICION:
            for nivel, descripcion in descriptores_provisorios(nucleo, rubrica.cantidad_niveles):
                descriptor, creado = DescriptorNivel.objects.get_or_create(
                    nivel_educativo=nivel_educativo, nucleo=nucleo, nivel=nivel,
                    defaults={"descripcion": descripcion, "provisorio": True},
                )
                if not creado and descriptor.provisorio and descriptor.descripcion != descripcion:
                    descriptor.descripcion = descripcion
                    descriptor.save(update_fields=["descripcion"])
