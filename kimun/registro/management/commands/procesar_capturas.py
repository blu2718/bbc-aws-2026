"""Proceso de fondo: separa las capturas pendientes en observaciones (Tasks 5 y 9).

Las notas escritas van directo a la separación; los audios se transcriben antes
con Transcribe (requiere `KIMUN_BUCKET`).

    python manage.py procesar_capturas              # bucle, revisa cada 5 s
    python manage.py procesar_capturas --una-vez    # procesa lo pendiente y termina
    python manage.py procesar_capturas --una-vez --reintentar   # incluye las con error y las atascadas en procesando

La lógica está en `registro/procesamiento.py`. Los tests pasan clientes falsos de
Bedrock y Transcribe con `call_command(..., cliente=..., transcriptor=...)`.
"""
import math
import time

from django.core.management.base import BaseCommand, CommandError

from registro.curriculo import leer_curriculo
from registro.ia import ClienteBedrock, ClienteTranscribe
from registro.procesamiento import UMBRAL_PROCESANDO_ATASCADA, procesar_pendientes, reintentar_errores

INTERVALO_POR_DEFECTO = 5.0


class Command(BaseCommand):
    help = "Separa las capturas pendientes (notas y audios) en observaciones pendientes de revisión."
    stealth_options = ("cliente", "catalogo", "transcriptor")

    def add_arguments(self, parser):
        parser.add_argument("--una-vez", action="store_true", help="Procesa lo pendiente y termina.")
        parser.add_argument(
            "--intervalo", type=float, default=INTERVALO_POR_DEFECTO,
            help=f"Segundos entre vueltas del bucle (por defecto {INTERVALO_POR_DEFECTO:g}).",
        )
        parser.add_argument(
            "--reintentar", action="store_true",
            help=(
                "Al empezar, vuelve a dejar pendientes las capturas que quedaron con error "
                f"y las que llevan más de {UMBRAL_PROCESANDO_ATASCADA.total_seconds() / 60:g} minutos en procesando."
            ),
        )

    def handle(self, *args, una_vez, intervalo, reintentar, **opciones):
        if not math.isfinite(intervalo) or intervalo <= 0:
            raise CommandError("--intervalo debe ser finito y mayor que 0.")
        # Un solo cliente para todo el proceso. boto3 se importa recién en la primera llamada.
        cliente = opciones.get("cliente") or ClienteBedrock()
        transcriptor = opciones.get("transcriptor") or ClienteTranscribe()
        catalogo = opciones.get("catalogo") or leer_curriculo()
        if reintentar:
            self.stdout.write(f"Capturas con error o atascadas que vuelven a pendiente: {reintentar_errores()}")

        procesadas = errores = 0
        try:
            while True:
                for captura, creadas in procesar_pendientes(cliente=cliente, catalogo=catalogo, transcriptor=transcriptor):
                    if creadas is None:
                        errores += 1
                        captura.refresh_from_db(fields=["error"])
                        self.stderr.write(f"Captura #{captura.pk}: error: {captura.error}")
                    else:
                        procesadas += 1
                        sin_nino = sum(1 for o in creadas if o.nino_id is None and not o.grupal)
                        self.stdout.write(
                            f"Captura #{captura.pk}: {len(creadas)} observaciones pendientes ({sin_nino} sin niño)."
                        )
                if una_vez:
                    break
                time.sleep(intervalo)
        except KeyboardInterrupt:
            self.stdout.write("Detenido.")
        self.stdout.write(f"Listo: {procesadas} capturas procesadas, {errores} con error.")
