"""Proceso de fondo: separa las capturas pendientes en observaciones (Tasks 5 y 9).

Las notas escritas van directo a la separación; las fotos se leen antes con Claude y
los audios se transcriben con Transcribe (requiere `KIMUN_BUCKET`). También lee las hojas
de resultados de instrumentos estandarizados (Task 14, `registro/instrumentos.py`). Es el único que
llama a Bedrock por una captura: la página solo consulta el estado. En el bucle,
las capturas atascadas en procesando vuelven solas a la cola.

    python manage.py procesar_capturas              # bucle, revisa cada 2 s
    python manage.py procesar_capturas --una-vez    # procesa lo pendiente y termina
    python manage.py procesar_capturas --una-vez --reintentar   # incluye las con error y las atascadas en procesando

La lógica está en `registro/procesamiento.py`. Los tests pasan clientes falsos de
Bedrock y Transcribe con `call_command(..., cliente=..., transcriptor=...)`.

Un error inesperado en una vuelta (por ejemplo, la base bloqueada) se registra y el bucle
sigue en la próxima: no tumba al proceso. SIGTERM (`systemctl restart`, cada despliegue)
detiene el bucle como Ctrl+C, así los `finally` alcanzan a borrar del bucket lo que se
subió a Transcribe.
"""
import logging
import math
import signal
import threading
import time

from django.core.management.base import BaseCommand, CommandError

from registro.curriculo import leer_curriculo
from registro.ia import ClienteBedrock, ClienteTranscribe
from registro.instrumentos import procesar_lecturas_pendientes, recuperar_lecturas_atascadas
from registro.procesamiento import (
    UMBRAL_PROCESANDO_ATASCADA, procesar_pendientes, recuperar_atascadas, reintentar_errores,
)

INTERVALO_POR_DEFECTO = 2.0

logger = logging.getLogger(__name__)


def _detener_con_sigterm(_senal, _marco):
    raise KeyboardInterrupt


class _SigtermComoCtrlC:
    """Mientras dura el bloque, SIGTERM se trata como Ctrl+C. Solo en el hilo principal (signal lo exige)."""

    def __enter__(self):
        self.anterior = None
        if threading.current_thread() is threading.main_thread():
            self.anterior = signal.signal(signal.SIGTERM, _detener_con_sigterm)
        return self

    def __exit__(self, *_):
        if self.anterior is not None:
            signal.signal(signal.SIGTERM, self.anterior)
        return False


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

        self.procesadas = self.errores = 0
        try:
            with _SigtermComoCtrlC():
                while True:
                    try:
                        self._vuelta(una_vez, cliente, catalogo, transcriptor)
                    except Exception:
                        # Lo que ya se tomó queda en error o vuelve solo a la cola (recuperar_atascadas).
                        self.errores += 1
                        logger.exception("Error inesperado en una vuelta de procesar_capturas; se sigue en la próxima")
                        self.stderr.write("Error inesperado en esta vuelta (detalle en el log); se sigue en la próxima.")
                    if una_vez:
                        break
                    time.sleep(intervalo)
        except KeyboardInterrupt:
            self.stdout.write("Detenido.")
        self.stdout.write(f"Listo: {self.procesadas} capturas procesadas, {self.errores} con error.")

    def _vuelta(self, una_vez, cliente, catalogo, transcriptor):
        # En el bucle, una captura que quedó a medias (worker reiniciado) vuelve sola a la cola.
        if not una_vez and (atascadas := recuperar_atascadas()):
            self.stdout.write(f"Capturas atascadas que vuelven a pendiente: {atascadas}")
        for captura, creadas in procesar_pendientes(cliente=cliente, catalogo=catalogo, transcriptor=transcriptor):
            if creadas is None:
                self.errores += 1
                self.stderr.write(f"Captura #{captura.pk}: error: {captura.error or 'cambió mientras se procesaba'}")
            else:
                self.procesadas += 1
                sin_nino = sum(1 for o in creadas if o.nino_id is None and not o.grupal)
                self.stdout.write(f"Captura #{captura.pk}: {len(creadas)} observaciones pendientes ({sin_nino} sin niño).")
        # Hojas de instrumentos estandarizados (Task 14): se leen con el mismo cliente de Bedrock.
        if not una_vez:
            recuperar_lecturas_atascadas()
        for resultado, ok in procesar_lecturas_pendientes(cliente=cliente):
            if ok:
                self.stdout.write(f"Hoja de instrumento #{resultado.pk}: leída, por revisar.")
            else:
                self.errores += 1
                self.stderr.write(f"Hoja de instrumento #{resultado.pk}: error: {resultado.error}")
