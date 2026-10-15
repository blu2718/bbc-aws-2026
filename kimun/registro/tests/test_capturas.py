"""Lo que agrega la interfaz al procesamiento: efecto y procesar desde la página.

Las fotos se prueban en test_captura_foto.py (Task 8).

El resto (tomar, reintentar, emparejar, el comando) se prueba en test_procesar_capturas.py.
"""
from datetime import timedelta

import pytest
from django.core.files.base import ContentFile
from django.utils import timezone

from registro import procesamiento
from registro.procesamiento import procesar_si_pendiente, reintentar_desde_la_pagina
from registro.ia import ErrorBedrock
from registro.models import Captura, NivelEducativo, Nino, ObjetivoAprendizaje

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 32


class ClienteFalso:
    """Reemplaza a ClienteBedrock: devuelve respuestas predefinidas y guarda las llamadas."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def invocar_herramienta(self, system, mensaje, herramienta, imagenes=None):
        self.llamadas.append({"system": system, "mensaje": mensaje, "herramienta": herramienta, "imagenes": imagenes})
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


def cruda(nombre, cita=None, **campos):
    """Una observación como la devolvería el modelo."""
    base = {
        "nombre_detectado": nombre,
        "fecha": timezone.localdate().isoformat(),
        "cita_literal": cita or f"{nombre} clasificó las hojas por color.",
        "interpretacion": None,
        "nucleos": ["PM"],
        "oas": [],
        "apoyo": "autonomo",
        "efecto": "sin_dato",
        "grupal": False,
    }
    base.update(campos)
    return base


@pytest.fixture
def curso_con_ninos(curso, nucleos):
    _ia, _lv, pm = nucleos
    ObjetivoAprendizaje.objects.create(nivel_educativo=NivelEducativo.TRANSICION, nucleo=pm, numero=2, texto="Clasificar")
    for nombre, alias in [("Pedro Salinas", []), ("Naiara Fuentes", ["Nayara"]), ("Sofía Rojas", [])]:
        Nino.objects.create(curso=curso, nombre=nombre, alias=alias, fecha_ingreso=timezone.localdate())
    return curso


def _captura(curso, autora, texto="Nota de prueba", tipo=Captura.Tipo.TEXTO):
    return Captura.objects.create(curso=curso, autora=autora, tipo=tipo, texto_original=texto)


def test_se_guarda_el_efecto_de_cada_suceso(curso_con_ninos, educadora):
    captura = _captura(curso_con_ninos, educadora, "Pedro clasificó hojas. Nayara no quiso participar.")
    cliente = ClienteFalso({"observaciones": [
        cruda("Pedro", oas=["OA 2 PM"], efecto="avance"),
        cruda("Nayara", "Nayara no quiso participar.", efecto="por_reforzar"),
    ]})

    assert procesar_si_pendiente(captura, cliente)

    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PROCESADA
    obs = list(captura.observaciones.order_by("id"))
    assert [(o.nino.nombre, o.efecto) for o in obs] == [("Pedro Salinas", "avance"), ("Naiara Fuentes", "por_reforzar")]
    assert [oa.codigo for oa in obs[0].oas.all()] == ["OA 2 PM"]


def test_dos_procesos_no_toman_la_misma_captura(curso_con_ninos, educadora):
    captura = _captura(curso_con_ninos, educadora)
    assert procesamiento.tomar(captura.pk)
    assert not procesar_si_pendiente(captura, ClienteFalso())  # ya la tomó otro: no llama al modelo


def test_desde_la_pagina_se_reintenta_un_error_o_una_atascada(curso_con_ninos, educadora):
    captura = _captura(curso_con_ninos, educadora)
    procesar_si_pendiente(captura, ClienteFalso(ErrorBedrock("Unable to locate credentials")))
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.ERROR

    assert reintentar_desde_la_pagina(captura)
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE

    procesamiento.tomar(captura.pk)
    captura.refresh_from_db()
    assert not reintentar_desde_la_pagina(captura)  # procesando hace poco: no se toca
    hace_rato = timezone.now() - procesamiento.UMBRAL_PROCESANDO_ATASCADA - timedelta(minutes=1)
    Captura.objects.filter(pk=captura.pk).update(actualizada=hace_rato)
    captura.refresh_from_db()
    assert reintentar_desde_la_pagina(captura)




def test_el_audio_espera_la_transcripcion(curso_con_ninos, educadora, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    captura = Captura(curso=curso_con_ninos, autora=educadora, tipo=Captura.Tipo.AUDIO)
    captura.archivo.save("audio.webm", ContentFile(WEBM), save=False)
    captura.save()

    assert not procesar_si_pendiente(captura, ClienteFalso())
    captura.refresh_from_db()
    assert captura.estado == Captura.Estado.PENDIENTE
