"""Niños que vienen de otro jardín o sala cuna: semestres previos y nivel esperado."""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from registro.alertas import semestre_de_permanencia, tabla_del_curso
from registro.historial import entradas, verificar
from registro.models import MetaSemestre, Nino, RegistroCambio, Semestre

S = SimpleNamespace


def test_los_semestres_previos_se_suman_al_de_permanencia():
    semestres = [S(inicio=date(2026, 3, 2), fin=date(2026, 7, 3)), S(inicio=date(2026, 7, 20), fin=date(2026, 12, 18))]
    hoy = date(2026, 10, 16)
    assert semestre_de_permanencia(date(2026, 7, 20), hoy, semestres) == 1
    assert semestre_de_permanencia(date(2026, 7, 20), hoy, semestres, previos=2) == 3
    assert semestre_de_permanencia(date(2026, 3, 2), hoy, semestres, previos=1) == 3
    assert semestre_de_permanencia(date(2026, 7, 20), hoy, [], previos=2) is None  # sin semestres no se compara


@pytest.fixture
def recien_llegada(curso, nucleos, educadora):
    """Llegó al inicio del semestre actual con nivel 4 en todo; metas 1, 3, 5, 7."""
    hoy = timezone.localdate()
    Semestre.objects.create(nombre="actual", inicio=hoy - timedelta(days=60), fin=hoy + timedelta(days=60))
    for semestre, nivel in {1: 1, 2: 3, 3: 5, 4: 7}.items():
        MetaSemestre.objects.create(curso=curso, semestre_permanencia=semestre, nivel_esperado=nivel)
    nina = Nino.objects.create(curso=curso, nombre="Josefa Morales", fecha_ingreso=hoy - timedelta(days=60))
    from registro.models import NivelValidado

    for nucleo in nucleos:
        NivelValidado.objects.create(nino=nina, nucleo=nucleo, nivel=4, fecha=hoy, validado_por=educadora)
    return nina


def _fila(nina):
    return next(f for f in tabla_del_curso(nina.curso).filas if f.nino.pk == nina.pk)


def _guardar(client, nina, **datos):
    return client.post(reverse("trayectoria", args=[nina.pk]),
                       {f"trayectoria-{k}": v for k, v in datos.items()})


def test_la_educadora_registra_los_semestres_previos_y_cambia_lo_esperado(client, educadora, recien_llegada):
    assert (_fila(recien_llegada).semestre, _fila(recien_llegada).nivel_esperado) == (1, 1)
    client.force_login(educadora)

    respuesta = _guardar(client, recien_llegada, semestres_previos=2, procedencia="Jardín Las Araucarias",
                         motivo="Informe de traslado")

    assert respuesta.status_code == 302 and respuesta["Location"].endswith("#trayectoria")
    recien_llegada.refresh_from_db()
    assert (recien_llegada.semestres_previos, recien_llegada.procedencia) == (2, "Jardín Las Araucarias")
    fila = _fila(recien_llegada)
    assert (fila.semestre, fila.nivel_esperado) == (3, 5)
    # Nivel 4 frente a 5 esperado: brecha de 1, sin señal todavía.
    assert all(not c.esperado.texto for c in fila.celdas)

    html = client.get(respuesta["Location"]).content.decode()
    assert "Trayectoria guardada: está en su semestre 3 y se espera el nivel 5." in html
    assert "Semestre 3 en Transición · se espera el nivel 5" in html
    assert "Incluye 2 semestres en Jardín Las Araucarias" in html


def test_cada_cambio_queda_en_el_historial_a_prueba_de_adulteracion(client, educadora, recien_llegada):
    client.force_login(educadora)
    _guardar(client, recien_llegada, semestres_previos=2, procedencia="Jardín Las Araucarias", motivo="Traslado")
    _guardar(client, recien_llegada, semestres_previos=2, procedencia="Jardín Las Araucarias")  # sin cambios
    _guardar(client, recien_llegada, semestres_previos=1, procedencia="Jardín Las Araucarias", motivo="Corrección")

    lista = list(entradas(RegistroCambio.Objeto.TRAYECTORIA, recien_llegada.pk))
    assert [(e.antes["semestres_previos"], e.despues["semestres_previos"], e.motivo) for e in lista] == [
        (0, 2, "Traslado"), (2, 1, "Corrección"),
    ]
    recien_llegada.refresh_from_db()
    assert verificar(recien_llegada).ok

    # Cambiarlo por fuera de la app se detecta.
    Nino.objects.filter(pk=recien_llegada.pk).update(semestres_previos=4)
    recien_llegada.refresh_from_db()
    assert not verificar(recien_llegada).ok


def test_con_semestres_previos_hay_que_indicar_de_donde_viene(client, educadora, recien_llegada):
    client.force_login(educadora)
    respuesta = _guardar(client, recien_llegada, semestres_previos=2, procedencia="  ")
    assert respuesta.status_code == 200
    assert "Indica de qué jardín o sala cuna viene." in respuesta.content.decode()
    recien_llegada.refresh_from_db()
    assert recien_llegada.semestres_previos == 0

    respuesta = _guardar(client, recien_llegada, semestres_previos=9, procedencia="Otro")
    assert respuesta.status_code == 200
    recien_llegada.refresh_from_db()
    assert recien_llegada.semestres_previos == 0


@pytest.mark.parametrize("rol", ["asistente_del_curso", "directora_del_jardin", "otra_educadora"])
def test_solo_la_educadora_del_curso_cambia_la_trayectoria(client, request, recien_llegada, rol):
    client.force_login(request.getfixturevalue(rol))
    assert _guardar(client, recien_llegada, semestres_previos=2, procedencia="X").status_code == 404
    recien_llegada.refresh_from_db()
    assert recien_llegada.semestres_previos == 0
    if rol != "otra_educadora":
        html = client.get(reverse("ficha", args=[recien_llegada.pk])).content.decode()
        assert "¿Viene de otro jardín o sala cuna?" not in html


def test_la_demo_trae_a_josefa_desde_otro_jardin_y_no_pisa_un_cambio_a_mano(db, educadora):
    call_command("cargar_demo", stdout=None)
    josefa = Nino.objects.get(nombre="Josefa Morales")
    assert josefa.semestres_previos == 2 and "Araucarias" in josefa.procedencia
    assert _fila(josefa).semestre == 3

    from registro.historial import instantanea, registrar

    antes = instantanea(josefa)
    josefa.semestres_previos = 1
    josefa.save()
    registrar(josefa, RegistroCambio.Accion.EDITAR, usuario=josefa.curso.educadora, antes=antes)
    call_command("cargar_demo", stdout=None)
    josefa.refresh_from_db()
    assert josefa.semestres_previos == 1
