"""De una nota escrita a observaciones pendientes, con un cliente de Bedrock falso (PLAN.md, Task 5)."""
import logging
from datetime import date, timedelta

import pytest
from django.core.management import CommandError, call_command
from django.urls import reverse
from django.utils import timezone

from registro.ia import ErrorBedrock
from registro.management.commands import procesar_capturas as comando
from registro.models import Apoyo, Captura, NivelEducativo, Nino, ObjetivoAprendizaje, Observacion
from registro.procesamiento import UMBRAL_PROCESANDO_ATASCADA, procesar, reintentar, tomar, tomar_siguiente
from registro.tests.ia.conftest import ClienteFalso

PENDIENTE = Captura.Estado.PENDIENTE
PROCESANDO = Captura.Estado.PROCESANDO
PROCESADA = Captura.Estado.PROCESADA
ERROR = Captura.Estado.ERROR

# Catálogo mínimo con la forma de datos/curriculo_transicion.json; calza con el fixture `nucleos`.
CATALOGO = {
    "nivel_educativo": "transicion",
    "nucleos": [
        {"sigla": "IA", "nombre": "Identidad y Autonomía", "oas": []},
        {"sigla": "LV", "nombre": "Lenguaje Verbal", "oas": [{"numero": 4, "codigo": "OA 4 LV", "texto": "Comunicar oralmente."}]},
        {"sigla": "PM", "nombre": "Pensamiento Matemático", "oas": [{"numero": 2, "codigo": "OA 2 PM", "texto": "Clasificar por atributos."}]},
    ],
}


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def ninos(curso, nucleos):
    datos = {
        "Pedro": ("Pedro Salinas", []),
        "Emilio": ("Emilio Vargas", []),
        "Rubí": ("Rubí Contreras", ["Rubi"]),
        "Naiara": ("Naiara Fuentes", ["Nayara"]),
        "SofíaR": ("Sofía Rojas", []),
        "SofíaM": ("Sofía Muñoz", []),
    }
    return {
        clave: Nino.objects.create(curso=curso, nombre=nombre, alias=alias, fecha_ingreso=date(2026, 3, 2))
        for clave, (nombre, alias) in datos.items()
    }


@pytest.fixture
def oas(nucleos):
    _ia, lv, pm = nucleos
    return {
        "OA 4 LV": ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, numero=4, texto="Comunicar oralmente."),
        "OA 2 PM": ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=pm, numero=2, texto="Clasificar por atributos."),
    }


def _captura(curso, autora, texto="Pedro y Emilio clasificaron hojas por color", tipo=Captura.Tipo.TEXTO, **campos):
    return Captura.objects.create(curso=curso, autora=autora, tipo=tipo, texto_original=texto, **campos)


def _obs(nombre, cita=None, **campos):
    """Observación cruda como la devuelve el modelo. Sin fecha: se usa la de la captura."""
    base = {
        "nombre_detectado": nombre,
        "fecha": None,
        "cita_literal": cita or f"{nombre} clasificó hojas por color",
        "interpretacion": None,
        "nucleos": ["PM"],
        "oas": ["OA 2 PM"],
        "apoyo": "autonomo",
        "grupal": False,
    }
    base.update(campos)
    return base


def _respuesta(*observaciones):
    return {"observaciones": list(observaciones)}


def _procesar(*respuestas):
    cliente = ClienteFalso(*respuestas)
    call_command("procesar_capturas", una_vez=True, cliente=cliente, catalogo=CATALOGO, verbosity=0)
    return cliente


def _estado(captura):
    captura.refresh_from_db()
    return captura.estado


# --- Separar y emparejar -------------------------------------------------------------------


def test_una_nota_sobre_3_ninos_genera_3_observaciones_pendientes(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora, "Pedro, Emilio y Rubí clasificaron hojas; a Rubí la tía le mostró las primeras.")
    cliente = _procesar(_respuesta(
        _obs("Pedro", interpretacion="Reconoce atributos"),
        _obs("Emilio"),
        _obs("Rubi", apoyo="con_ayuda"),
    ))

    assert _estado(captura) == PROCESADA
    assert captura.intentos == 1 and captura.error == ""
    creadas = list(captura.observaciones.order_by("id"))
    assert [o.nino for o in creadas] == [ninos["Pedro"], ninos["Emilio"], ninos["Rubí"]]
    assert all(o.estado == Observacion.Estado.PENDIENTE for o in creadas)
    pedro = creadas[0]
    assert (pedro.nombre_detectado, pedro.cita, pedro.interpretacion) == ("Pedro", "Pedro clasificó hojas por color", "Reconoce atributos")
    assert pedro.fecha == timezone.localdate(captura.creada)
    assert [n.sigla for n in pedro.nucleos.all()] == ["PM"]
    assert list(pedro.oas.all()) == [oas["OA 2 PM"]]
    assert (pedro.apoyo, creadas[2].apoyo, pedro.grupal) == (Apoyo.AUTONOMO, Apoyo.CON_AYUDA, False)
    # Al modelo le llegan el texto y los nombres del curso como pista.
    assert "Pedro, Emilio y Rubí" in cliente.llamadas[0]["mensaje"]
    assert "Sofía Muñoz" in cliente.llamadas[0]["system"]


def test_nayara_se_asigna_a_naiara(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora, "Nayara contó hasta 10")
    _procesar(_respuesta(_obs("Nayara")))
    obs = captura.observaciones.get()
    assert obs.nino == ninos["Naiara"] and obs.nombre_detectado == "Nayara"


def test_sofia_queda_sin_nino_porque_hay_dos(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora, "Sofía armó una torre")
    _procesar(_respuesta(_obs("Sofía")))
    obs = captura.observaciones.get()
    assert obs.nino is None and obs.nombre_detectado == "Sofía" and obs.estado == Observacion.Estado.PENDIENTE


def test_un_nombre_desconocido_queda_sin_nino(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora, "Florencia saltó en un pie")
    _procesar(_respuesta(_obs("Florencia")))
    obs = captura.observaciones.get()
    assert obs.nino is None and obs.nombre_detectado == "Florencia"


def test_una_nota_grupal_queda_como_contexto_sin_nino(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora, "Hoy bajó la asistencia por la lluvia")
    # separar() deja la grupal sin nombre, sin OA y con apoyo sin_dato, aunque el modelo los traiga.
    _procesar(_respuesta(_obs("Pedro", cita="Hoy bajó la asistencia por la lluvia", grupal=True)))
    obs = captura.observaciones.get()
    assert obs.grupal and obs.nino is None and obs.nombre_detectado == ""
    assert not obs.oas.exists() and obs.apoyo == Apoyo.SIN_DATO


def test_una_nota_sin_observaciones_queda_procesada(curso, educadora, ninos):
    captura = _captura(curso, educadora, "Hoy no pasó nada especial")
    _procesar(_respuesta())
    assert _estado(captura) == PROCESADA and not captura.observaciones.exists()


def test_un_oa_que_no_esta_en_la_base_se_omite_sin_fallar(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora)
    catalogo = {**CATALOGO, "nucleos": CATALOGO["nucleos"] + [{"sigla": "CM", "nombre": "Corporalidad", "oas": [{"numero": 1, "codigo": "OA 1 CM", "texto": "x"}]}]}
    call_command(
        "procesar_capturas", una_vez=True, verbosity=0, catalogo=catalogo,
        cliente=ClienteFalso(_respuesta(_obs("Pedro", nucleos=["PM"], oas=["OA 2 PM", "OA 1 CM"]))),
    )
    assert _estado(captura) == PROCESADA
    assert list(captura.observaciones.get().oas.all()) == [oas["OA 2 PM"]]


# --- Errores y reintentos ------------------------------------------------------------------


@pytest.mark.parametrize("falla", [ErrorBedrock("ThrottlingException: demasiadas llamadas"), "esto no es JSON {"])
def test_un_error_de_separar_deja_la_captura_en_error_y_se_puede_reintentar(curso, educadora, ninos, oas, falla):
    captura = _captura(curso, educadora)

    _procesar(falla)

    assert _estado(captura) == ERROR
    assert captura.error and captura.intentos == 1
    assert not captura.observaciones.exists()
    # Una captura con error no se vuelve a tomar sola.
    assert tomar_siguiente() is None

    assert reintentar(captura) is True
    assert _estado(captura) == PENDIENTE
    _procesar(_respuesta(_obs("Pedro"), _obs("Emilio")))

    assert _estado(captura) == PROCESADA
    assert captura.intentos == 2 and captura.error == ""
    assert captura.observaciones.count() == 2


def test_la_opcion_reintentar_devuelve_los_errores_a_la_cola(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora, estado=ERROR, error="Bedrock falló", intentos=1)
    call_command(
        "procesar_capturas", una_vez=True, reintentar=True, verbosity=0, catalogo=CATALOGO,
        cliente=ClienteFalso(_respuesta(_obs("Pedro"))),
    )
    assert _estado(captura) == PROCESADA and captura.intentos == 2


def test_la_opcion_reintentar_recupera_las_atascadas_en_procesando(curso, educadora, ninos, oas, capsys):
    """Si el proceso murió a mitad, la captura queda en procesando: pasados 5 minutos, --reintentar la recupera."""
    atascada = _captura(curso, educadora, "Pedro contó hasta 10", estado=PROCESANDO, intentos=1)
    reciente = _captura(curso, educadora, "Emilio saltó en un pie", estado=PROCESANDO, intentos=1)
    Captura.objects.filter(pk=atascada.pk).update(
        actualizada=timezone.now() - UMBRAL_PROCESANDO_ATASCADA - timedelta(seconds=1)
    )
    Captura.objects.filter(pk=reciente.pk).update(actualizada=timezone.now() - timedelta(minutes=4))
    reciente.refresh_from_db()
    antes = reciente.actualizada

    call_command(
        "procesar_capturas", una_vez=True, reintentar=True, catalogo=CATALOGO,
        cliente=ClienteFalso(_respuesta(_obs("Pedro"))),
    )

    assert "Capturas con error o atascadas que vuelven a pendiente: 1" in capsys.readouterr().out
    assert _estado(atascada) == PROCESADA and atascada.intentos == 2
    assert atascada.observaciones.get().nino == ninos["Pedro"]
    # La reciente puede seguir en manos de otro proceso: no se toca.
    assert _estado(reciente) == PROCESANDO
    assert (reciente.intentos, reciente.actualizada) == (1, antes)
    assert not reciente.observaciones.exists()


def test_reintentar_solo_cambia_capturas_con_error(curso, educadora):
    for estado in (PENDIENTE, PROCESANDO, PROCESADA):
        captura = _captura(curso, educadora, estado=estado)
        assert reintentar(captura) is False
        assert _estado(captura) == estado


def test_un_error_inesperado_no_deja_la_captura_procesando(curso, educadora, ninos, oas, caplog):
    captura = _captura(curso, educadora)
    with caplog.at_level(logging.WARNING, logger="registro.procesamiento"):
        _procesar(RuntimeError("se cayó algo"))
    assert _estado(captura) == ERROR and "se cayó algo" in captura.error
    # El detalle queda en el log con el traceback.
    registro = next(r for r in caplog.records if r.name == "registro.procesamiento")
    assert registro.exc_info and "se cayó algo" in str(registro.exc_info[1])


def test_el_detalle_del_error_queda_en_la_captura_y_en_el_log_pero_no_en_la_lista(client, curso, educadora, ninos, oas, caplog):
    detalle = "AccessDeniedException: arn:aws:sts::123456789012:assumed-role/kimun no puede invocar el modelo"
    captura = _captura(curso, educadora)
    with caplog.at_level(logging.WARNING, logger="registro.procesamiento"):
        _procesar(ErrorBedrock(detalle))

    assert _estado(captura) == ERROR and detalle in captura.error
    assert detalle in caplog.text
    client.force_login(educadora)
    html = client.get(reverse("capturas_recientes", args=[curso.pk])).content.decode()
    assert "No se pudo procesar la nota. Puedes reintentar." in html
    assert "123456789012" not in html and "AccessDenied" not in html


# --- Toma de capturas ----------------------------------------------------------------------


def test_dos_procesos_no_toman_la_misma_captura(curso, educadora):
    captura = _captura(curso, educadora)
    # Los dos procesos leyeron la misma captura pendiente; la actualización condicional decide.
    assert tomar(captura.pk) is True
    assert tomar(captura.pk) is False
    assert _estado(captura) == PROCESANDO and captura.intentos == 1


def test_tomar_siguiente_entrega_cada_captura_una_sola_vez(curso, educadora):
    primera = _captura(curso, educadora, "primera")
    segunda = _captura(curso, educadora, "segunda")
    assert tomar_siguiente() == primera
    assert tomar_siguiente() == segunda
    assert tomar_siguiente() is None


def test_tomar_siguiente_salta_la_que_otro_proceso_acaba_de_tomar(curso, educadora, monkeypatch):
    """Simula la carrera: entre la consulta y la actualización, otro proceso toma la primera."""
    primera = _captura(curso, educadora, "primera")
    segunda = _captura(curso, educadora, "segunda")
    original = tomar

    def tomar_con_carrera(pk):
        if pk == primera.pk:
            assert original(pk) is True  # el otro proceso
        return original(pk)

    monkeypatch.setattr("registro.procesamiento.tomar", tomar_con_carrera)
    assert tomar_siguiente() == segunda
    assert _estado(primera) == PROCESANDO and primera.intentos == 1


# Las fotos (Task 8) se prueban en test_capturas.py y los audios (Task 9) en test_captura_audio.py.


def test_procesar_una_captura_ya_tomada(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora)
    tomada = tomar_siguiente()
    creadas = procesar(tomada, cliente=ClienteFalso(_respuesta(_obs("Pedro"))), catalogo=CATALOGO)
    assert [o.nino for o in creadas] == [ninos["Pedro"]]
    assert _estado(captura) == PROCESADA


# --- Opciones del comando ------------------------------------------------------------------


def test_sin_una_vez_espera_el_intervalo_entre_vueltas(curso, educadora, ninos, oas, monkeypatch):
    esperas = []

    def dormir(segundos):
        esperas.append(segundos)
        raise KeyboardInterrupt

    monkeypatch.setattr(comando.time, "sleep", dormir)
    captura = _captura(curso, educadora)
    call_command("procesar_capturas", intervalo=2, verbosity=0, catalogo=CATALOGO,
                 cliente=ClienteFalso(_respuesta(_obs("Pedro"))))
    assert esperas == [2]
    assert _estado(captura) == PROCESADA


def test_el_intervalo_debe_ser_positivo(db):
    with pytest.raises(CommandError, match="--intervalo"):
        call_command("procesar_capturas", "--intervalo", "0", cliente=ClienteFalso(), catalogo=CATALOGO)


def test_el_comando_informa_lo_procesado(curso, educadora, ninos, oas, capsys):
    _captura(curso, educadora)
    call_command("procesar_capturas", una_vez=True, catalogo=CATALOGO,
                 cliente=ClienteFalso(_respuesta(_obs("Pedro"), _obs("Sofía"))))
    salida = capsys.readouterr().out
    assert "2 observaciones pendientes (1 sin niño)" in salida
    assert "Listo: 1 capturas procesadas, 0 con error." in salida


# --- Lo creado aparece en la pantalla de revisión (Task 6) ---------------------------------


def test_las_observaciones_creadas_aparecen_y_funcionan_en_la_revision(client, curso, educadora, ninos, oas):
    captura = _captura(curso, educadora, "Pedro y Sofía clasificaron hojas. Hoy bajó la asistencia.")
    _procesar(_respuesta(
        _obs("Pedro", interpretacion="Reconoce atributos"),
        _obs("Sofía", cita="Sofía separó las hojas grandes"),
        _obs(None, cita="Hoy bajó la asistencia", grupal=True),
    ))
    client.force_login(educadora)

    html = client.get(reverse("revision", args=[curso.pk])).content.decode()

    assert f'id="captura-{captura.pk}"' in html
    assert "Pedro clasificó hojas por color" in html and "Reconoce atributos" in html and "OA 2 PM" in html
    assert "en la nota dice «Sofía»" in html
    assert "Contexto del curso" in html and "Hoy bajó la asistencia" in html

    # Se asigna la Sofía ambigua y se aceptan todas.
    sofia = captura.observaciones.get(nombre_detectado="Sofía")
    client.post(reverse("observacion_asignar", args=[sofia.pk]), {"nino": ninos["SofíaR"].pk})
    client.post(reverse("captura_aceptar_todas", args=[captura.pk]))
    assert set(captura.observaciones.values_list("estado", flat=True)) == {Observacion.Estado.ACEPTADA}
    assert ninos["SofíaR"].observaciones.get().cita == "Sofía separó las hojas grandes"


def test_la_revision_muestra_el_nombre_de_la_nota_si_la_asignacion_no_es_exacta(client, curso, educadora, ninos, oas):
    """«Emilia» no está en el curso y se asigna a Emilio por parecido: la educadora tiene que verlo."""
    captura = _captura(curso, educadora, "Emilia, Nayara, Pedro y Rubí clasificaron hojas")
    _procesar(_respuesta(
        _obs("Emilia", cita="Emilia separó las hojas rojas"),
        _obs("Nayara"),             # alias de Naiara
        _obs("pedro"),              # nombre de pila, en minúsculas
        _obs("RUBÍ CONTRERAS"),     # nombre completo, en mayúsculas
    ))
    obs = {o.nombre_detectado: o for o in captura.observaciones.all()}
    assert obs["Emilia"].nino == ninos["Emilio"]
    client.force_login(educadora)

    html = client.get(reverse("revision", args=[curso.pk])).content.decode()

    assert html.count("en la nota dice «") == 1
    assert "en la nota dice «Emilia»" in html
    for nombre in ("Nayara", "pedro", "RUBÍ CONTRERAS"):
        assert obs[nombre].nino is not None
        assert f"en la nota dice «{nombre}»" not in html, nombre


def test_una_fecha_relativa_del_modelo_se_respeta(curso, educadora, ninos, oas):
    captura = _captura(curso, educadora, "Ayer Pedro contó hasta 10")
    ayer = timezone.localdate(captura.creada) - timedelta(days=1)
    _procesar(_respuesta(_obs("Pedro", fecha=ayer.isoformat())))
    assert captura.observaciones.get().fecha == ayer
