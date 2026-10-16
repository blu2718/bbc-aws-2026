"""Un ID enorme enviado a mano en un campo de selección múltiple responde 400, no 500."""
import pytest
from django.urls import reverse
from django.utils import timezone

from registro.models import Captura, Nino, Observacion

GIGANTE = "99999999999999999999"


@pytest.fixture
def pendiente(curso, nucleos, educadora):
    nino = Nino.objects.create(curso=curso, nombre="Pedro Salinas", fecha_ingreso=timezone.localdate())
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="x",
                                     estado=Captura.Estado.PROCESADA)
    return Observacion.objects.create(captura=captura, nino=nino, fecha=timezone.localdate(), cita="Ordenó bloques.")


@pytest.mark.parametrize("campo", ["nucleos", "oas"])
def test_editar_una_observacion_con_un_id_gigante(client, educadora, pendiente, campo):
    client.force_login(educadora)
    p = f"obs{pendiente.pk}"
    datos = {f"{p}-fecha": pendiente.fecha.isoformat(), f"{p}-cita": "Ordenó bloques por color.",
             f"{p}-apoyo": "sin_dato", f"{p}-efecto": "sin_dato", f"{p}-{campo}": GIGANTE}
    respuesta = client.post(reverse("observacion_editar", args=[pendiente.pk]), datos)
    assert respuesta.status_code in (200, 400)
    pendiente.refresh_from_db()
    assert pendiente.cita == "Ordenó bloques."  # no se guardó


def test_editar_una_sala_con_un_asistente_gigante(client, curso, directora_del_jardin):
    client.force_login(directora_del_jardin)
    datos = {"nombre": curso.nombre, "educadora": curso.educadora_id, "asistentes": GIGANTE}
    respuesta = client.post(reverse("sala_editar", args=[curso.pk]), datos)
    assert respuesta.status_code == 400
    assert not curso.asistentes.exists()
