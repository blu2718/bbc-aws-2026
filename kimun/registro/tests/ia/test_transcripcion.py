"""Cliente de Transcribe con Transcribe y S3 falsos (PLAN.md, Task 9). Sin Django, sin red ni boto3."""
import io
import json
import logging
import re

import pytest

from registro.ia.transcripcion import (
    ClienteTranscribe,
    ErrorTranscripcion,
    formato_audio,
    frases_vocabulario,
    nombre_vocabulario,
)

WEBM = b"\x1a\x45\xdf\xa3" + bytes(64)
MP4_IPHONE = b"\x00\x00\x00\x1cftypiso5" + bytes(64)
TEXTO = "Rubí cruzó el circuito sin ayuda"
BUCKET = "kimun-mvp-123"
FRASES = ["Pedro", "Rubí", "Rubí-Contreras"]
# Lo que acepta Transcribe en un vocabulario en español (docs: "Spanish character set").
FRASE_VALIDA = re.compile(r"^[A-Za-z'\-.áéíóúñüÁÉÍÓÚÑ]+$")


class ErrorAws(Exception):
    """Imita a botocore.exceptions.ClientError: trae el código en `response`."""

    def __init__(self, codigo, mensaje="error de prueba"):
        super().__init__(f"{codigo}: {mensaje}")
        self.response = {"Error": {"Code": codigo, "Message": mensaje}}


class TranscribeFalso:
    """`vocabulario`: estado del vocabulario, None si no existe, o una excepción."""

    def __init__(self, estados=("COMPLETED",), vocabulario="READY", motivo="El audio no tiene voz."):
        self.estados = list(estados)
        self.vocabulario = vocabulario
        self.motivo = motivo
        self.creados = []
        self.trabajos = []
        self.consultas = 0
        self.error_al_crear = None
        self.error_al_iniciar = None

    def get_vocabulary(self, VocabularyName):
        if isinstance(self.vocabulario, Exception):
            raise self.vocabulario
        if self.vocabulario is None:
            raise ErrorAws("BadRequestException", "The requested vocabulary couldn't be found.")
        return {"VocabularyName": VocabularyName, "VocabularyState": self.vocabulario}

    def create_vocabulary(self, **pedido):
        if self.error_al_crear:
            raise self.error_al_crear
        self.creados.append(pedido)
        return {"VocabularyState": "PENDING"}

    def start_transcription_job(self, **pedido):
        if self.error_al_iniciar:
            raise self.error_al_iniciar
        self.trabajos.append(pedido)
        return {}

    def get_transcription_job(self, TranscriptionJobName):
        self.consultas += 1
        estado = self.estados.pop(0) if len(self.estados) > 1 else self.estados[0]
        if isinstance(estado, Exception):
            raise estado
        info = {"TranscriptionJobName": TranscriptionJobName, "TranscriptionJobStatus": estado}
        if estado == "FAILED":
            info["FailureReason"] = self.motivo
        return {"TranscriptionJob": info}


class S3Falso:
    def __init__(self, texto=TEXTO):
        self.texto = texto
        self.subidos = {}
        self.leidos = []

    def put_object(self, Bucket, Key, Body, ContentType):
        self.subidos[Key] = {"bucket": Bucket, "cuerpo": Body, "tipo": ContentType}

    def get_object(self, Bucket, Key):
        self.leidos.append(Key)
        salida = {"jobName": "x", "results": {"transcripts": [{"transcript": self.texto}], "items": []}}
        return {"Body": io.BytesIO(json.dumps(salida).encode("utf-8"))}


class Reloj:
    """Reloj falso: `dormir` avanza el tiempo sin esperar."""

    def __init__(self):
        self.ahora = 0.0
        self.siestas = []

    def __call__(self):
        return self.ahora

    def dormir(self, segundos):
        self.siestas.append(segundos)
        self.ahora += segundos


def _cliente(transcribe=None, s3=None, bucket=BUCKET, tiempo_maximo=180.0):
    reloj = Reloj()
    cliente = ClienteTranscribe(
        bucket=bucket, intervalo=5.0, tiempo_maximo=tiempo_maximo,
        transcribe=transcribe or TranscribeFalso(), s3=s3 or S3Falso(), dormir=reloj.dormir, reloj=reloj,
    )
    return cliente, reloj


def _transcribir(cliente, audio=WEBM, frases=FRASES):
    return cliente.transcribir(audio, id_trabajo="kimun-captura-7-1", prefijo_vocabulario="kimun-curso-3", frases=frases)


# --- Formato ---------------------------------------------------------------------------


@pytest.mark.parametrize("cabecera, formato", [
    (WEBM, "webm"),
    (MP4_IPHONE, "mp4"),
    (b"\x00\x00\x00\x20ftypM4A " + bytes(8), "m4a"),
    (b"OggS\x00\x02" + bytes(8), "ogg"),
    (b"RIFF\x24\x00\x00\x00WAVEfmt ", "wav"),
    (b"ID3\x04" + bytes(8), "mp3"),
    (b"\xff\xfb\x90\x00" + bytes(8), "mp3"),
    (b"fLaC" + bytes(8), "flac"),
    (b"#!AMR\n" + bytes(8), "amr"),
])
def test_detecta_el_formato_por_los_primeros_bytes(cabecera, formato):
    assert formato_audio(cabecera) == formato


@pytest.mark.parametrize("cabecera", [b"%PDF-1.7\n%\xe2\xe3", b"\x89PNG\r\n\x1a\n\x00\x00", b"hola mundo!!", b""])
def test_lo_que_no_es_audio_no_tiene_formato(cabecera):
    assert formato_audio(cabecera) is None


# --- Vocabulario -----------------------------------------------------------------------


def test_el_vocabulario_usa_solo_caracteres_validos():
    frases = frases_vocabulario([
        "Rubí Contreras", "Rubí", "rubí", "Ñuñoa Müller", "JÜRGEN", "Ana-María 2", "Sofi R", "   ", "O'Higgins", "Zoë",
    ])

    assert frases and all(FRASE_VALIDA.match(f) for f in frases)
    assert "Rubí-Contreras" in frases  # las palabras se unen con guion
    assert [f for f in frases if f.casefold() == "rubí"] == ["Rubí"]  # sin repetir
    assert "Ñuñoa-Müller" in frases  # ñ y ü minúscula son válidas
    assert "JURGEN" in frases  # "Ü" no es válida: queda "U"
    assert "Ana-María" in frases  # los dígitos se omiten
    assert {"Sofi-R", "O'Higgins", "Zoe"} <= set(frases)


def test_el_vocabulario_tiene_orden_estable_y_su_nombre_cambia_si_cambian_los_ninos():
    assert frases_vocabulario(["Pedro", "Ana"]) == frases_vocabulario(["Ana", "Pedro"]) == ["Ana", "Pedro"]
    nombre = nombre_vocabulario("kimun-curso-3", ["Ana", "Pedro"])
    assert re.fullmatch(r"kimun-curso-3-[0-9a-f]{10}", nombre)
    assert nombre == nombre_vocabulario("kimun-curso-3", ["Ana", "Pedro"])
    assert nombre != nombre_vocabulario("kimun-curso-3", ["Ana", "Pedro", "Rubí"])


def test_un_frase_larga_se_corta_a_256():
    assert len(frases_vocabulario(["a" * 300])[0]) == 256


# --- Transcribir -----------------------------------------------------------------------


def test_transcripcion_exitosa_con_el_vocabulario_listo():
    transcribe, s3 = TranscribeFalso(estados=["QUEUED", "IN_PROGRESS", "COMPLETED"]), S3Falso()
    cliente, reloj = _cliente(transcribe, s3)

    assert _transcribir(cliente) == TEXTO

    (clave_audio, subido), = s3.subidos.items()
    assert clave_audio.startswith("originales/capturas/kimun-captura-7-1-") and clave_audio.endswith(".webm")
    assert subido == {"bucket": BUCKET, "cuerpo": WEBM, "tipo": "audio/webm"}
    trabajo, = transcribe.trabajos
    assert trabajo["TranscriptionJobName"].startswith("kimun-captura-7-1-")
    assert trabajo["LanguageCode"] == "es-US"
    assert trabajo["MediaFormat"] == "webm"
    assert trabajo["Media"] == {"MediaFileUri": f"s3://{BUCKET}/{clave_audio}"}
    assert trabajo["OutputBucketName"] == BUCKET
    assert trabajo["OutputKey"] == f"transcripciones/{trabajo['TranscriptionJobName']}.json"
    assert trabajo["Settings"] == {"VocabularyName": nombre_vocabulario("kimun-curso-3", FRASES)}
    assert s3.leidos == [trabajo["OutputKey"]]
    assert transcribe.consultas == 3 and reloj.siestas == [5.0, 5.0]


def test_el_audio_de_iphone_se_manda_como_mp4_sin_convertir():
    transcribe, s3 = TranscribeFalso(), S3Falso()
    cliente, _ = _cliente(transcribe, s3)
    _transcribir(cliente, audio=MP4_IPHONE)
    assert transcribe.trabajos[0]["MediaFormat"] == "mp4"
    assert next(iter(s3.subidos.values()))["tipo"] == "audio/mp4"


def test_si_el_vocabulario_no_existe_se_crea_y_se_transcribe_sin_el():
    transcribe = TranscribeFalso(vocabulario=None)
    cliente, _ = _cliente(transcribe)

    assert _transcribir(cliente) == TEXTO
    assert transcribe.creados == [{
        "VocabularyName": nombre_vocabulario("kimun-curso-3", FRASES), "LanguageCode": "es-US", "Phrases": FRASES,
    }]
    assert "Settings" not in transcribe.trabajos[0]


@pytest.mark.parametrize("estado", ["PENDING", "FAILED"])
def test_si_el_vocabulario_no_esta_listo_se_transcribe_sin_el(estado):
    transcribe = TranscribeFalso(vocabulario=estado)
    cliente, _ = _cliente(transcribe)
    assert _transcribir(cliente) == TEXTO
    assert transcribe.creados == [] and "Settings" not in transcribe.trabajos[0]


def test_un_problema_con_el_vocabulario_no_impide_transcribir(caplog):
    transcribe = TranscribeFalso(vocabulario=ErrorAws("AccessDeniedException"))
    cliente, _ = _cliente(transcribe)
    with caplog.at_level(logging.WARNING):
        assert _transcribir(cliente) == TEXTO
    assert "Settings" not in transcribe.trabajos[0]
    assert "AccessDeniedException" in caplog.text


def test_si_otro_proceso_ya_creo_el_vocabulario_no_se_avisa(caplog):
    transcribe = TranscribeFalso(vocabulario=None)
    transcribe.error_al_crear = ErrorAws("ConflictException")
    cliente, _ = _cliente(transcribe)
    with caplog.at_level(logging.WARNING):
        _transcribir(cliente)
    assert "ConflictException" not in caplog.text


def test_sin_ninos_no_se_usa_vocabulario():
    transcribe = TranscribeFalso(vocabulario=None)
    cliente, _ = _cliente(transcribe)
    _transcribir(cliente, frases=[])
    assert transcribe.creados == [] and "Settings" not in transcribe.trabajos[0]


def test_transcripcion_fallida():
    transcribe = TranscribeFalso(estados=["IN_PROGRESS", "FAILED"], motivo="The media format is invalid.")
    cliente, _ = _cliente(transcribe)
    with pytest.raises(ErrorTranscripcion, match="The media format is invalid."):
        _transcribir(cliente)


def test_transcripcion_que_no_termina_a_tiempo():
    transcribe = TranscribeFalso(estados=["IN_PROGRESS"])
    cliente, reloj = _cliente(transcribe, tiempo_maximo=30.0)
    with pytest.raises(ErrorTranscripcion, match="no terminó en 30 s"):
        _transcribir(cliente)
    assert reloj.ahora == 30.0 and transcribe.consultas == 7


def test_una_consulta_limitada_se_reintenta():
    transcribe = TranscribeFalso(estados=[ErrorAws("ThrottlingException"), "COMPLETED"])
    cliente, _ = _cliente(transcribe)
    assert _transcribir(cliente) == TEXTO


def test_un_error_al_consultar_que_no_es_transitorio_corta():
    transcribe = TranscribeFalso(estados=[ErrorAws("AccessDeniedException")])
    cliente, _ = _cliente(transcribe)
    with pytest.raises(ErrorTranscripcion, match="No se pudo consultar"):
        _transcribir(cliente)


def test_un_error_al_iniciar_queda_como_error_de_transcripcion():
    transcribe = TranscribeFalso()
    transcribe.error_al_iniciar = ErrorAws("AccessDeniedException")
    cliente, _ = _cliente(transcribe)
    with pytest.raises(ErrorTranscripcion, match="No se pudo iniciar"):
        _transcribir(cliente)


def test_sin_bucket_no_se_llama_a_aws():
    transcribe, s3 = TranscribeFalso(), S3Falso()
    cliente, _ = _cliente(transcribe, s3, bucket="")
    with pytest.raises(ErrorTranscripcion, match="KIMUN_BUCKET"):
        _transcribir(cliente)
    assert s3.subidos == {} and transcribe.trabajos == []


def test_un_archivo_que_no_es_audio_no_se_sube():
    transcribe, s3 = TranscribeFalso(), S3Falso()
    cliente, _ = _cliente(transcribe, s3)
    with pytest.raises(ErrorTranscripcion, match="formato de audio"):
        _transcribir(cliente, audio=b"%PDF-1.7 no es audio")
    assert s3.subidos == {} and transcribe.trabajos == []


def test_cada_intento_es_un_trabajo_con_otro_nombre():
    transcribe = TranscribeFalso()
    cliente, _ = _cliente(transcribe)
    _transcribir(cliente)
    _transcribir(cliente)
    primero, segundo = (t["TranscriptionJobName"] for t in transcribe.trabajos)
    assert primero != segundo


def test_el_bucket_sale_del_entorno(monkeypatch):
    monkeypatch.setenv("KIMUN_BUCKET", "bucket-del-entorno")
    assert ClienteTranscribe().bucket == "bucket-del-entorno"
