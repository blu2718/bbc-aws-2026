"""Sala cuna (0 a 2 años) y nivel medio (2 a 4 años): OA de las Bases Curriculares, demo y procesamiento."""
import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from registro.curriculo import cargar_curriculo, leer_curriculo, leer_curriculo_de
from registro.models import (
    Captura, Curso, DescriptorNivel, NivelEducativo, Nino, Nucleo, ObjetivoAprendizaje, Observacion, PropuestaNivel,
)
from registro.propuestas import generar_propuesta, rubrica_completa
from registro import procesamiento
from registro.tests.test_capturas import ClienteFalso, cruda

# Tabla de contexto/hallazgos-bases-curriculares.md, en el orden IA, CC, CM, LV, LA, EEN, CES, PM.
CONTEOS = {
    NivelEducativo.SALA_CUNA: [7, 6, 7, 8, 6, 5, 5, 6],
    NivelEducativo.MEDIO: [12, 10, 8, 8, 7, 9, 7, 10],
}


@pytest.mark.parametrize("nivel", list(CONTEOS))
def test_el_curriculo_trae_los_oa_de_las_bases(nivel):
    datos = leer_curriculo_de(nivel)
    assert datos["nivel_educativo"] == nivel
    assert [n["sigla"] for n in datos["nucleos"]] == [n["sigla"] for n in leer_curriculo()["nucleos"]]
    assert [len(n["oas"]) for n in datos["nucleos"]] == CONTEOS[nivel]
    for nucleo in datos["nucleos"]:
        for i, oa in enumerate(nucleo["oas"], start=1):
            assert oa["numero"] == i and oa["codigo"] == f"OA {i} {nucleo['sigla']}"
            assert len(oa["texto"]) > 20 and not oa["texto"].endswith(("y", ",", "de"))


def test_cargar_sala_cuna_no_borra_la_trayectoria_de_transicion(db):
    cargar_curriculo(leer_curriculo())
    lv = Nucleo.objects.get(sigla="LV")
    assert lv.esperado_inicio_nt1

    cargar_curriculo(leer_curriculo_de(NivelEducativo.SALA_CUNA), nivel_educativo=NivelEducativo.SALA_CUNA)

    lv.refresh_from_db()
    assert lv.esperado_inicio_nt1 and Nucleo.objects.count() == 8
    assert ObjetivoAprendizaje.objects.filter(nivel_educativo=NivelEducativo.SALA_CUNA).count() == 50
    assert ObjetivoAprendizaje.objects.filter(nivel_educativo=NivelEducativo.TRANSICION).count() == 85
    assert "balbuceos" in ObjetivoAprendizaje.objects.get(
        nivel_educativo=NivelEducativo.SALA_CUNA, nucleo=lv, numero=1
    ).texto


def test_la_demo_de_sala_cuna_se_carga_aparte(db, settings):
    salida = StringIO()
    call_command("cargar_demo", stdout=salida)
    call_command("cargar_demo", "--demo", str(settings.DATOS_DIR / "demo_sala_cuna.json"), stdout=salida)

    # La demo principal trae tres salas de Transición (A, B y C, Task 12); la sala de la educadora es la A.
    principal = Curso.objects.get(nivel_educativo=NivelEducativo.TRANSICION, nombre="Transición Mayor A")
    assert Curso.objects.filter(nivel_educativo=NivelEducativo.TRANSICION).count() == 3
    sala_cuna = Curso.objects.get(nivel_educativo=NivelEducativo.SALA_CUNA)
    assert principal.educadora.username == "educadora" and principal.ninos.count() == 15
    assert sala_cuna.educadora.username == "educadora.salacuna" and sala_cuna.ninos.count() == 6
    hoy = timezone.localdate()
    assert all((hoy - n.fecha_nacimiento).days < 2 * 366 for n in sala_cuna.ninos.all())
    gael = Nino.objects.get(nombre="Gael Pino")
    oa = gael.observaciones.get(cita__contains="balbuceó").oas.get()
    assert oa.nivel_educativo == NivelEducativo.SALA_CUNA and oa.codigo == "OA 1 LV"


def test_una_nota_de_sala_cuna_se_separa_con_los_oa_de_sala_cuna(db, jardin, educadora):
    cargar_curriculo(leer_curriculo())
    cargar_curriculo(leer_curriculo_de(NivelEducativo.SALA_CUNA), nivel_educativo=NivelEducativo.SALA_CUNA)
    curso = Curso.objects.create(jardin=jardin, nombre="Sala Cuna A", nivel_educativo=NivelEducativo.SALA_CUNA,
                                 educadora=educadora)
    Nino.objects.create(curso=curso, nombre="Gael Pino", fecha_ingreso=timezone.localdate())
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO,
                                     texto_original="Gael balbuceó mirando a la tía.")
    cliente = ClienteFalso({"observaciones": [cruda("Gael", "Gael balbuceó mirando a la tía.", nucleos=["LV"],
                                                    oas=["OA 1 LV"])]})

    assert procesamiento.tomar(captura.pk)
    captura.refresh_from_db()
    procesamiento.procesar(captura, cliente=cliente)

    assert "balbuceos" in cliente.llamadas[0]["system"]  # el catálogo enviado es el de sala cuna
    obs = captura.observaciones.get()
    assert obs.nino.nombre == "Gael Pino"
    assert obs.oas.get().nivel_educativo == NivelEducativo.SALA_CUNA


# --- Propuestas de nivel con la rúbrica provisoria de sala cuna y medio ----------------------------


@pytest.fixture
def curso_medio(db, jardin, educadora):
    cargar_curriculo(leer_curriculo())
    cargar_curriculo(leer_curriculo_de(NivelEducativo.MEDIO), nivel_educativo=NivelEducativo.MEDIO)
    return Curso.objects.create(jardin=jardin, nombre="Medio A", nivel_educativo=NivelEducativo.MEDIO,
                                educadora=educadora)


def test_sala_cuna_y_medio_reciben_rubrica_provisoria_sobre_sus_oa(curso_medio):
    for nucleo in Nucleo.objects.all():
        descriptores = DescriptorNivel.objects.filter(nivel_educativo=NivelEducativo.MEDIO, nucleo=nucleo)
        assert sorted(descriptores.values_list("nivel", flat=True)) == list(range(1, 9))
        assert all(d.provisorio and "OA del núcleo" in d.descripcion for d in descriptores)
        assert rubrica_completa(NivelEducativo.MEDIO, nucleo)


def test_una_propuesta_de_medio_usa_los_oa_del_nivel_y_no_la_trayectoria_nt1(curso_medio):
    nino = Nino.objects.create(curso=curso_medio, nombre="Gael Pino", fecha_ingreso=timezone.localdate())
    lv = Nucleo.objects.get(sigla="LV")
    captura = Captura.objects.create(curso=curso_medio, autora=curso_medio.educadora, tipo=Captura.Tipo.TEXTO,
                                     texto_original="x")
    obs = Observacion.objects.create(captura=captura, nino=nino, fecha=timezone.localdate(), cita="Gael nombró 3 objetos.",
                                     estado=Observacion.Estado.ACEPTADA)
    obs.nucleos.set([lv])
    cliente = ClienteFalso({"nivel": 2, "evidencia_suficiente": True, "observaciones_citadas": [obs.pk],
                            "conductas_observadas": ["Nombra objetos"], "justificacion": "Rúbrica provisoria."})

    generacion = generar_propuesta(nino, lv, cliente=cliente)

    assert generacion.respuesta["nivel"] == 2
    rubrica = json.loads(cliente.llamadas[0]["mensaje"])["rubrica"]
    assert rubrica["origen"] == "provisoria" and "trayectoria" not in rubrica
    assert [oa["oa"] for oa in rubrica["oas_del_nivel"]] == [f"OA {i} LV" for i in range(1, 9)]


def test_sin_rubrica_completa_no_se_encolan_propuestas_que_fallarian(client, jardin, educadora, nucleos):
    curso = Curso.objects.create(jardin=jardin, nombre="Medio B", nivel_educativo=NivelEducativo.MEDIO,
                                 educadora=educadora)  # sin currículo cargado: sin descriptores
    nino = Nino.objects.create(curso=curso, nombre="Gael Pino", fecha_ingreso=timezone.localdate())
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="x")
    obs = Observacion.objects.create(captura=captura, nino=nino, fecha=timezone.localdate(), cita="Gael saltó.")
    obs.nucleos.set([nucleos[0]])
    client.force_login(educadora)

    client.post(reverse("observacion_aceptar", args=[obs.pk]))
    html = client.post(reverse("solicitar_propuesta", args=[nino.pk, nucleos[0].sigla]), follow=True).content.decode()

    assert not PropuestaNivel.objects.exists()
    assert "aún no tiene una rúbrica completa" in html
    assert reverse("solicitar_propuesta", args=[nino.pk, nucleos[0].sigla]) not in html
