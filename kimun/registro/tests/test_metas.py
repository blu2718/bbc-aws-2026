"""Tabla de metas del curso y enlaces en la tabla del curso (Task 3, spec task3-ficha-nino, requisitos 7 y 8).

El test "editar metas cambia las alertas" queda para cuando exista alertas.py (Task 2).
"""
import pytest
from django.urls import reverse

from registro.models import MetaSemestre

METAS = {"semestre_1": "2", "semestre_2": "4", "semestre_3": "6", "semestre_4": "8"}


def _url(curso):
    return reverse("metas", args=[curso.pk])


def _metas(curso):
    return dict(curso.metas.values_list("semestre_permanencia", "nivel_esperado"))


def test_guardar_metas_y_volver_a_abrirlas(client, curso, educadora):
    client.force_login(educadora)
    respuesta = client.post(_url(curso), METAS)
    assert respuesta.status_code == 302 and respuesta["Location"] == reverse("curso", args=[curso.pk])
    assert _metas(curso) == {1: 2, 2: 4, 3: 6, 4: 8}
    assert "Metas guardadas." in client.get(respuesta["Location"]).content.decode()

    html = client.get(_url(curso)).content.decode()
    for semestre, valor in [(1, 2), (2, 4), (3, 6), (4, 8)]:
        select = html.split(f'name="semestre_{semestre}"')[1].split("</select>")[0]
        assert f'<option value="{valor}" selected>' in select
    assert "Desde el semestre 5 de permanencia se espera el nivel máximo de la rúbrica (8)." in html


def test_guardar_actualiza_sin_duplicar(client, curso, educadora):
    MetaSemestre.objects.create(curso=curso, semestre_permanencia=1, nivel_esperado=1)
    client.force_login(educadora)
    client.post(_url(curso), METAS)
    assert curso.metas.count() == 4 and _metas(curso)[1] == 2


def test_metas_invalidas_no_cambian_nada(client, curso, educadora):
    MetaSemestre.objects.create(curso=curso, semestre_permanencia=1, nivel_esperado=1)
    client.force_login(educadora)
    respuesta = client.post(_url(curso), {**METAS, "semestre_1": "3", "semestre_2": "9"})
    assert respuesta.status_code == 200
    assert "Elige un nivel entre 1 y 8." in respuesta.content.decode()
    assert _metas(curso) == {1: 1}


@pytest.mark.parametrize("rol", ["asistente_del_curso", "directora_del_jardin", "otra_educadora"])
def test_solo_la_educadora_edita_metas(client, curso, request, rol):
    client.force_login(request.getfixturevalue(rol))
    assert client.get(_url(curso)).status_code == 404
    assert client.post(_url(curso), METAS).status_code == 404
    assert not curso.metas.exists()


def test_la_tabla_del_curso_enlaza_a_la_ficha_y_a_metas(client, nino, curso, educadora, asistente_del_curso,
                                                       descriptores):
    client.force_login(educadora)
    html = client.get(reverse("curso", args=[curso.pk])).content.decode()
    assert f'href="{reverse("ficha", args=[nino.pk])}"' in html
    assert f'href="{_url(curso)}"' in html
    assert "<td>1 · Comenzando</td>" in html  # IA con rúbrica oficial
    assert "<td>1</td>" in html               # LV provisoria y PM sin descriptores

    client.force_login(asistente_del_curso)
    assert "Editar metas del curso" not in client.get(reverse("curso", args=[curso.pk])).content.decode()
