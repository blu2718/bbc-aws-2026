"""Captura por audio (PLAN.md, Task 9): subida, proceso de fondo, borrado del audio y revisión.

El audio solo se guarda mientras espera a ser transcrito: después se borra y queda el texto.
Transcribe y Bedrock se reemplazan por clientes falsos; los archivos van a una carpeta temporal.
"""
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse

from registro import forms
from registro.ia import ErrorBedrock, ErrorTranscripcion
from registro.models import Captura, Curso, NivelEducativo, Nino, Observacion
from registro.procesamiento import procesar, reintentar, tomar_siguiente
from registro.tests.ia.conftest import ClienteFalso

WEBM = b"\x1a\x45\xdf\xa3" + bytes(range(64))
MP4_IPHONE = b"\x00\x00\x00\x1cftypiso5" + bytes(64)
DICTADO = "Rubí cruzó el circuito sin ayuda"
CATALOGO = {
    "nivel_educativo": "transicion",
    "nucleos": [
        {"sigla": "IA", "nombre": "Identidad y Autonomía", "oas": []},
        {"sigla": "LV", "nombre": "Lenguaje Verbal", "oas": []},
        {"sigla": "PM", "nombre": "Pensamiento Matemático", "oas": []},
    ],
}


@pytest.fixture(autouse=True)
def _ajustes(settings, tmp_path):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.MEDIA_ROOT = tmp_path
    # Disco temporal aunque el entorno defina KIMUN_BUCKET.
    settings.STORAGES = {**settings.STORAGES, "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}


@pytest.fixture
def ninos(curso, nucleos):
    return {
        "Rubí": Nino.objects.create(curso=curso, nombre="Rubí Contreras", alias=["Rubi"], fecha_ingreso=date(2026, 3, 2)),
        "Pedro": Nino.objects.create(curso=curso, nombre="Pedro Salinas", fecha_ingreso=date(2026, 3, 2)),
    }


@pytest.fixture
def otro_curso(jardin, otra_educadora):
    return Curso.objects.create(
        jardin=jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora
    )


class TranscriptorFalso:
    """Reemplaza a ClienteTranscribe: devuelve textos predefinidos (o lanza) y guarda las llamadas."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.vocabularios = []

    def transcribir(self, audio, id_trabajo, prefijo_vocabulario=None, frases=()):
        self.llamadas.append({"audio": audio, "id_trabajo": id_trabajo, "prefijo": prefijo_vocabulario, "frases": list(frases)})
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    def asegurar_vocabulario(self, prefijo, frases):
        self.vocabularios.append((prefijo, list(frases)))
        return None


def _respuesta_bedrock(nombre="Rubí", cita=DICTADO):
    return {"observaciones": [{
        "nombre_detectado": nombre, "fecha": None, "cita_literal": cita, "interpretacion": None,
        "nucleos": ["IA"], "oas": [], "apoyo": "autonomo", "grupal": False,
    }]}


def _captura_audio(curso, autora, contenido=WEBM, **campos):
    return Captura.objects.create(
        curso=curso, autora=autora, tipo=Captura.Tipo.AUDIO,
        archivo=SimpleUploadedFile("audio-prueba.webm", contenido), **campos,
    )


def _subir(client, curso, contenido=WEBM, nombre="grabacion.webm", tipo="audio/webm"):
    archivo = SimpleUploadedFile(nombre, contenido, content_type=tipo)
    return client.post(reverse("capturar_audio", args=[curso.pk]), {"audio": archivo}, follow=True)


# --- Subir el audio --------------------------------------------------------------------


def test_la_pantalla_de_captura_tiene_el_formulario_de_audio(client, curso, educadora):
    client.force_login(educadora)
    html = client.get(reverse("capturar", args=[curso.pk])).content.decode()
    assert 'id="form-audio"' in html and 'enctype="multipart/form-data"' in html
    assert 'accept="audio/*"' in html and "registro/grabar.js" in html
    assert 'id="grabar"' in html and 'role="status"' in html


@pytest.mark.parametrize("quien", ["educadora", "asistente_del_curso"])
def test_la_educadora_y_la_asistente_suben_un_audio(client, request, curso, quien):
    usuaria = request.getfixturevalue(quien)
    client.force_login(usuaria)

    respuesta = _subir(client, curso)

    assert "Audio guardado." in respuesta.content.decode()
    captura = Captura.objects.get()
    assert (captura.tipo, captura.estado, captura.autora, captura.curso) == (Captura.Tipo.AUDIO, Captura.Estado.PENDIENTE, usuaria, curso)
    assert captura.archivo.name.endswith(".webm") and "grabacion" not in captura.archivo.name
    with captura.archivo.open("rb") as archivo:
        assert archivo.read() == WEBM


def test_el_audio_de_iphone_se_guarda_como_mp4(client, curso, educadora):
    client.force_login(educadora)
    _subir(client, curso, contenido=MP4_IPHONE, nombre="grabacion.mp4", tipo="audio/mp4")
    assert Captura.objects.get().archivo.name.endswith(".mp4")


def test_un_archivo_que_no_es_audio_se_rechaza_aunque_diga_que_lo_es(client, curso, educadora):
    client.force_login(educadora)
    respuesta = _subir(client, curso, contenido=b"%PDF-1.7 esto es un pdf", nombre="nota.webm")
    assert respuesta.status_code == 200
    assert "no es un audio compatible" in respuesta.content.decode()
    assert not Captura.objects.exists()


def test_un_audio_demasiado_grande_se_rechaza(client, curso, educadora, monkeypatch):
    monkeypatch.setattr(forms, "MAX_BYTES_AUDIO", 16)
    client.force_login(educadora)
    assert "pesa más de" in _subir(client, curso).content.decode()
    assert not Captura.objects.exists()


def test_sin_archivo_no_se_crea_captura(client, curso, educadora):
    client.force_login(educadora)
    respuesta = client.post(reverse("capturar_audio", args=[curso.pk]), {})
    assert respuesta.status_code == 200 and not Captura.objects.exists()


@pytest.mark.parametrize("quien", ["otra_educadora", "directora_del_jardin"])
def test_quien_no_registra_en_el_curso_recibe_404(client, request, curso, quien):
    client.force_login(request.getfixturevalue(quien))
    assert _subir(client, curso).status_code == 404
    assert not Captura.objects.exists()


def test_subir_pide_login(client, curso):
    respuesta = client.post(reverse("capturar_audio", args=[curso.pk]), {})
    assert respuesta.status_code == 302 and reverse("login") in respuesta["Location"]


# --- Proceso de fondo ------------------------------------------------------------------


def test_el_audio_se_transcribe_y_se_separa_en_observaciones(curso, educadora, ninos):
    _captura_audio(curso, educadora)
    transcriptor, bedrock = TranscriptorFalso(DICTADO), ClienteFalso(_respuesta_bedrock())

    captura = tomar_siguiente()
    creadas = procesar(captura, cliente=bedrock, catalogo=CATALOGO, transcriptor=transcriptor)

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA
    assert captura.texto_extraido == DICTADO
    obs, = creadas
    assert (obs.nino, obs.cita, obs.estado) == (ninos["Rubí"], DICTADO, Observacion.Estado.PENDIENTE)
    llamada, = transcriptor.llamadas
    assert llamada["audio"] == WEBM
    assert llamada["id_trabajo"] == f"kimun-captura-{captura.pk}-1"
    assert llamada["prefijo"] == f"kimun-curso-{curso.pk}"
    assert {"Rubí", "Rubí-Contreras", "Rubi", "Pedro", "Pedro-Salinas"} <= set(llamada["frases"])
    assert DICTADO in bedrock.llamadas[0]["mensaje"]


def test_si_falla_la_transcripcion_la_captura_queda_con_error_y_se_puede_reintentar(curso, educadora, ninos):
    _captura_audio(curso, educadora)
    transcriptor = TranscriptorFalso(ErrorTranscripcion("La transcripción no terminó en 180 s."), DICTADO)

    captura = tomar_siguiente()
    assert procesar(captura, cliente=ClienteFalso(), catalogo=CATALOGO, transcriptor=transcriptor) is None
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR
    assert "no terminó" in captura.error and captura.texto_extraido == ""

    assert reintentar(captura)
    captura = tomar_siguiente()
    assert procesar(captura, cliente=ClienteFalso(_respuesta_bedrock()), catalogo=CATALOGO, transcriptor=transcriptor)
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA and captura.intentos == 2
    assert transcriptor.llamadas[1]["id_trabajo"].endswith("-2")


def test_si_falla_bedrock_al_reintentar_no_se_vuelve_a_transcribir(curso, educadora, ninos):
    _captura_audio(curso, educadora)
    transcriptor = TranscriptorFalso(DICTADO)  # una sola respuesta: una segunda llamada fallaría

    captura = tomar_siguiente()
    bedrock_caido = ClienteFalso(ErrorBedrock("Bedrock falló 3 veces"))
    assert procesar(captura, cliente=bedrock_caido, catalogo=CATALOGO, transcriptor=transcriptor) is None
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR and captura.texto_extraido == DICTADO

    reintentar(captura)
    captura = tomar_siguiente()
    assert procesar(captura, cliente=ClienteFalso(_respuesta_bedrock()), catalogo=CATALOGO, transcriptor=transcriptor)
    assert len(transcriptor.llamadas) == 1


def test_la_pantalla_avisa_que_el_audio_no_se_guarda(client, curso, educadora):
    client.force_login(educadora)
    html = client.get(reverse("capturar", args=[curso.pk])).content.decode()
    assert "El audio no se guarda: se borra apenas se transcribe" in html


def test_un_audio_sin_archivo_queda_con_error(curso, educadora, ninos):
    Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.AUDIO)
    captura = tomar_siguiente()
    assert procesar(captura, cliente=ClienteFalso(), catalogo=CATALOGO, transcriptor=TranscriptorFalso()) is None
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR and "no tiene archivo" in captura.error


def test_el_comando_procesa_audios(curso, educadora, ninos, capsys):
    _captura_audio(curso, educadora)
    call_command(
        "procesar_capturas", "--una-vez",
        cliente=ClienteFalso(_respuesta_bedrock()), catalogo=CATALOGO, transcriptor=TranscriptorFalso(DICTADO),
    )
    assert "1 observaciones pendientes (0 sin niño)" in capsys.readouterr().out
    assert Captura.objects.get().estado == Captura.Estado.PROCESADA


def test_preparar_vocabularios_crea_el_de_cada_curso_con_ninos(curso, ninos, otro_curso, capsys):
    transcriptor = TranscriptorFalso()
    call_command("preparar_vocabularios", transcriptor=transcriptor)

    (prefijo, frases), = transcriptor.vocabularios
    assert prefijo == f"kimun-curso-{curso.pk}" and "Rubí" in frases
    salida = capsys.readouterr().out
    assert "Transición B (Jardín de prueba): sin niños" in salida and "creándose" in salida


# --- El audio no se conserva -----------------------------------------------------------


def _archivos(carpeta):
    return [p for p in carpeta.rglob("*") if p.is_file()]


def test_al_transcribir_se_guarda_el_texto_y_se_borra_el_audio(curso, educadora, ninos, tmp_path):
    _captura_audio(curso, educadora)
    assert len(_archivos(tmp_path)) == 1

    captura = tomar_siguiente()
    procesar(captura, cliente=ClienteFalso(_respuesta_bedrock()), catalogo=CATALOGO, transcriptor=TranscriptorFalso(DICTADO))

    captura.refresh_from_db()
    assert captura.texto_extraido == DICTADO
    assert not captura.archivo and _archivos(tmp_path) == []


def test_si_falla_la_transcripcion_el_audio_se_conserva_para_reintentar(curso, educadora, ninos, tmp_path):
    _captura_audio(curso, educadora)
    captura = tomar_siguiente()
    procesar(captura, cliente=ClienteFalso(), catalogo=CATALOGO,
             transcriptor=TranscriptorFalso(ErrorTranscripcion("La transcripción no terminó en 180 s.")))

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR and captura.archivo
    assert len(_archivos(tmp_path)) == 1


def test_si_falla_bedrock_el_audio_ya_esta_borrado(curso, educadora, ninos, tmp_path):
    _captura_audio(curso, educadora)
    captura = tomar_siguiente()
    procesar(captura, cliente=ClienteFalso(ErrorBedrock("Bedrock falló 3 veces")), catalogo=CATALOGO,
             transcriptor=TranscriptorFalso(DICTADO))

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR and captura.texto_extraido == DICTADO
    assert not captura.archivo and _archivos(tmp_path) == []


def test_un_archivo_que_no_es_audio_se_borra_y_queda_en_error_sin_transcribir(curso, educadora, ninos, tmp_path):
    _captura_audio(curso, educadora, contenido=b"%PDF-1.7 no es audio")
    transcriptor = TranscriptorFalso()

    captura = tomar_siguiente()
    assert procesar(captura, cliente=ClienteFalso(), catalogo=CATALOGO, transcriptor=transcriptor) is None

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR and "Archivo inválido" in captura.error
    assert transcriptor.llamadas == []
    assert not captura.archivo and _archivos(tmp_path) == []


def test_la_carpeta_de_archivos_no_se_sirve(client, curso, educadora):
    captura = _captura_audio(curso, educadora)
    client.force_login(educadora)
    assert client.get(f"/media/{captura.archivo.name}").status_code == 404


# --- Revisión y lista de capturas ------------------------------------------------------


def test_la_revision_muestra_la_transcripcion_sin_el_audio(client, curso, educadora, ninos):
    captura = Captura.objects.create(
        curso=curso, autora=educadora, tipo=Captura.Tipo.AUDIO, estado=Captura.Estado.PROCESADA, texto_extraido=DICTADO
    )
    Observacion.objects.create(captura=captura, nino=ninos["Rubí"], fecha=date(2026, 10, 15), cita=DICTADO)
    client.force_login(educadora)

    html = client.get(reverse("revision", args=[curso.pk])).content.decode()

    assert "Ver la transcripción" in html and DICTADO in html
    assert "<audio" not in html and "original" not in html.lower()


def test_la_lista_de_capturas_muestra_el_audio_con_su_transcripcion(client, curso, educadora):
    Captura.objects.create(
        curso=curso, autora=educadora, tipo=Captura.Tipo.AUDIO, estado=Captura.Estado.PROCESADA, texto_extraido=DICTADO
    )
    client.force_login(educadora)
    html = client.get(reverse("capturar", args=[curso.pk])).content.decode()
    assert f"Audio: «{DICTADO}»" in html
