"""Cliente mínimo de Bedrock (API Converse) con tool use obligatorio.

No depende de Django. boto3 se importa recién al crear el cliente real, así los
tests pueden pasar un cliente falso (cualquier objeto con `converse(**kwargs)`)
sin boto3 ni credenciales.

Uso:

    cliente = ClienteBedrock()
    entrada = cliente.invocar_herramienta(system, mensaje, herramienta)
    cliente.ultimo_uso  # {"tokens_entrada", "tokens_salida", "latencia_ms", "intentos"}
"""

import logging
import os
import random
import time

logger = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "us.anthropic.claude-sonnet-5"
REGION_POR_DEFECTO = "us-east-1"

# Errores transitorios del servicio: se reintentan con espera creciente.
CODIGOS_REINTENTABLES = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "InternalServerException",
    "ModelNotReadyException",
    "ModelTimeoutException",
}
# Errores de red de botocore. Se comparan por nombre para no importar botocore aquí.
CLASES_RED_REINTENTABLES = {
    "EndpointConnectionError",
    "ConnectTimeoutError",
    "ReadTimeoutError",
    "ConnectionClosedError",
}


class ErrorBedrock(Exception):
    """Falla al llamar a Bedrock o respuesta inutilizable. `codigo` trae el código de AWS si lo hay."""

    def __init__(self, mensaje, codigo=None):
        super().__init__(mensaje)
        self.codigo = codigo


def _codigo_error(error):
    respuesta = getattr(error, "response", None)
    if isinstance(respuesta, dict):
        return respuesta.get("Error", {}).get("Code")
    return None


def _es_reintentable(error):
    if _codigo_error(error) in CODIGOS_REINTENTABLES:
        return True
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    return any(clase.__name__ in CLASES_RED_REINTENTABLES for clase in type(error).__mro__)


class ClienteBedrock:
    """Llama a un modelo con una sola herramienta y obliga a usarla.

    - Modelo: `BEDROCK_MODEL_ID` (por defecto el perfil de inferencia de Sonnet 5).
    - Región: `BEDROCK_REGION` (por defecto us-east-1).
    - No envía `temperature` ni `topP`: Sonnet 5 los rechaza.
    - Reintenta solo errores transitorios, hasta `max_intentos`, con espera
      exponencial más jitter. Cada llamada está acotada por `connect_timeout` y
      `read_timeout` (los reintentos propios de botocore quedan apagados), y un
      reintento solo se lanza si, sumando la espera y el peor caso de la llamada
      (`connect_timeout + read_timeout`), se termina dentro de `tiempo_maximo`.
      `read_timeout` de botocore mide el tiempo sin recibir datos, así que el
      plazo es un tope práctico, no un corte exacto.
    - Con los valores por defecto (read_timeout 60, tiempo_maximo 90), un timeout
      de lectura no se reintenta: el modelo seguía generando y reenviar el prompt
      lo cobraría de nuevo y tardaría lo mismo. Los errores rápidos (throttling,
      servicio no disponible) sí se reintentan.
    - `dormir`, `reloj` y `azar` se pueden inyectar para testear sin esperar.
    """

    def __init__(
        self,
        modelo=None,
        region=None,
        max_tokens=4096,
        max_intentos=3,
        espera_base=1.0,
        espera_maxima=8.0,
        tiempo_maximo=90.0,
        connect_timeout=5,
        read_timeout=60,
        cliente=None,
        dormir=time.sleep,
        reloj=time.monotonic,
        azar=random.random,
    ):
        self.modelo = modelo or os.environ.get("BEDROCK_MODEL_ID") or MODELO_POR_DEFECTO
        self.region = region or os.environ.get("BEDROCK_REGION") or REGION_POR_DEFECTO
        self.max_tokens = max_tokens
        self.max_intentos = max_intentos
        self.espera_base = espera_base
        self.espera_maxima = espera_maxima
        self.tiempo_maximo = tiempo_maximo
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self._cliente = cliente
        self._dormir = dormir
        self._reloj = reloj
        self._azar = azar
        self.ultimo_uso = None

    @property
    def cliente(self):
        if self._cliente is None:
            import boto3
            from botocore.config import Config

            self._cliente = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                config=Config(
                    connect_timeout=self.connect_timeout,
                    read_timeout=self.read_timeout,
                    retries={"total_max_attempts": 1},
                ),
            )
        return self._cliente

    def _espera(self, intento):
        espera = min(self.espera_maxima, self.espera_base * 2 ** (intento - 1))
        return espera + espera * 0.25 * self._azar()

    def invocar_herramienta(self, system, mensaje, herramienta, imagenes=()):
        """Devuelve el `input` que el modelo pasó a la herramienta (un dict).

        `herramienta` es un toolSpec de Converse:
        {"name": ..., "description": ..., "inputSchema": {"json": {...}}}.
        `imagenes` es una lista de (formato, bytes), con formato "jpeg", "png",
        "gif" o "webp". Van antes del texto en el mismo mensaje. La validación
        de formato y tamaño la hace quien llama (ver `ia/foto.py`).
        Deja en `self.ultimo_uso` los tokens, la latencia del modelo y los intentos.
        """
        nombre = herramienta["name"]
        contenido = [{"image": {"format": formato, "source": {"bytes": datos}}} for formato, datos in imagenes]
        contenido.append({"text": mensaje})
        pedido = {
            "modelId": self.modelo,
            "system": [{"text": system}],
            "messages": [{"role": "user", "content": contenido}],
            "inferenceConfig": {"maxTokens": self.max_tokens},
            "toolConfig": {
                "tools": [{"toolSpec": herramienta}],
                "toolChoice": {"tool": {"name": nombre}},
            },
        }
        inicio = self._reloj()
        intento = 0
        while True:
            intento += 1
            try:
                respuesta = self.cliente.converse(**pedido)
                break
            except Exception as error:
                codigo = _codigo_error(error)
                if not _es_reintentable(error):
                    raise ErrorBedrock(f"Bedrock rechazó la llamada: {error}", codigo) from error
                if intento >= self.max_intentos:
                    raise ErrorBedrock(f"Bedrock falló {intento} veces: {error}", codigo) from error
                espera = self._espera(intento)
                # Solo se reintenta si el intento siguiente, en su peor caso, termina dentro del plazo.
                peor_intento = self.connect_timeout + self.read_timeout
                if self._reloj() - inicio + espera + peor_intento > self.tiempo_maximo:
                    raise ErrorBedrock(
                        f"Se agotó el tiempo máximo ({self.tiempo_maximo} s) tras {intento} intentos: {error}",
                        codigo,
                    ) from error
                logger.warning("Bedrock intento %s falló (%s); reintento en %.1f s", intento, codigo or error, espera)
                self._dormir(espera)

        uso = respuesta.get("usage", {})
        self.ultimo_uso = {
            "tokens_entrada": uso.get("inputTokens"),
            "tokens_salida": uso.get("outputTokens"),
            "latencia_ms": respuesta.get("metrics", {}).get("latencyMs"),
            "intentos": intento,
        }
        if respuesta.get("stopReason") == "max_tokens":
            raise ErrorBedrock(f"La respuesta se cortó al llegar a maxTokens ({self.max_tokens}).")
        for bloque in respuesta.get("output", {}).get("message", {}).get("content", []):
            uso_herramienta = bloque.get("toolUse")
            if uso_herramienta and uso_herramienta.get("name") == nombre:
                return uso_herramienta.get("input")
        raise ErrorBedrock(f"La respuesta no trae el uso de la herramienta {nombre!r}.")
