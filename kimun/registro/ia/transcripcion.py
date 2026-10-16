"""Transcripción de audios con Amazon Transcribe (PLAN.md, Task 9).

No depende de Django. boto3 se importa recién al usar los clientes reales; los
tests pasan clientes falsos de Transcribe y S3.

`ClienteTranscribe.transcribir(audio, ...)`:

1. Detecta el formato por los primeros bytes, no por el nombre ni por el tipo que
   manda el navegador.
2. Sube el audio a `originales/capturas/` del bucket `KIMUN_BUCKET`.
3. Usa el vocabulario de nombres del curso si ya está listo (READY). Si no existe,
   lo crea; mientras queda listo (tarda unos minutos), transcribe sin vocabulario.
4. Lanza el trabajo en es-US con salida en `transcripciones/` del mismo bucket y
   consulta cada `intervalo` segundos hasta que termina o se cumple `tiempo_maximo`.
5. Lee el JSON de salida y devuelve el texto.
6. Borra del bucket la copia del audio y el JSON de salida, termine bien o mal: el audio
   no se conserva y el texto lo guarda quien llama (`registro/lectura.py`).

Si el proceso se corta antes del paso 6 (corte de luz, SIGKILL) o Transcribe escribe la
salida después de que se dejó de esperar (un trabajo en curso no se puede cancelar ni
borrar), las reglas de ciclo de vida del bucket (infra/plantilla.yaml) borran
`originales/capturas/` y `transcripciones/` al día siguiente.

Transcribe batch acepta AMR, FLAC, M4A, MP3, MP4, Ogg, WebM y WAV
(https://docs.aws.amazon.com/transcribe/latest/dg/how-input.html): los audios de
Android (WebM/Opus) y de iPhone (MP4/AAC) se mandan sin convertir.

Los permisos del rol de la instancia (infra/plantilla.yaml) exigen que los trabajos
y los vocabularios se llamen `kimun-*` y que la salida vaya a `transcripciones/`.
"""
import hashlib
import json
import logging
import os
import re
import secrets
import time
import unicodedata

logger = logging.getLogger(__name__)

IDIOMA = "es-US"
PREFIJO_ORIGINALES = "originales/capturas/"
PREFIJO_TRANSCRIPCIONES = "transcripciones/"
LARGO_MAXIMO_FRASE = 256

TIPOS_MIME = {
    "webm": "audio/webm",
    "ogg": "audio/ogg",
    "mp4": "audio/mp4",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "amr": "audio/amr",
}

# Caracteres válidos en un vocabulario en español
# (https://docs.aws.amazon.com/transcribe/latest/dg/charsets.html). No incluye "Ü".
_CARACTERES_VOCABULARIO = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'-.áéíóúñüÁÉÍÓÚÑ"
)
_CODIGOS_NO_EXISTE = {"BadRequestException", "NotFoundException"}
_CODIGOS_TRANSITORIOS = {"ThrottlingException", "LimitExceededException", "InternalFailureException"}
# Errores de red de botocore (EndpointConnectionError, ReadTimeoutError, ...) por nombre, para no importar
# botocore aquí. No traen `response`: sin esto, un corte breve de red se trataba como error definitivo.
_ERRORES_DE_RED = {"HTTPClientError", "ConnectionError", "TimeoutError"}
# Timeouts por llamada: los de botocore por defecto (60 s y varios reintentos) pueden pasar el umbral de
# captura atascada del worker (5 minutos) sumados a la espera de la transcripción.
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30
MAX_INTENTOS_LLAMADA = 3


class ErrorTranscripcion(Exception):
    """El audio no se pudo transcribir. La captura debe quedar con error y poder reintentarse."""


def _codigo_error(error):
    respuesta = getattr(error, "response", None)
    if isinstance(respuesta, dict):
        return respuesta.get("Error", {}).get("Code")
    return None


def _es_transitorio(error):
    """Throttling o error interno de Transcribe, o un error de red: se vuelve a consultar."""
    if _codigo_error(error) in _CODIGOS_TRANSITORIOS:
        return True
    return any(clase.__name__ in _ERRORES_DE_RED for clase in type(error).__mro__)


def _config_boto():
    from botocore.config import Config

    return Config(
        connect_timeout=CONNECT_TIMEOUT, read_timeout=READ_TIMEOUT,
        retries={"max_attempts": MAX_INTENTOS_LLAMADA, "mode": "standard"},
    )


def formato_audio(cabecera):
    """Formato de Transcribe ("webm", "mp4", ...) según los primeros 12 bytes; None si no es audio aceptado."""
    c = bytes(cabecera[:12])
    if c.startswith(b"\x1a\x45\xdf\xa3"):  # EBML: WebM de Chrome, Firefox y Android
        return "webm"
    if c.startswith(b"OggS"):
        return "ogg"
    if c[4:8] == b"ftyp":  # MP4 de Safari en iPhone
        return "m4a" if c[8:12] == b"M4A " else "mp4"
    if c.startswith(b"RIFF") and c[8:12] == b"WAVE":
        return "wav"
    if c.startswith(b"fLaC"):
        return "flac"
    if c.startswith(b"#!AMR"):
        return "amr"
    if c.startswith(b"ID3") or (len(c) >= 2 and c[0] == 0xFF and c[1] & 0xE0 == 0xE0):
        return "mp3"
    return None


def _limpiar_frase(texto):
    """Una frase válida para el vocabulario: espacios como guiones y sin caracteres fuera del set."""
    salida = []
    for caracter in unicodedata.normalize("NFC", texto.strip()):
        if caracter in _CARACTERES_VOCABULARIO:
            salida.append(caracter)
        elif caracter.isspace():
            salida.append("-")
        else:
            # "Ü" -> "U", "ç" -> "c". Dígitos y otros signos se omiten.
            base = unicodedata.normalize("NFD", caracter)[0]
            if base.isalpha() and base in _CARACTERES_VOCABULARIO:
                salida.append(base)
    frase = re.sub(r"-{2,}", "-", "".join(salida)).strip("-.'")
    return frase[:LARGO_MAXIMO_FRASE].strip("-.'")


def frases_vocabulario(nombres):
    """Frases del vocabulario a partir de nombres y apodos, sin repetir y en orden estable."""
    vistas, frases = set(), []
    for nombre in nombres:
        frase = _limpiar_frase(nombre or "")
        if frase and frase.casefold() not in vistas:
            vistas.add(frase.casefold())
            frases.append(frase)
    return sorted(frases, key=str.casefold)


def nombre_vocabulario(prefijo, frases):
    """El nombre lleva una firma de las frases: si cambian los niños, es otro vocabulario."""
    firma = hashlib.sha256("\n".join(frases).encode("utf-8")).hexdigest()[:10]
    return f"{prefijo}-{firma}"


class ClienteTranscribe:
    """Transcribe un audio y devuelve el texto. Ver el docstring del módulo.

    - Bucket: `KIMUN_BUCKET`. Región: `TRANSCRIBE_REGION` o `AWS_DEFAULT_REGION` (por defecto us-east-1).
    - `tiempo_maximo` (180 s) más la llamada a Bedrock (90 s como máximo) queda bajo
      el umbral de captura atascada del worker (5 minutos).
    - `transcribe`, `s3`, `dormir` y `reloj` se pueden inyectar para testear sin AWS ni esperas.
    """

    def __init__(
        self, bucket=None, region=None, intervalo=5.0, tiempo_maximo=180.0,
        transcribe=None, s3=None, dormir=time.sleep, reloj=time.monotonic,
    ):
        self.bucket = bucket if bucket is not None else os.environ.get("KIMUN_BUCKET", "")
        self.region = (
            region or os.environ.get("TRANSCRIBE_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
        )
        self.intervalo = intervalo
        self.tiempo_maximo = tiempo_maximo
        self._transcribe = transcribe
        self._s3 = s3
        self._dormir = dormir
        self._reloj = reloj

    @property
    def transcribe(self):
        if self._transcribe is None:
            import boto3

            self._transcribe = boto3.client("transcribe", region_name=self.region, config=_config_boto())
        return self._transcribe

    @property
    def s3(self):
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region, config=_config_boto())
        return self._s3

    def asegurar_vocabulario(self, prefijo, frases):
        """Nombre del vocabulario si está listo para usarse; si no, None.

        Si no existe, lo crea. Cualquier problema con el vocabulario se registra y se
        transcribe sin él: mejora el reconocimiento de nombres, pero no es indispensable.
        """
        frases = list(frases)
        if not frases:
            return None
        nombre = nombre_vocabulario(prefijo, frases)
        try:
            estado = self.transcribe.get_vocabulary(VocabularyName=nombre).get("VocabularyState")
        except Exception as error:
            if _codigo_error(error) not in _CODIGOS_NO_EXISTE:
                logger.warning("No se pudo consultar el vocabulario %s: %s", nombre, error)
                return None
            try:
                self.transcribe.create_vocabulary(VocabularyName=nombre, LanguageCode=IDIOMA, Phrases=frases)
                logger.info("Vocabulario %s creado (%s frases); se usará cuando esté listo", nombre, len(frases))
            except Exception as error_crear:
                if _codigo_error(error_crear) != "ConflictException":
                    logger.warning("No se pudo crear el vocabulario %s: %s", nombre, error_crear)
            return None
        if estado == "READY":
            return nombre
        if estado == "FAILED":
            logger.warning("El vocabulario %s quedó en FAILED; se transcribe sin vocabulario", nombre)
        return None

    def transcribir(self, audio, id_trabajo, prefijo_vocabulario=None, frases=()):
        """Texto transcrito de `audio` (bytes). Lanza ErrorTranscripcion si no se pudo.

        `id_trabajo` y `prefijo_vocabulario` deben empezar con "kimun-" (permisos del rol).
        Al trabajo se le agrega un sufijo al azar, porque Transcribe no admite nombres repetidos.
        """
        if not self.bucket:
            raise ErrorTranscripcion("Falta KIMUN_BUCKET, el bucket donde Transcribe lee el audio y deja el texto.")
        formato = formato_audio(audio[:12])
        if formato is None:
            raise ErrorTranscripcion("El archivo no está en un formato de audio que Transcribe acepte.")
        trabajo = f"{id_trabajo}-{secrets.token_hex(3)}"
        clave_audio = f"{PREFIJO_ORIGINALES}{trabajo}.{formato}"
        clave_salida = f"{PREFIJO_TRANSCRIPCIONES}{trabajo}.json"
        vocabulario = self.asegurar_vocabulario(prefijo_vocabulario, frases) if prefijo_vocabulario else None

        pedido = {
            "TranscriptionJobName": trabajo,
            "LanguageCode": IDIOMA,
            "MediaFormat": formato,
            "Media": {"MediaFileUri": f"s3://{self.bucket}/{clave_audio}"},
            "OutputBucketName": self.bucket,
            "OutputKey": clave_salida,
        }
        if vocabulario:
            pedido["Settings"] = {"VocabularyName": vocabulario}
        subido = False
        try:
            self.s3.put_object(Bucket=self.bucket, Key=clave_audio, Body=audio, ContentType=TIPOS_MIME[formato])
            subido = True
            self.transcribe.start_transcription_job(**pedido)
        except Exception as error:
            if subido:
                self._borrar(clave_audio)
            raise ErrorTranscripcion(f"No se pudo iniciar la transcripción {trabajo}: {error}") from error
        logger.info("Transcripción %s iniciada (%s, vocabulario: %s)", trabajo, formato, vocabulario or "ninguno")

        try:
            self._esperar(trabajo)
            return self._leer_texto(clave_salida)
        finally:
            # Ni el audio ni la salida de Transcribe se conservan en el bucket.
            self._borrar(clave_audio)
            self._borrar(clave_salida)

    def _borrar(self, clave):
        """Borra un objeto del bucket. Si falla, lo registra y sigue: la transcripción no se pierde."""
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=clave)
        except Exception as error:
            logger.warning("No se pudo borrar s3://%s/%s: %s", self.bucket, clave, error)

    def _esperar(self, trabajo):
        inicio = self._reloj()
        while True:
            try:
                info = self.transcribe.get_transcription_job(TranscriptionJobName=trabajo)["TranscriptionJob"]
                estado = info.get("TranscriptionJobStatus")
            except Exception as error:
                if not _es_transitorio(error):
                    raise ErrorTranscripcion(f"No se pudo consultar la transcripción {trabajo}: {error}") from error
                logger.warning(
                    "Consulta de %s falló (%s); se reintenta", trabajo, _codigo_error(error) or type(error).__name__
                )
                estado = None
            if estado == "COMPLETED":
                return
            if estado == "FAILED":
                motivo = info.get("FailureReason") or "sin motivo"
                raise ErrorTranscripcion(f"Transcribe no pudo transcribir el audio ({trabajo}): {motivo}")
            if self._reloj() - inicio >= self.tiempo_maximo:
                raise ErrorTranscripcion(f"La transcripción {trabajo} no terminó en {self.tiempo_maximo:g} s.")
            self._dormir(self.intervalo)

    def _leer_texto(self, clave):
        try:
            cuerpo = self.s3.get_object(Bucket=self.bucket, Key=clave)["Body"].read()
            transcripciones = json.loads(cuerpo)["results"]["transcripts"]
            return " ".join(t.get("transcript", "") for t in transcripciones).strip()
        except Exception as error:
            raise ErrorTranscripcion(f"No se pudo leer la transcripción {clave}: {error}") from error
