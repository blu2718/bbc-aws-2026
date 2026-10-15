"""Captura por foto (PLAN.md, Task 8): subida, lectura, borrado de la foto y proceso de fondo.

La foto solo se guarda mientras espera a ser leída: apenas se lee, se borra y queda
el texto. Los archivos van a un MEDIA_ROOT temporal, nunca al repo. Bedrock se
reemplaza por un cliente falso.
"""
import re

import pytest
from django.conf import settings as ajustes
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from registro.ia import ErrorBedrock, ErrorTranscripcion
from registro.ia.foto import TAMANO_MAXIMO
from registro.lectura import texto_para_separar
from registro.models import Captura, NivelEducativo, Observacion, ruta_original
from registro.procesamiento import reintentar
from registro.tests.ia.conftest import ClienteFalso

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
LEIDO = "Pedro y Nayara clasificaron hojas por color [ilegible]"


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    """Disco temporal aunque el entorno defina KIMUN_BUCKET. Devuelve la carpeta."""
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.STORAGES = {**settings.STORAGES, "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}
    return settings.MEDIA_ROOT


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def _archivos(media):
    """Archivos que quedan guardados (no carpetas)."""
    return [p for p in media.rglob("*") if p.is_file()] if media.exists() else []


def _subir(client, curso, contenido=JPEG, nombre="sofia-rojas-postit.jpg", tipo="image/jpeg"):
    archivo = SimpleUploadedFile(nombre, contenido, content_type=tipo)
    return client.post(reverse("capturar_foto", args=[curso.pk]), {"foto": archivo})


def _captura_con_foto(curso, autora, contenido=JPEG, extension="jpg", **campos):
    captura = Captura(curso=curso, autora=autora, tipo=Captura.Tipo.FOTO, **campos)
    captura.archivo.save(f"foto.{extension}", ContentFile(contenido), save=False)
    captura.save()
    return captura


# --- Ruta del archivo mientras espera ser leído --------------------------------------


def test_la_ruta_no_conserva_el_nombre_original():
    ruta = ruta_original(None, "Sofía Rojas post-it.JPG")
    assert re.fullmatch(r"originales/\d{4}/\d{2}/[0-9a-f]{32}\.jpg", ruta)
    assert ruta_original(None, "foto.jpg") != ruta_original(None, "foto.jpg")


@pytest.mark.parametrize("nombre", ["sin-extension", "raro.j p g", "../../etc/passwd", "x.extensionlarga", ""])
def test_una_extension_rara_se_omite(nombre):
    assert re.fullmatch(r"originales/\d{4}/\d{2}/[0-9a-f]{32}", ruta_original(None, nombre))


# --- Subir una foto -------------------------------------------------------------------


def test_la_educadora_sube_una_foto_y_queda_pendiente(client, curso, educadora):
    client.force_login(educadora)

    respuesta = _subir(client, curso)

    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("capturar", args=[curso.pk])
    captura = Captura.objects.get()
    assert (captura.curso, captura.autora, captura.tipo, captura.estado) == (
        curso, educadora, Captura.Tipo.FOTO, Captura.Estado.PENDIENTE
    )
    assert re.fullmatch(r"originales/\d{4}/\d{2}/[0-9a-f]{32}\.jpg", captura.archivo.name)
    assert "sofia" not in captura.archivo.name
    with captura.archivo.open("rb") as archivo:
        assert archivo.read() == JPEG


def test_la_subida_no_deja_copias_temporales_en_disco():
    """Django guarda en memoria las subidas hasta FILE_UPLOAD_MAX_MEMORY_SIZE; por sobre eso, en /tmp."""
    assert ajustes.FILE_UPLOAD_MAX_MEMORY_SIZE >= TAMANO_MAXIMO


def test_la_extension_sale_del_contenido_y_no_del_nombre(client, curso, educadora):
    client.force_login(educadora)
    _subir(client, curso, contenido=PNG, nombre="foto.jpg", tipo="image/jpeg")
    assert Captura.objects.get().archivo.name.endswith(".png")


def test_la_asistente_del_curso_puede_subir(client, curso, asistente_del_curso):
    client.force_login(asistente_del_curso)
    assert _subir(client, curso).status_code == 302
    assert Captura.objects.get().autora == asistente_del_curso


@pytest.mark.parametrize("quien", ["directora_del_jardin", "otra_educadora", "asistente"])
def test_quien_no_registra_en_el_curso_recibe_404(client, request, curso, quien, media):
    client.force_login(request.getfixturevalue(quien))
    assert _subir(client, curso).status_code == 404
    assert not Captura.objects.exists()
    assert _archivos(media) == []


def test_subir_una_foto_pide_login(client, curso):
    respuesta = _subir(client, curso)
    assert respuesta.status_code == 302
    assert reverse("login") in respuesta["Location"]
    assert not Captura.objects.exists()


def test_subir_una_foto_solo_por_post(client, curso, educadora):
    client.force_login(educadora)
    assert client.get(reverse("capturar_foto", args=[curso.pk])).status_code == 405


@pytest.mark.parametrize(
    "contenido, nombre, mensaje",
    [
        (b"%PDF-1.7 no es una foto", "nota.jpg", "JPEG, PNG, GIF o WebP"),
        (b"\x00\x00\x00\x18ftypheic" + b"\x00" * 50, "IMG_0001.HEIC", "JPEG, PNG, GIF o WebP"),
        (b"<script>alert(1)</script>", "foto.png", "JPEG, PNG, GIF o WebP"),
    ],
)
def test_se_rechaza_un_archivo_de_tipo_invalido(client, curso, educadora, media, contenido, nombre, mensaje):
    client.force_login(educadora)

    respuesta = _subir(client, curso, contenido=contenido, nombre=nombre)

    assert respuesta.status_code == 200
    assert mensaje in respuesta.content.decode()
    assert not Captura.objects.exists()
    assert _archivos(media) == []


def test_se_rechaza_una_foto_demasiado_grande(client, curso, educadora, media):
    client.force_login(educadora)

    respuesta = _subir(client, curso, contenido=JPEG[:4] + b"\x00" * TAMANO_MAXIMO)

    assert respuesta.status_code == 200
    assert "el máximo es 3,75 MB" in respuesta.content.decode()
    assert not Captura.objects.exists()
    assert _archivos(media) == []


def test_sin_foto_pide_una(client, curso, educadora):
    client.force_login(educadora)
    respuesta = client.post(reverse("capturar_foto", args=[curso.pk]), {})
    assert respuesta.status_code == 200
    assert "Toma o elige una foto." in respuesta.content.decode()


def test_la_pantalla_trae_la_camara_junto_a_la_nota_y_avisa_que_la_foto_se_borra(client, curso, educadora):
    client.force_login(educadora)

    html = client.get(reverse("capturar", args=[curso.pk])).content.decode()

    # La misma pantalla de la nota escrita (Task 5) trae el formulario de foto.
    assert 'name="texto"' in html
    assert f'action="{reverse("capturar_foto", args=[curso.pk])}"' in html
    assert 'accept="image/*"' in html and 'capture="environment"' in html
    assert 'enctype="multipart/form-data"' in html
    assert "captura_foto.js" in html
    assert "se borra apenas se lee" in html


def test_una_foto_invalida_muestra_el_error_sin_perder_la_pantalla(client, curso, educadora):
    client.force_login(educadora)
    html = _subir(client, curso, contenido=b"%PDF-1.7", nombre="nota.jpg").content.decode()
    assert "JPEG, PNG, GIF o WebP" in html
    assert 'name="texto"' in html and "Tus últimas notas" not in html


# --- La foto no se muestra en ninguna parte ----------------------------------------------


def test_la_carpeta_de_archivos_no_se_sirve(client, curso, educadora):
    captura = _captura_con_foto(curso, educadora)
    client.force_login(educadora)
    assert client.get(f"/{ajustes.MEDIA_URL}{captura.archivo.name}").status_code == 404


def test_la_revision_muestra_lo_leido_pero_no_la_foto(client, curso, educadora):
    captura = Captura.objects.create(
        curso=curso, autora=educadora, tipo=Captura.Tipo.FOTO, texto_extraido=LEIDO, estado=Captura.Estado.PROCESADA
    )
    Observacion.objects.create(captura=captura, fecha=timezone.localdate(), cita=LEIDO, nombre_detectado="Pedro")
    client.force_login(educadora)

    html = client.get(reverse("revision", args=[curso.pk])).content.decode()

    assert "Ver lo leído de la foto" in html and LEIDO in html
    assert "<img" not in html.split('id="revision-contenido"')[1]
    assert "original" not in html.lower()


def test_la_lista_de_capturas_muestra_lo_leido_sin_enlace_a_la_foto(client, curso, educadora):
    _captura_con_foto(curso, educadora)  # pendiente: todavía tiene foto
    Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.FOTO, texto_extraido=LEIDO,
                           estado=Captura.Estado.PROCESADA)
    client.force_login(educadora)

    html = client.get(reverse("capturas_recientes", args=[curso.pk])).content.decode()

    assert "Foto ·" in html and LEIDO[:40] in html
    assert "original" not in html.lower() and ajustes.MEDIA_URL not in html


# --- Lectura y borrado ------------------------------------------------------------------


def test_al_leer_la_foto_se_guarda_el_texto_y_se_borra_la_foto(curso, educadora, media):
    captura = _captura_con_foto(curso, educadora)
    assert len(_archivos(media)) == 1
    cliente = ClienteFalso({"texto": "Pedro y Emilio clasificaron hojas por color"})

    texto = texto_para_separar(captura, cliente=cliente)

    assert texto == "Pedro y Emilio clasificaron hojas por color"
    assert cliente.llamadas[0]["imagenes"] == [("jpeg", JPEG)]
    captura.refresh_from_db()
    assert captura.texto_extraido == texto
    assert not captura.archivo and captura.archivo.name == ""
    assert _archivos(media) == []


def test_una_foto_sin_texto_legible_tambien_se_borra(curso, educadora, media):
    captura = _captura_con_foto(curso, educadora)
    assert texto_para_separar(captura, cliente=ClienteFalso({"texto": "  "})) == ""
    captura.refresh_from_db()
    assert not captura.archivo and _archivos(media) == []


def test_si_falla_la_lectura_la_foto_se_conserva_para_reintentar(curso, educadora, media):
    captura = _captura_con_foto(curso, educadora)
    with pytest.raises(ErrorTranscripcion):
        texto_para_separar(captura, cliente=ClienteFalso(ErrorBedrock("ThrottlingException", "ThrottlingException")))
    captura.refresh_from_db()
    assert captura.texto_extraido == "" and captura.archivo
    assert len(_archivos(media)) == 1


def test_si_falla_el_borrado_el_texto_no_se_pierde_y_se_borra_en_la_siguiente_vuelta(
    curso, educadora, media, monkeypatch
):
    captura = _captura_con_foto(curso, educadora)
    borrar = FileSystemStorage.delete

    def fallar(self, name):
        raise OSError("disco ocupado")

    monkeypatch.setattr(FileSystemStorage, "delete", fallar)
    assert texto_para_separar(captura, cliente=ClienteFalso({"texto": LEIDO})) == LEIDO
    captura.refresh_from_db()
    assert captura.texto_extraido == LEIDO and captura.archivo
    assert len(_archivos(media)) == 1

    monkeypatch.setattr(FileSystemStorage, "delete", borrar)
    cliente = ClienteFalso()
    assert texto_para_separar(captura, cliente=cliente) == LEIDO
    captura.refresh_from_db()
    assert not captura.archivo and _archivos(media) == []
    assert cliente.llamadas == []  # no se vuelve a leer


def test_una_nota_escrita_no_llama_al_modelo(curso, educadora):
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="nota")
    cliente = ClienteFalso()
    assert texto_para_separar(captura, cliente=cliente) == "nota"
    assert cliente.llamadas == []


# --- Proceso de fondo: foto → lectura → borrado → separación → observaciones pendientes ------

CATALOGO = {
    "nivel_educativo": "transicion",
    "nucleos": [
        {"sigla": "IA", "nombre": "Identidad y Autonomía", "oas": []},
        {"sigla": "LV", "nombre": "Lenguaje Verbal", "oas": []},
        {"sigla": "PM", "nombre": "Pensamiento Matemático",
         "oas": [{"numero": 2, "codigo": "OA 2 PM", "texto": "Clasificar por atributos."}]},
    ],
}


@pytest.fixture
def ninos(curso, nucleos):
    from datetime import date

    from registro.models import Nino, ObjetivoAprendizaje

    _ia, _lv, pm = nucleos
    ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=pm, numero=2,
                                       texto="Clasificar por atributos.")
    return {
        "Pedro": Nino.objects.create(curso=curso, nombre="Pedro Salinas", fecha_ingreso=date(2026, 3, 2)),
        "Naiara": Nino.objects.create(curso=curso, nombre="Naiara Fuentes", alias=["Nayara"],
                                      fecha_ingreso=date(2026, 3, 2)),
    }


def _separadas(*nombres):
    return {"observaciones": [
        {"nombre_detectado": n, "fecha": None, "cita_literal": LEIDO, "interpretacion": None,
         "nucleos": ["PM"], "oas": ["OA 2 PM"], "apoyo": "autonomo", "grupal": False}
        for n in nombres
    ]}


def _procesar(cliente):
    call_command("procesar_capturas", una_vez=True, cliente=cliente, catalogo=CATALOGO, verbosity=0)


def test_procesar_capturas_lee_la_foto_la_borra_y_crea_observaciones_pendientes(curso, educadora, ninos, media):
    captura = _captura_con_foto(curso, educadora)
    cliente = ClienteFalso({"texto": LEIDO}, _separadas("Pedro", "Nayara"))

    _procesar(cliente)

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA and captura.texto_extraido == LEIDO
    assert not captura.archivo and _archivos(media) == []
    # Primero la lectura (con la foto), después la separación del texto leído (sin foto).
    assert cliente.llamadas[0]["imagenes"] == [("jpeg", JPEG)]
    assert cliente.llamadas[1]["imagenes"] == [] and LEIDO in cliente.llamadas[1]["mensaje"]
    creadas = list(captura.observaciones.order_by("id"))
    assert [o.nino for o in creadas] == [ninos["Pedro"], ninos["Naiara"]]
    assert all(o.estado == Observacion.Estado.PENDIENTE and "[ilegible]" in o.cita for o in creadas)


def test_si_falla_la_separacion_la_foto_ya_esta_borrada_y_el_reintento_usa_el_texto(curso, educadora, ninos, media):
    captura = _captura_con_foto(curso, educadora)
    _procesar(ClienteFalso({"texto": LEIDO}, ErrorBedrock("ThrottlingException", "ThrottlingException")))
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR and captura.texto_extraido == LEIDO
    assert not captura.archivo and _archivos(media) == []

    assert reintentar(captura)
    cliente = ClienteFalso(_separadas("Pedro"))
    _procesar(cliente)

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA
    assert len(cliente.llamadas) == 1 and cliente.llamadas[0]["imagenes"] == []


def test_si_falla_la_lectura_la_captura_queda_en_error_con_la_foto_para_reintentar(curso, educadora, ninos, media):
    captura = _captura_con_foto(curso, educadora)
    _procesar(ClienteFalso(ErrorBedrock("ServiceUnavailableException", "ServiceUnavailableException")))

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR and captura.texto_extraido == ""
    assert not captura.observaciones.exists()
    assert captura.archivo and len(_archivos(media)) == 1

    assert reintentar(captura)
    _procesar(ClienteFalso({"texto": LEIDO}, _separadas("Pedro")))
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA and _archivos(media) == []


def test_un_archivo_que_no_es_foto_se_borra_y_queda_en_error_sin_llamar_al_modelo(curso, educadora, ninos, media):
    captura = _captura_con_foto(curso, educadora, contenido=b"%PDF-1.7", extension="jpg")
    cliente = ClienteFalso()

    _procesar(cliente)

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR and "Archivo inválido" in captura.error
    assert cliente.llamadas == []
    assert not captura.archivo and _archivos(media) == []


def test_borrar_una_captura_pendiente_borra_su_foto(curso, educadora, media):
    captura = _captura_con_foto(curso, educadora)
    assert len(_archivos(media)) == 1
    captura.delete()
    assert _archivos(media) == []


def test_borrar_el_curso_borra_las_fotos_pendientes(curso, educadora, media):
    _captura_con_foto(curso, educadora)
    _captura_con_foto(curso, educadora)
    curso.delete()
    assert _archivos(media) == []
