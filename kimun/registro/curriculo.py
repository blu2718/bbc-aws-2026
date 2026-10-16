"""Carga del currículo y la rúbrica provisoria desde `datos/`."""
import json
from pathlib import Path

from django.conf import settings
from django.db import transaction

from .models import DescriptorNivel, Manifestacion, NivelEducativo, Nucleo, ObjetivoAprendizaje, Rubrica
from .rubrica import NIVELES_PROVISORIOS, descriptores_provisorios, nombre_provisorio

RUTA_CURRICULO_TRANSICION = Path(settings.DATOS_DIR) / "curriculo_transicion.json"
# Sala cuna y medio salen de las Bases Curriculares (scripts/extraer_oa_bases.py). No traen conductas por año.
RUTAS_CURRICULO = {
    NivelEducativo.SALA_CUNA: Path(settings.DATOS_DIR) / "curriculo_sala_cuna.json",
    NivelEducativo.MEDIO: Path(settings.DATOS_DIR) / "curriculo_medio.json",
    NivelEducativo.TRANSICION: RUTA_CURRICULO_TRANSICION,
}


def leer_curriculo(ruta=RUTA_CURRICULO_TRANSICION):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def leer_curriculo_de(nivel_educativo):
    """El catálogo de núcleos y OA del nivel educativo (sala cuna, medio o transición)."""
    return leer_curriculo(RUTAS_CURRICULO[nivel_educativo])


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
        # La trayectoria (lo esperado al iniciar NT1 y en Básica) solo viene en el currículo de Transición:
        # cargar sala cuna o medio no la borra.
        trayectoria = {campo: n[campo] for campo in ("esperado_inicio_nt1", "continuidad_basica") if campo in n}
        if nivel_educativo == NivelEducativo.TRANSICION:
            trayectoria = {"esperado_inicio_nt1": "", "continuidad_basica": ""} | trayectoria
        nucleo, _ = Nucleo.objects.update_or_create(
            sigla=n["sigla"],
            defaults={"nombre": n["nombre"], "orden": orden, **trayectoria},
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

        # Sala cuna y medio también reciben rúbrica provisoria (sobre sus OA), solo en los núcleos con OA en
        # ese nivel: sin OA la propuesta no tendría con qué comparar.
        if nivel_educativo == NivelEducativo.TRANSICION or n["oas"]:
            for nivel, descripcion in descriptores_provisorios(nucleo, rubrica.cantidad_niveles, nivel_educativo):
                nombre = nombre_provisorio(nivel)
                descriptor, creado = DescriptorNivel.objects.get_or_create(
                    nivel_educativo=nivel_educativo, nucleo=nucleo, nivel=nivel,
                    defaults={"nombre": nombre, "descripcion": descripcion, "provisorio": True},
                )
                cambio = (descriptor.nombre, descriptor.descripcion) != (nombre, descripcion)
                if not creado and descriptor.provisorio and cambio:
                    descriptor.nombre, descriptor.descripcion = nombre, descripcion
                    descriptor.save(update_fields=["nombre", "descripcion"])
