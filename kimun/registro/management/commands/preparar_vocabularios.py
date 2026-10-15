"""Crea en Transcribe el vocabulario de nombres de cada curso (Task 9).

    python manage.py preparar_vocabularios

Un vocabulario nuevo tarda unos minutos en quedar listo. Mientras tanto los audios se
transcriben sin él, así que conviene correr esto antes de la demo y después de cambiar
los niños de un curso. Se puede repetir: si el vocabulario ya existe, solo informa su estado.
"""
from django.core.management.base import BaseCommand

from registro.ia import ClienteTranscribe
from registro.models import Curso
from registro.procesamiento import frases_del_curso, prefijo_vocabulario


class Command(BaseCommand):
    help = "Crea en Transcribe el vocabulario de nombres de cada curso."
    stealth_options = ("transcriptor",)

    def handle(self, *args, **opciones):
        transcriptor = opciones.get("transcriptor") or ClienteTranscribe()
        for curso in Curso.objects.prefetch_related("ninos"):
            frases = frases_del_curso(curso.ninos.all())
            if not frases:
                self.stdout.write(f"{curso}: sin niños, no se crea vocabulario.")
                continue
            listo = transcriptor.asegurar_vocabulario(prefijo_vocabulario(curso), frases)
            estado = f"listo ({listo})" if listo else "creándose o con problemas; ver el log"
            self.stdout.write(f"{curso}: {len(frases)} frases, vocabulario {estado}.")
