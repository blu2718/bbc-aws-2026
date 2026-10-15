"""Genera con Polly los audios de prueba del set de notas (PLAN.md, Tasks 9 y 10).

    python manage.py generar_audios                 # las notas que todavía no tienen audio
    python manage.py generar_audios --ids n04 n15   # solo algunas
    python manage.py generar_audios --forzar        # vuelve a generar todas

Deja `datos/eval/audios/<id>.mp3`, uno por nota de `datos/eval/notas_separacion.json`.
Usa `texto_audio` (la nota como se dictaría) si la nota lo trae, y si no `texto`.
Las voces es-US de Polly se reparten en orden por la posición de la nota en el set,
para que haya voces de mujer y de hombre, neurales y estándar. Los audios son
sintéticos: en el evento no se graban voces reales (docs/investigacion_servicios.md,
"Privacidad"). Los tests pasan un Polly falso con `call_command(..., polly=...)`.
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

RUTA_SET = Path(settings.DATOS_DIR) / "eval" / "notas_separacion.json"
CARPETA_AUDIOS = Path(settings.DATOS_DIR) / "eval" / "audios"
IDIOMA = "es-US"
# (voz, motor). Penélope y Miguel solo existen en el motor estándar.
VOCES = [("Lupe", "neural"), ("Pedro", "neural"), ("Penelope", "standard"), ("Miguel", "standard")]


def texto_a_dictar(nota):
    return nota.get("texto_audio") or nota["texto"]


def voz_de(posicion):
    return VOCES[posicion % len(VOCES)]


class Command(BaseCommand):
    help = "Genera con Polly un audio MP3 por nota del set de evaluación."
    stealth_options = ("polly",)

    def add_arguments(self, parser):
        parser.add_argument("--ids", nargs="+", metavar="ID", help="Solo estas notas del set.")
        parser.add_argument("--forzar", action="store_true", help="Vuelve a generar aunque el audio ya exista.")
        parser.add_argument("--carpeta", default=str(CARPETA_AUDIOS), help="Dónde dejar los audios.")
        parser.add_argument("--set", dest="ruta_set", default=str(RUTA_SET), help="Set de notas a usar.")

    def handle(self, *args, ids, forzar, carpeta, ruta_set, **opciones):
        notas = json.loads(Path(ruta_set).read_text(encoding="utf-8"))["notas"]
        if ids:
            desconocidas = sorted(set(ids) - {n["id"] for n in notas})
            if desconocidas:
                raise CommandError(f"No existen en el set: {', '.join(desconocidas)}")
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        polly = opciones.get("polly")
        if polly is None:
            import boto3

            polly = boto3.client("polly")

        generados = omitidos = 0
        for posicion, nota in enumerate(notas):
            if ids and nota["id"] not in ids:
                continue
            ruta = carpeta / f"{nota['id']}.mp3"
            if ruta.exists() and not forzar:
                omitidos += 1
                continue
            voz, motor = voz_de(posicion)
            try:
                respuesta = polly.synthesize_speech(
                    Text=texto_a_dictar(nota), VoiceId=voz, Engine=motor, LanguageCode=IDIOMA, OutputFormat="mp3",
                )
                audio = respuesta["AudioStream"].read()
            except Exception as error:
                raise CommandError(f"Polly no pudo generar {nota['id']} con la voz {voz}: {error}") from error
            ruta.write_bytes(audio)
            generados += 1
            self.stdout.write(f"{nota['id']}: {voz} ({motor}), {len(audio) // 1024} KB")
        self.stdout.write(f"Listo: {generados} audios generados, {omitidos} ya existían, en {carpeta}.")
