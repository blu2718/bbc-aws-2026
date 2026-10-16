"""Quién ve, quién registra y quién valida (PLAN.md, "Seguridad y privacidad")."""
from django.contrib.auth.models import AnonymousUser

from registro.models import Curso, Jardin, NivelEducativo
from registro.permisos import cursos_de, cursos_donde_registra, cursos_que_valida, puede_validar


def test_educadora_ve_registra_y_valida(curso, educadora):
    assert list(cursos_de(educadora)) == [curso]
    assert list(cursos_donde_registra(educadora)) == [curso]
    assert list(cursos_que_valida(educadora)) == [curso]
    assert puede_validar(educadora, curso)


def test_asistente_ve_y_registra_pero_no_valida(curso, asistente):
    curso.asistentes.add(asistente)
    assert list(cursos_de(asistente)) == [curso]
    assert list(cursos_donde_registra(asistente)) == [curso]
    assert list(cursos_que_valida(asistente)) == []
    assert not puede_validar(asistente, curso)


def test_directora_ve_y_registra_en_su_jardin_pero_no_valida(curso, directora, jardin, otra_educadora):
    jardin.directora = directora
    jardin.save()
    otro = Curso.objects.create(
        jardin=jardin, nombre="Transición B", nivel_educativo=NivelEducativo.TRANSICION, educadora=otra_educadora
    )
    assert set(cursos_de(directora)) == {curso, otro}
    assert set(cursos_donde_registra(directora)) == {curso, otro}
    assert list(cursos_que_valida(directora)) == []
    assert not puede_validar(directora, curso)
    assert not puede_validar(directora, otro)


def test_directora_de_otro_jardin_no_registra(curso, directora):
    Jardin.objects.create(nombre="Otro jardín", directora=directora)
    assert list(cursos_donde_registra(directora)) == []


def test_quien_cumple_dos_roles_no_ve_el_curso_repetido(curso, educadora, jardin):
    curso.asistentes.add(educadora)
    jardin.directora = educadora
    jardin.save()
    assert list(cursos_de(educadora)) == [curso]
    assert list(cursos_donde_registra(educadora)) == [curso]


def test_sin_sesion_no_ve_nada(curso):
    anonimo = AnonymousUser()
    assert not cursos_de(anonimo).exists()
    assert not cursos_donde_registra(anonimo).exists()
    assert not cursos_que_valida(anonimo).exists()
    assert not puede_validar(anonimo, curso)
