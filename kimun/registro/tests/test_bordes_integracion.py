"""Casos borde en los límites entre formularios, vistas y procesamiento."""
import importlib
from datetime import timedelta

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.urls import reverse
from django.utils import timezone

from registro import lectura, procesamiento
from registro.forms_registro import LARGO_TEXTO, RegistroForm
from registro.models import (
    Captura, Curso, DescriptorNivel, NivelEducativo, Nino, ObjetivoAprendizaje, Rubrica,
)
from registro.radar import EjeRadar, svg_radar
from registro.rubrica import NIVELES_PROVISORIOS
from registro.tests.test_capturas import ClienteFalso, JPEG, WEBM


@pytest.fixture(autouse=True)
def entorno_aislado(settings, tmp_path):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.MEDIA_ROOT = tmp_path
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    }


def test_post_totalmente_vacio_muestra_validacion(client, curso, educadora):
    client.force_login(educadora)
    respuesta = client.post(reverse("registrar", args=[curso.pk]), {})
    assert respuesta.status_code == 400
    assert "Escribe lo que pasó" in respuesta.content.decode()
    assert not Captura.objects.exists()


@pytest.mark.parametrize("largo,valido", [(LARGO_TEXTO, True), (LARGO_TEXTO + 1, False)])
def test_limite_de_texto(largo, valido):
    assert RegistroForm({"texto": "x" * largo}).is_valid() is valido


def test_foto_y_audio_juntos_no_crean_captura(client, curso, educadora):
    client.force_login(educadora)
    respuesta = client.post(reverse("registrar", args=[curso.pk]), {
        "foto": SimpleUploadedFile("nota.jpg", JPEG),
        "audio": SimpleUploadedFile("nota.webm", WEBM),
    })
    assert respuesta.status_code == 400
    assert "por separado" in respuesta.content.decode()
    assert not Captura.objects.exists()


@pytest.mark.parametrize("tipo", [Captura.Tipo.FOTO, Captura.Tipo.AUDIO])
@pytest.mark.parametrize("ya_leida", [False, True])
def test_nota_junto_al_archivo_llega_a_separacion(curso, educadora, monkeypatch, tipo, ya_leida):
    extraido = "Pedro clasificó hojas."
    nota = "Fue ayer en el patio, con ayuda."
    captura = Captura.objects.create(
        curso=curso, autora=educadora, tipo=tipo, texto_original=nota,
        texto_extraido=extraido if ya_leida else "",
    )
    if not ya_leida:
        captura.archivo.save("nota.jpg" if tipo == Captura.Tipo.FOTO else "nota.webm",
                             ContentFile(JPEG if tipo == Captura.Tipo.FOTO else WEBM))
    monkeypatch.setattr(lectura, "transcribir_foto", lambda *a, **kw: extraido)

    class Transcriptor:
        def transcribir(self, *args, **kwargs):
            return extraido

    cliente = ClienteFalso({"observaciones": []})
    assert procesamiento.tomar(captura.pk)
    assert procesamiento.procesar(captura, cliente=cliente, transcriptor=Transcriptor()) == []
    mensaje = cliente.llamadas[-1]["mensaje"]
    assert extraido in mensaje and nota in mensaje
    captura.refresh_from_db()
    assert captura.texto_extraido == extraido  # No mezclar la nota con el OCR almacenado.
    assert not captura.archivo
    # Una nueva lectura usa el texto guardado sin repetir ni perder el contexto.
    assert lectura.texto_para_separar(captura).count(nota) == 1


@pytest.mark.parametrize("tipo", [Captura.Tipo.FOTO, Captura.Tipo.AUDIO])
def test_contexto_agregado_a_un_archivo_leido_llega_a_la_ia(client, curso, educadora, tipo):
    captura = Captura.objects.create(
        curso=curso, autora=educadora, tipo=tipo, texto_extraido="Pedro saltó.",
        estado=Captura.Estado.PROCESADA, pregunta="¿Dónde?",
    )
    client.force_login(educadora)
    respuesta = client.post(reverse("captura_contexto", args=[captura.pk]), {"contexto": "En el patio."})
    assert respuesta.status_code == 302
    captura.refresh_from_db()
    cliente = ClienteFalso({"observaciones": []})
    assert procesamiento.tomar(captura.pk)
    assert procesamiento.procesar(captura, cliente=cliente) == []
    assert "Contexto agregado: En el patio." in cliente.llamadas[-1]["mensaje"]


@pytest.mark.parametrize("fecha", ["0001-01-01", "0001-01-15", "2024-02-29", "9999-12-31", "2026-02-30", "basura"])
def test_fechas_extremas_no_rompen_la_tabla(client, curso, educadora, fecha):
    client.force_login(educadora)
    respuesta = client.get(reverse("curso", args=[curso.pk]), {"quincena": fecha})
    assert respuesta.status_code == 200


def test_reintento_con_objeto_obsoleto_no_recupera_un_trabajo_recien_tomado(curso, educadora):
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO,
                                     texto_original="Pedro saltó.", estado=Captura.Estado.PROCESANDO)
    antigua = timezone.now() - procesamiento.UMBRAL_PROCESANDO_ATASCADA - timedelta(seconds=1)
    Captura.objects.filter(pk=captura.pk).update(actualizada=antigua)
    captura.refresh_from_db()
    assert procesamiento.reintentar_errores() == 1
    assert procesamiento.tomar(captura.pk)  # Otro worker acaba de tomar el trabajo.
    assert not procesamiento.reintentar_desde_la_pagina(captura)
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESANDO


def test_un_curso_de_un_nivel_sin_rubrica_no_rompe_sus_paginas(client, jardin, educadora, rubrica):
    """Un curso de medio creado en el panel antes de cargar su currículo parte con la rúbrica provisoria."""
    curso = Curso.objects.create(jardin=jardin, nombre="Medio A", nivel_educativo=NivelEducativo.MEDIO,
                                 educadora=educadora)
    nino = Nino.objects.create(curso=curso, nombre="Gael Pino", fecha_ingreso=timezone.localdate())
    assert Rubrica.nivel_maximo(NivelEducativo.MEDIO) == NIVELES_PROVISORIOS
    client.force_login(educadora)
    for url in (reverse("curso", args=[curso.pk]), reverse("registrar", args=[curso.pk]),
                reverse("ficha", args=[nino.pk]), reverse("metas", args=[curso.pk])):
        assert client.get(url).status_code == 200, url


def test_la_migracion_crea_rubricas_y_descriptores_provisorios_faltantes(db, jardin, educadora, nucleos):
    from django.apps import apps

    migracion = importlib.import_module("registro.migrations.0009_rubricas_provisorias_por_nivel")
    curso = Curso.objects.create(jardin=jardin, nombre="Sala Cuna A", nivel_educativo=NivelEducativo.SALA_CUNA,
                                 educadora=educadora)
    ia, lv, _pm = nucleos
    ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.SALA_CUNA, nucleo=lv, numero=1, texto="Balbucear")
    DescriptorNivel.objects.create(nivel_educativo=NivelEducativo.SALA_CUNA, nucleo=ia, nivel=1, descripcion="Integra",
                                   provisorio=False)
    Rubrica.objects.filter(nivel_educativo=curso.nivel_educativo).delete()  # como en una base anterior al fix

    migracion.crear_rubricas(apps, None)
    migracion.crear_rubricas(apps, None)  # repetirla no duplica

    assert Rubrica.nivel_maximo(NivelEducativo.SALA_CUNA) == NIVELES_PROVISORIOS
    lv_sala_cuna = DescriptorNivel.objects.filter(nivel_educativo=NivelEducativo.SALA_CUNA, nucleo=lv)
    assert sorted(lv_sala_cuna.values_list("nivel", flat=True)) == list(range(1, NIVELES_PROVISORIOS + 1))
    assert all(d.provisorio for d in lv_sala_cuna)
    # No pisa descriptores existentes ni crea en núcleos sin OA en el nivel.
    assert DescriptorNivel.objects.filter(nivel_educativo=NivelEducativo.SALA_CUNA, nucleo=ia).count() == 1
    assert not DescriptorNivel.objects.filter(nivel_educativo=NivelEducativo.SALA_CUNA, nucleo=_pm).exists()


def test_la_migracion_acorta_el_nivel_1_provisorio_sin_pisar_los_editados(rubrica, nucleos):
    from django.apps import apps

    migracion = importlib.import_module("registro.migrations.0013_rubrica_provisoria_nivel_1_corto")
    ia, lv, pm = nucleos
    for nucleo in nucleos:
        nucleo.esperado_inicio_nt1 = f"Al iniciar NT1, en {nucleo.nombre}…"
        nucleo.save()
    antiguo = {n.sigla: f"Muestra lo esperado al iniciar NT1. {n.esperado_inicio_nt1}" for n in nucleos}
    crear = DescriptorNivel.objects.create
    crear(nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, nivel=1, descripcion=antiguo["LV"])
    crear(nivel_educativo=NivelEducativo.TRANSICION, nucleo=pm, nivel=1, descripcion="Editado a mano")
    crear(nivel_educativo=NivelEducativo.TRANSICION, nucleo=ia, nivel=1, descripcion=antiguo["IA"], provisorio=False)

    migracion.acortar(apps, None)
    migracion.acortar(apps, None)  # repetirla no cambia nada

    def nivel_1(nucleo):
        return DescriptorNivel.objects.get(nivel_educativo=NivelEducativo.TRANSICION, nucleo=nucleo, nivel=1)

    assert (nivel_1(lv).descripcion, nivel_1(lv).conducta) == (
        f"Muestra lo esperado al iniciar NT1. Núcleo: {lv.nombre}.", lv.esperado_inicio_nt1)
    assert (nivel_1(pm).descripcion, nivel_1(pm).conducta) == ("Editado a mano", "")
    assert (nivel_1(ia).descripcion, nivel_1(ia).conducta) == (antiguo["IA"], "")  # no es provisorio

    migracion.alargar(apps, None)
    assert (nivel_1(lv).descripcion, nivel_1(lv).conducta) == (antiguo["LV"], "")


def test_radar_con_mediana_decimal_sobre_el_maximo():
    """Si la rúbrica se achicó, la mediana del curso puede quedar en x,5 sobre el máximo."""
    ejes = [EjeRadar("IA", "Identidad", 3, "3", mediana=9.5), EjeRadar("LV", "Lenguaje", 2, "2"),
            EjeRadar("PM", "Pensamiento", None, "Sin nivel validado")]
    assert svg_radar(ejes, nivel_maximo=8).startswith("<svg")


@pytest.mark.parametrize("intervalo", [float("nan"), float("inf"), -1, 0])
def test_worker_rechaza_intervalos_invalidos_antes_de_procesar(db, intervalo):
    with pytest.raises(CommandError, match="--intervalo"):
        call_command("procesar_capturas", una_vez=True, intervalo=intervalo, cliente=ClienteFalso())
