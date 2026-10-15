"""Pantalla de revisión (PLAN.md, Task 6)."""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from registro.cobertura import cobertura_del_nino
from registro.models import (
    Apoyo,
    Captura,
    Curso,
    NivelEducativo,
    Nino,
    ObjetivoAprendizaje,
    Observacion,
    Semestre,
)
from registro.revision import aceptar_todas, contar_pendientes, revision_del_curso

HTMX = {"HX-Request": "true"}
PENDIENTE = Observacion.Estado.PENDIENTE
ACEPTADA = Observacion.Estado.ACEPTADA
DESCARTADA = Observacion.Estado.DESCARTADA


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    """Crear usuarias con el hasher por defecto toma ~0,3 s cada una; aquí no se prueba el login."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def hoy():
    return timezone.localdate()


@pytest.fixture
def ninos(curso, nucleos, hoy):
    Semestre.objects.create(nombre="actual", inicio=hoy - timedelta(days=365), fin=hoy + timedelta(days=60))
    return {
        n.split()[0]: Nino.objects.create(curso=curso, nombre=n, fecha_ingreso=hoy - timedelta(days=300))
        for n in ["Pedro Salinas", "Emilio Vargas", "Sofía Rojas"]
    }


@pytest.fixture
def oas(nucleos):
    ia, lv, pm = nucleos
    return {
        "OA 4 LV": ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=lv, numero=4, texto="Comunicar oralmente."),
        "OA 2 PM": ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=pm, numero=2, texto="Clasificar por atributos."),
        "OA 2 PM medio": ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.MEDIO, nucleo=pm, numero=2, texto="Otro nivel educativo."),
    }


def _captura(curso, autora, texto="Pedro y Emilio clasificaron hojas por color"):
    return Captura.objects.create(
        curso=curso, autora=autora, tipo=Captura.Tipo.TEXTO, texto_original=texto, estado=Captura.Estado.PROCESADA
    )


def _obs(captura, nino=None, *, fecha=None, cita="Clasificó hojas por color.", nucleos=(), oas=(), estado=PENDIENTE, **campos):
    obs = Observacion.objects.create(
        captura=captura, nino=nino, fecha=fecha or timezone.localdate(), cita=cita, estado=estado, **campos
    )
    obs.nucleos.set(nucleos)
    obs.oas.set(oas)
    return obs


@pytest.fixture
def nota(curso, educadora, ninos, nucleos, oas):
    """Una nota sobre Pedro y Emilio, un nombre ambiguo y un comentario sobre el grupo."""
    ia, lv, pm = nucleos
    captura = _captura(curso, educadora)
    return {
        "captura": captura,
        "pedro": _obs(captura, ninos["Pedro"], nucleos=[pm], oas=[oas["OA 2 PM"]], apoyo=Apoyo.AUTONOMO,
                      nombre_detectado="Pedro", interpretacion="Reconoce atributos."),
        "emilio": _obs(captura, ninos["Emilio"], nucleos=[pm], apoyo=Apoyo.CON_AYUDA, nombre_detectado="Emilio"),
        "sofia": _obs(captura, None, nombre_detectado="Sofía", cita="Sofía contó las hojas."),
        "grupal": _obs(captura, None, grupal=True, cita="Hoy bajó la asistencia por lluvia."),
    }


def _url(nombre, obj):
    return reverse(nombre, args=[obj.pk])


def _estado(obs):
    obs.refresh_from_db()
    return obs.estado


# --- La pantalla ------------------------------------------------------------------------


def test_la_revision_agrupa_por_captura_y_separa_las_notas_grupales(client, curso, educadora, nota):
    otra_captura = _captura(curso, educadora, texto="Rubí cruzó el circuito")
    _obs(otra_captura, nota["pedro"].nino, cita="Cruzó el circuito sin ayuda.")
    client.force_login(educadora)

    respuesta = client.get(_url("revision", curso))

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert f'id="captura-{nota["captura"].pk}"' in html and f'id="captura-{otra_captura.pk}"' in html
    assert "Contexto del curso" in html and "Hoy bajó la asistencia por lluvia." in html
    assert "en la nota dice «Sofía»" in html
    assert "4 observaciones por revisar" in html and "1 nota grupal de contexto" in html
    assert "OA 2 PM" in html and "Autónomo" in html and "Reconoce atributos." in html

    revision = revision_del_curso(curso)
    assert [len(g.individuales) for g in revision.grupos] == [3, 1]
    assert [o for _, o in revision.grupales] == [nota["grupal"]]


def test_la_revision_no_muestra_las_ya_revisadas(client, curso, educadora, nota):
    for clave in ("pedro", "emilio", "sofia", "grupal"):
        Observacion.objects.filter(pk=nota[clave].pk).update(estado=DESCARTADA)
    client.force_login(educadora)

    html = client.get(_url("revision", curso)).content.decode()

    assert "No quedan observaciones por revisar." in html
    assert "Clasificó hojas por color." not in html


def test_la_revision_pide_login(client, curso):
    respuesta = client.get(_url("revision", curso))
    assert respuesta.status_code == 302
    assert reverse("login") in respuesta["Location"]


# --- Permisos (asistente_del_curso y directora_del_jardin vienen de conftest.py) ----------


@pytest.mark.parametrize("quien", ["asistente_del_curso", "directora_del_jardin", "otra_educadora"])
def test_solo_la_educadora_del_curso_revisa(client, request, curso, nota, quien):
    client.force_login(request.getfixturevalue(quien))
    pedro, captura = nota["pedro"], nota["captura"]

    assert client.get(_url("revision", curso)).status_code == 404
    assert client.get(_url("observacion_editar", pedro)).status_code == 404
    assert client.post(_url("observacion_editar", pedro), {"obs%d-cita" % pedro.pk: "x"}).status_code == 404
    assert client.post(_url("observacion_aceptar", pedro)).status_code == 404
    assert client.post(_url("observacion_descartar", pedro)).status_code == 404
    assert client.post(_url("observacion_asignar", nota["sofia"]), {"nino": pedro.nino_id}).status_code == 404
    assert client.post(_url("captura_aceptar_todas", captura)).status_code == 404
    assert _estado(pedro) == PENDIENTE
    assert Observacion.objects.filter(captura=captura, estado=PENDIENTE).count() == 4


def test_una_educadora_no_puede_actuar_sobre_observaciones_de_otro_curso(client, jardin, otra_educadora, nota):
    """Aunque tenga su propio curso, las observaciones de otro curso responden 404."""
    Curso.objects.create(jardin=jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora)
    client.force_login(otra_educadora)

    assert client.post(_url("observacion_aceptar", nota["pedro"]), headers=HTMX).status_code == 404
    assert _estado(nota["pedro"]) == PENDIENTE


def test_una_observacion_ya_revisada_no_se_puede_volver_a_tocar(client, educadora, nota):
    client.force_login(educadora)
    pedro = nota["pedro"]
    assert client.post(_url("observacion_aceptar", pedro), headers=HTMX).status_code == 200

    assert client.post(_url("observacion_descartar", pedro), headers=HTMX).status_code == 404
    assert _estado(pedro) == ACEPTADA


def test_el_contador_de_pendientes_es_solo_de_quien_revisa(curso, educadora, asistente_del_curso, otra_educadora, nota):
    assert contar_pendientes(educadora) == 4
    assert contar_pendientes(asistente_del_curso) == 0
    assert contar_pendientes(otra_educadora) == 0


# --- Contador en la barra de navegación y enlaces ----------------------------------------


def test_la_barra_muestra_el_contador_a_la_educadora_en_todas_las_paginas(client, curso, educadora, nota):
    client.force_login(educadora)
    for url in (_url("curso", curso), _url("ficha", nota["pedro"].nino), _url("metas", curso)):
        html = client.get(url).content.decode()
        assert 'id="contador-pendientes"' in html, url
        assert f'href="{_url("revision", curso)}">Por revisar: <strong>4</strong>' in html, url


@pytest.mark.parametrize("quien", ["asistente_del_curso", "directora_del_jardin"])
def test_la_barra_no_muestra_el_contador_a_quien_no_revisa(client, request, curso, nota, quien):
    client.force_login(request.getfixturevalue(quien))
    html = client.get(_url("curso", curso)).content.decode()
    assert 'id="contador-pendientes"' not in html
    assert _url("revision", curso) not in html


def test_con_varios_cursos_el_contador_va_por_curso(client, jardin, educadora, nota):
    otro = Curso.objects.create(jardin=jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION, educadora=educadora)
    client.force_login(educadora)
    html = client.get(reverse("inicio")).content.decode()
    assert "Por revisar en Transición A: <strong>4</strong>" in html
    assert f'href="{_url("revision", otro)}">Por revisar en Transición B: <strong>0</strong>' in html


def test_las_acciones_actualizan_el_contador_fuera_de_banda(client, curso, educadora, nota):
    client.force_login(educadora)

    html = client.post(_url("observacion_descartar", nota["pedro"]), headers=HTMX).content.decode()
    assert '<li id="contador-pendientes" hx-swap-oob="true">' in html
    assert "Por revisar: <strong>3</strong>" in html

    html = client.post(_url("captura_aceptar_todas", nota["captura"]), headers=HTMX).content.decode()
    assert '<li id="contador-pendientes" hx-swap-oob="true">' in html
    assert "Por revisar: <strong>1</strong>" in html


def test_la_tabla_del_curso_enlaza_a_la_revision_con_las_pendientes(client, curso, educadora, nota):
    client.force_login(educadora)
    html = client.get(_url("curso", curso)).content.decode()
    # La nota grupal no cuenta: es contexto, no una observación de un niño.
    assert f'<a href="{_url("revision", curso)}">Revisar observaciones (3 pendientes)</a>' in html


# --- Aceptar, descartar y asignar -------------------------------------------------------


def test_aceptar_con_htmx_devuelve_la_tarjeta_resuelta_y_el_contador(client, educadora, nota):
    client.force_login(educadora)

    respuesta = client.post(_url("observacion_aceptar", nota["pedro"]), headers=HTMX)

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Aceptada:" in html and "Pedro Salinas" in html
    assert 'id="resumen-revision" role="status" hx-swap-oob="true"' in html
    assert "2 observaciones por revisar" in html
    assert _estado(nota["pedro"]) == ACEPTADA


def test_aceptar_sin_javascript_redirige_a_la_revision(client, curso, educadora, nota):
    client.force_login(educadora)

    respuesta = client.post(_url("observacion_aceptar", nota["pedro"]), follow=True)

    assert respuesta.redirect_chain[-1][0] == _url("revision", curso)
    assert "Observación aceptada." in respuesta.content.decode()
    assert _estado(nota["pedro"]) == ACEPTADA


def test_no_se_acepta_una_observacion_sin_nino(client, educadora, nota):
    client.force_login(educadora)

    respuesta = client.post(_url("observacion_aceptar", nota["sofia"]), headers=HTMX)

    assert respuesta.status_code == 200
    assert "Elige a qué niño o niña corresponde antes de aceptarla." in respuesta.content.decode()
    assert _estado(nota["sofia"]) == PENDIENTE


def test_una_nota_grupal_se_acepta_como_contexto_sin_nino(client, educadora, nota):
    client.force_login(educadora)
    assert client.post(_url("observacion_aceptar", nota["grupal"]), headers=HTMX).status_code == 200
    nota["grupal"].refresh_from_db()
    assert nota["grupal"].estado == ACEPTADA and nota["grupal"].nino is None


def test_descartar(client, educadora, nota):
    client.force_login(educadora)

    respuesta = client.post(_url("observacion_descartar", nota["emilio"]), headers=HTMX)

    assert "Descartada:" in respuesta.content.decode()
    assert _estado(nota["emilio"]) == DESCARTADA


def test_asignar_un_nino_a_un_nombre_ambiguo_y_luego_aceptar(client, educadora, ninos, nota):
    client.force_login(educadora)
    sofia = nota["sofia"]

    respuesta = client.post(_url("observacion_asignar", sofia), {"nino": ninos["Sofía"].pk}, headers=HTMX)

    assert respuesta.status_code == 200
    assert "Sofía Rojas" in respuesta.content.decode()
    sofia.refresh_from_db()
    assert sofia.nino == ninos["Sofía"] and sofia.estado == PENDIENTE
    client.post(_url("observacion_aceptar", sofia), headers=HTMX)
    assert _estado(sofia) == ACEPTADA


def test_reasignar_a_otro_nino(client, educadora, ninos, nota):
    client.force_login(educadora)
    pedro = nota["pedro"]

    client.post(_url("observacion_asignar", pedro), {"nino": ninos["Emilio"].pk}, headers=HTMX)

    pedro.refresh_from_db()
    assert pedro.nino == ninos["Emilio"]


def test_no_se_puede_asignar_un_nino_de_otro_curso(client, jardin, educadora, otra_educadora, nota, hoy):
    otro_curso = Curso.objects.create(
        jardin=jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora
    )
    ajeno = Nino.objects.create(curso=otro_curso, nombre="Niño ajeno", fecha_ingreso=hoy)
    client.force_login(educadora)

    respuesta = client.post(_url("observacion_asignar", nota["sofia"]), {"nino": ajeno.pk}, headers=HTMX)

    assert "Elige un niño o niña de la lista." in respuesta.content.decode()
    nota["sofia"].refresh_from_db()
    assert nota["sofia"].nino is None


# --- Editar -----------------------------------------------------------------------------


def _datos_edicion(obs, **cambios):
    datos = {
        "nino": obs.nino_id or "",
        "fecha": obs.fecha.isoformat(),
        "cita": obs.cita,
        "interpretacion": obs.interpretacion,
        "nucleos": [n.pk for n in obs.nucleos.all()],
        "oas": [o.pk for o in obs.oas.all()],
        "apoyo": obs.apoyo,
    }
    datos.update(cambios)
    if datos.pop("grupal", False):
        datos["grupal"] = "on"
    return {f"obs{obs.pk}-{k}": v for k, v in datos.items()}


def test_editar_con_htmx_muestra_el_formulario_con_los_oa_del_nivel_educativo(client, educadora, nota, oas):
    client.force_login(educadora)

    html = client.get(_url("observacion_editar", nota["pedro"]), headers=HTMX).content.decode()

    assert "Editar observación" in html
    assert "Clasificar por atributos." in html
    assert "Otro nivel educativo." not in html
    assert f'value="{oas["OA 2 PM"].pk}" checked' in html


def test_editar_guarda_los_cambios_y_vuelve_a_la_tarjeta(client, educadora, nota, nucleos, oas, hoy):
    ia, lv, pm = nucleos
    client.force_login(educadora)
    pedro = nota["pedro"]
    ayer = hoy - timedelta(days=1)

    respuesta = client.post(
        _url("observacion_editar", pedro),
        _datos_edicion(pedro, cita="Clasificó hojas y explicó su criterio.", fecha=ayer.isoformat(),
                       nucleos=[pm.pk, lv.pk], oas=[oas["OA 2 PM"].pk, oas["OA 4 LV"].pk], apoyo=Apoyo.CON_AYUDA),
        headers=HTMX,
    )

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Clasificó hojas y explicó su criterio." in html and "Editar observación" not in html
    pedro.refresh_from_db()
    assert pedro.cita == "Clasificó hojas y explicó su criterio."
    assert pedro.fecha == ayer
    assert pedro.apoyo == Apoyo.CON_AYUDA
    assert set(pedro.nucleos.all()) == {pm, lv}
    assert set(pedro.oas.all()) == {oas["OA 2 PM"], oas["OA 4 LV"]}
    assert pedro.estado == PENDIENTE  # editar no acepta


@pytest.mark.parametrize("cambio, error", [
    ("fecha_futura", "La fecha no puede ser posterior a hoy."),
    ("oa_de_otro_nivel", "Escoja una opción válida"),
    ("cita_vacia", "Este campo es obligatorio."),
])
def test_editar_rechaza_datos_invalidos(client, educadora, nota, oas, hoy, cambio, error):
    client.force_login(educadora)
    pedro = nota["pedro"]
    cambios = {
        "fecha_futura": {"fecha": (hoy + timedelta(days=1)).isoformat()},
        "oa_de_otro_nivel": {"oas": [oas["OA 2 PM medio"].pk]},
        "cita_vacia": {"cita": ""},
    }[cambio]

    respuesta = client.post(_url("observacion_editar", pedro), _datos_edicion(pedro, **cambios), headers=HTMX)

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Editar observación" in html and error in html
    pedro.refresh_from_db()
    assert pedro.cita == "Clasificó hojas por color." and pedro.fecha == hoy


def test_marcar_como_grupal_quita_el_nino(client, educadora, nota):
    client.force_login(educadora)
    emilio = nota["emilio"]

    client.post(_url("observacion_editar", emilio), _datos_edicion(emilio, grupal=True), headers=HTMX)

    emilio.refresh_from_db()
    assert emilio.grupal and emilio.nino is None


def test_editar_sin_javascript_abre_una_pagina_y_redirige(client, curso, educadora, nota):
    client.force_login(educadora)
    pedro = nota["pedro"]

    pagina = client.get(_url("observacion_editar", pedro))
    assert pagina.status_code == 200 and "Volver a la revisión" in pagina.content.decode()

    respuesta = client.post(_url("observacion_editar", pedro), _datos_edicion(pedro, cita="Nueva cita."))
    assert respuesta.status_code == 302
    assert respuesta["Location"] == f'{_url("revision", curso)}#obs-{pedro.pk}'


def test_cancelar_la_edicion_vuelve_a_la_tarjeta(client, educadora, nota):
    client.force_login(educadora)
    html = client.get(_url("observacion", nota["pedro"]), headers=HTMX).content.decode()
    assert "Clasificó hojas por color." in html and "Editar observación" not in html


# --- Aceptar todas ----------------------------------------------------------------------


def test_aceptar_todas_deja_pendientes_solo_las_que_no_tienen_nino(client, educadora, nota):
    client.force_login(educadora)

    respuesta = client.post(_url("captura_aceptar_todas", nota["captura"]), headers=HTMX)

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Se aceptaron 3 observaciones. 1 queda pendiente porque no tiene niño o niña asignado." in html
    assert 'id="revision-contenido"' in html
    assert "1 observación por revisar" in html
    assert [_estado(nota[k]) for k in ("pedro", "emilio", "grupal", "sofia")] == [ACEPTADA, ACEPTADA, ACEPTADA, PENDIENTE]


def test_aceptar_todas_no_toca_las_ya_descartadas(educadora, nota):
    Observacion.objects.filter(pk=nota["emilio"].pk).update(estado=DESCARTADA)

    assert aceptar_todas(nota["captura"]) == (2, 1)
    assert _estado(nota["emilio"]) == DESCARTADA


# --- Lo aceptado alimenta la tabla, las alertas y la cobertura ---------------------------


def test_aceptar_actualiza_el_aviso_de_datos_en_la_siguiente_carga(client, curso, educadora, ninos, nucleos, hoy):
    """Sin procesos aparte: la tabla del curso se calcula cada vez que se pide."""
    ia, lv, pm = nucleos
    captura = _captura(curso, educadora)
    _obs(captura, ninos["Pedro"], fecha=hoy - timedelta(days=20), nucleos=[lv], estado=ACEPTADA)
    nueva = _obs(captura, ninos["Pedro"], fecha=hoy, nucleos=[lv])
    client.force_login(educadora)
    antes = client.get(_url("curso", curso)).content.decode()
    assert "Datos de hace 20 días" in antes

    client.post(_url("observacion_aceptar", nueva), headers=HTMX)

    despues = client.get(_url("curso", curso)).content.decode()
    assert "Datos de hace 20 días" not in despues
    assert despues.count("Sin datos") == antes.count("Sin datos")


def test_aceptar_suma_al_resumen_de_la_quincena(client, curso, educadora, ninos, nucleos, hoy):
    ia, lv, pm = nucleos
    nueva = _obs(_captura(curso, educadora), ninos["Pedro"], fecha=hoy, nucleos=[pm])
    client.force_login(educadora)
    assert "3 de 3 núcleos sin observaciones" in client.get(_url("curso", curso)).content.decode()

    client.post(_url("observacion_aceptar", nueva), headers=HTMX)

    assert "2 de 3 núcleos sin observaciones" in client.get(_url("curso", curso)).content.decode()


def test_lo_aceptado_aparece_en_la_ficha_y_quita_el_aviso_de_datos(client, curso, educadora, ninos, nucleos, hoy):
    """Demo de la Task 6: se revisa una nota, aparece en la ficha y desaparece el aviso de datos desactualizados."""
    ia, lv, pm = nucleos
    pedro = ninos["Pedro"]
    captura = _captura(curso, educadora)
    _obs(captura, pedro, fecha=hoy - timedelta(days=20), nucleos=[lv], estado=ACEPTADA, cita="Relató su fin de semana.")
    nueva = _obs(captura, pedro, fecha=hoy, nucleos=[lv], cita="Explicó con sus palabras cómo armó la torre.")
    descartada = _obs(captura, pedro, fecha=hoy, nucleos=[lv], cita="Nota equivocada.")
    client.force_login(educadora)
    antes = client.get(_url("ficha", pedro)).content.decode()
    assert "Sin observaciones aceptadas en los últimos 14 días" in antes
    assert "Explicó con sus palabras cómo armó la torre." not in antes  # pendiente: todavía no cuenta

    client.post(_url("observacion_aceptar", nueva), headers=HTMX)
    client.post(_url("observacion_descartar", descartada), headers=HTMX)

    despues = client.get(_url("ficha", pedro)).content.decode()
    assert "Explicó con sus palabras cómo armó la torre." in despues
    assert "Nota equivocada." not in despues
    assert "Sin observaciones aceptadas en los últimos 14 días" not in despues


def test_una_nota_grupal_aceptada_no_aparece_en_la_ficha(client, educadora, ninos, nota):
    client.force_login(educadora)
    client.post(_url("observacion_aceptar", nota["grupal"]), headers=HTMX)
    assert "Hoy bajó la asistencia por lluvia." not in client.get(_url("ficha", ninos["Pedro"])).content.decode()


def test_aceptar_suma_a_la_cobertura_por_oa_del_nino(client, educadora, ninos, nota, oas):
    """La cobertura es la que muestra la ficha (Task 3)."""
    client.force_login(educadora)
    pedro = ninos["Pedro"]

    def cantidad():
        return next(c.cantidad for c in cobertura_del_nino(pedro)["PM"] if c.oa == oas["OA 2 PM"])

    assert cantidad() == 0
    client.post(_url("observacion_aceptar", nota["pedro"]), headers=HTMX)
    assert cantidad() == 1
