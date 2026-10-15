"""Cliente de Bedrock con un cliente boto3 falso: sin red, sin credenciales y sin esperar."""

import pytest

from registro.ia import ClienteBedrock, ErrorBedrock
from registro.ia.bedrock import MODELO_POR_DEFECTO

HERRAMIENTA = {"name": "registrar_observaciones", "description": "d", "inputSchema": {"json": {"type": "object"}}}


class ErrorAws(Exception):
    """Imita botocore.exceptions.ClientError: el código viene en `response`."""

    def __init__(self, codigo):
        super().__init__(f"An error occurred ({codigo})")
        self.response = {"Error": {"Code": codigo, "Message": "falso"}}


class EndpointConnectionError(Exception):
    """Mismo nombre que el error de red de botocore."""


class ReadTimeoutError(Exception):
    """Mismo nombre que el timeout de lectura de botocore."""


class Reloj:
    def __init__(self):
        self.ahora = 0.0
        self.esperas = []

    def __call__(self):
        return self.ahora

    def dormir(self, segundos):
        self.esperas.append(segundos)
        self.ahora += segundos


def respuesta_ok(entrada=None, nombre="registrar_observaciones"):
    return {
        "output": {"message": {"role": "assistant", "content": [
            {"text": "Listo."},
            {"toolUse": {"toolUseId": "t1", "name": nombre, "input": entrada or {"observaciones": []}}},
        ]}},
        "stopReason": "tool_use",
        "usage": {"inputTokens": 5000, "outputTokens": 300, "totalTokens": 5300},
        "metrics": {"latencyMs": 4800},
    }


class Boto3Falso:
    def __init__(self, *resultados, reloj=None, demora=0.0):
        self.resultados = list(resultados)
        self.pedidos = []
        self.reloj = reloj
        self.demora = demora

    def converse(self, **pedido):
        self.pedidos.append(pedido)
        if self.reloj:
            self.reloj.ahora += self.demora
        resultado = self.resultados.pop(0)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado


@pytest.fixture
def reloj():
    return Reloj()


def _cliente(boto, reloj, **opciones):
    return ClienteBedrock(cliente=boto, dormir=reloj.dormir, reloj=reloj, azar=lambda: 0.0, **opciones)


def test_devuelve_el_input_de_la_herramienta_y_el_uso(reloj):
    boto = Boto3Falso(respuesta_ok({"observaciones": [{"cita_literal": "x"}]}))
    cliente = _cliente(boto, reloj)
    assert cliente.invocar_herramienta("sistema", "nota", HERRAMIENTA) == {"observaciones": [{"cita_literal": "x"}]}
    assert cliente.ultimo_uso == {"tokens_entrada": 5000, "tokens_salida": 300, "latencia_ms": 4800, "intentos": 1}


def test_fuerza_la_herramienta_y_no_envia_temperature(reloj):
    boto = Boto3Falso(respuesta_ok())
    _cliente(boto, reloj, max_tokens=2048).invocar_herramienta("sistema", "nota", HERRAMIENTA)
    pedido = boto.pedidos[0]
    assert pedido["toolConfig"] == {
        "tools": [{"toolSpec": HERRAMIENTA}],
        "toolChoice": {"tool": {"name": "registrar_observaciones"}},
    }
    assert pedido["inferenceConfig"] == {"maxTokens": 2048}
    assert pedido["system"] == [{"text": "sistema"}]
    assert pedido["messages"] == [{"role": "user", "content": [{"text": "nota"}]}]
    assert "temperature" not in str(pedido) and "topP" not in str(pedido)


def test_envia_las_imagenes_antes_del_texto(reloj):
    boto = Boto3Falso(respuesta_ok())
    _cliente(boto, reloj).invocar_herramienta("s", "Transcribe.", HERRAMIENTA, imagenes=[("jpeg", b"\xff\xd8\xffdatos")])
    assert boto.pedidos[0]["messages"] == [{"role": "user", "content": [
        {"image": {"format": "jpeg", "source": {"bytes": b"\xff\xd8\xffdatos"}}},
        {"text": "Transcribe."},
    ]}]


def test_modelo_y_region_por_variable_de_entorno(monkeypatch, reloj):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    monkeypatch.setenv("BEDROCK_REGION", "us-west-2")
    boto = Boto3Falso(respuesta_ok())
    cliente = _cliente(boto, reloj)
    cliente.invocar_herramienta("s", "m", HERRAMIENTA)
    assert boto.pedidos[0]["modelId"] == "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    assert cliente.region == "us-west-2"


def test_modelo_por_defecto(monkeypatch):
    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)
    monkeypatch.delenv("BEDROCK_REGION", raising=False)
    cliente = ClienteBedrock(cliente=Boto3Falso())
    assert cliente.modelo == MODELO_POR_DEFECTO == "us.anthropic.claude-sonnet-5"
    assert cliente.region == "us-east-1"


@pytest.mark.parametrize(
    "error",
    [ErrorAws("ThrottlingException"), ErrorAws("ServiceUnavailableException"), ErrorAws("ModelTimeoutException"),
     EndpointConnectionError("sin red"), TimeoutError("lectura")],
)
def test_reintenta_errores_transitorios_con_espera_creciente(error, reloj):
    boto = Boto3Falso(error, error, respuesta_ok())
    cliente = _cliente(boto, reloj, max_intentos=3, espera_base=1.0)
    assert cliente.invocar_herramienta("s", "m", HERRAMIENTA) == {"observaciones": []}
    assert len(boto.pedidos) == 3
    assert reloj.esperas == [1.0, 2.0]
    assert cliente.ultimo_uso["intentos"] == 3


def test_jitter_suma_hasta_un_cuarto_de_la_espera(reloj):
    boto = Boto3Falso(ErrorAws("ThrottlingException"), respuesta_ok())
    cliente = ClienteBedrock(cliente=boto, dormir=reloj.dormir, reloj=reloj, azar=lambda: 1.0, espera_base=2.0)
    cliente.invocar_herramienta("s", "m", HERRAMIENTA)
    assert reloj.esperas == [2.5]


@pytest.mark.parametrize("codigo", ["AccessDeniedException", "ValidationException"])
def test_no_reintenta_errores_definitivos(codigo, reloj):
    boto = Boto3Falso(ErrorAws(codigo), respuesta_ok())
    with pytest.raises(ErrorBedrock) as error:
        _cliente(boto, reloj).invocar_herramienta("s", "m", HERRAMIENTA)
    assert error.value.codigo == codigo
    assert len(boto.pedidos) == 1
    assert reloj.esperas == []


def test_se_rinde_al_agotar_los_intentos(reloj):
    boto = Boto3Falso(*[ErrorAws("ThrottlingException")] * 3)
    with pytest.raises(ErrorBedrock) as error:
        _cliente(boto, reloj, max_intentos=3).invocar_herramienta("s", "m", HERRAMIENTA)
    assert error.value.codigo == "ThrottlingException"
    assert len(boto.pedidos) == 3


def test_respeta_el_tiempo_maximo(reloj):
    # Cada llamada tarda 10 s (su peor caso): la tercera ya no cabría en los 25 s.
    boto = Boto3Falso(*[ErrorAws("ThrottlingException")] * 5, reloj=reloj, demora=10.0)
    cliente = _cliente(boto, reloj, max_intentos=5, tiempo_maximo=25.0, connect_timeout=0, read_timeout=10)
    with pytest.raises(ErrorBedrock, match="tiempo máximo"):
        cliente.invocar_herramienta("s", "m", HERRAMIENTA)
    assert len(boto.pedidos) == 2
    assert reloj.esperas == [1.0]
    assert reloj.ahora <= 25.0


def test_timeout_de_lectura_no_se_reintenta_con_los_valores_por_defecto(reloj):
    # Tras 60 s esperando al modelo no queda plazo para otra llamada completa.
    boto = Boto3Falso(ReadTimeoutError("lectura"), respuesta_ok(), reloj=reloj, demora=60.0)
    with pytest.raises(ErrorBedrock, match="tiempo máximo"):
        _cliente(boto, reloj).invocar_herramienta("s", "m", HERRAMIENTA)
    assert len(boto.pedidos) == 1
    assert reloj.esperas == []


def test_sin_tool_use_lanza_error(reloj):
    sin_herramienta = respuesta_ok()
    sin_herramienta["output"]["message"]["content"] = [{"text": "No puedo."}]
    with pytest.raises(ErrorBedrock, match="herramienta"):
        _cliente(Boto3Falso(sin_herramienta), reloj).invocar_herramienta("s", "m", HERRAMIENTA)


def test_tool_use_de_otra_herramienta_lanza_error(reloj):
    with pytest.raises(ErrorBedrock):
        _cliente(Boto3Falso(respuesta_ok(nombre="otra")), reloj).invocar_herramienta("s", "m", HERRAMIENTA)


def test_respuesta_cortada_por_max_tokens_lanza_error(reloj):
    cortada = respuesta_ok()
    cortada["stopReason"] = "max_tokens"
    with pytest.raises(ErrorBedrock, match="maxTokens"):
        _cliente(Boto3Falso(cortada), reloj).invocar_herramienta("s", "m", HERRAMIENTA)
