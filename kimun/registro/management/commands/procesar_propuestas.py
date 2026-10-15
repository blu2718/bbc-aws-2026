"""Proceso de fondo de propuestas de nivel; comparte la base con Django."""
import math
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from registro.propuestas import CADUCIDAD_SEGUNDOS, procesar_siguiente, recuperar_interrumpidas


class Command(BaseCommand):
    help = "Procesa propuestas pendientes. --once procesa como máximo una solicitud y termina."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--intervalo", type=float, default=2.0, help="Espera sin trabajos, entre 0 y 60 segundos.")
        parser.add_argument("--caducidad", type=int, default=CADUCIDAD_SEGUNDOS,
                            help="Segundos para recuperar un intento interrumpido (mínimo 120).")

    def handle(self, *args, **options):
        intervalo, caducidad = options["intervalo"], options["caducidad"]
        if not math.isfinite(intervalo) or not 0 < intervalo <= 60 or caducidad < 120:
            raise CommandError("El intervalo debe ser mayor que 0 y hasta 60; la caducidad, al menos 120 segundos.")
        try:
            while True:
                close_old_connections()
                recuperadas = recuperar_interrumpidas(caducidad=caducidad)
                if recuperadas:
                    self.stdout.write(f"Intentos interrumpidos recuperados: {recuperadas}.")
                propuesta = procesar_siguiente()
                if propuesta:
                    self.stdout.write(f"Propuesta #{propuesta.pk}: {propuesta.get_estado_display()}.")
                if options["once"]:
                    return
                if propuesta is None:
                    time.sleep(intervalo)
        except KeyboardInterrupt:
            self.stdout.write("Procesamiento detenido.")
