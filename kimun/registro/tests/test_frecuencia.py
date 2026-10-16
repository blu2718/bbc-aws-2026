"""Cuántas veces se observa a cada niño frente al curso (registro/frecuencia.py)."""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from django.urls import reverse
from django.utils import timezone

from registro.alertas import Gravedad
from registro.frecuencia import calcular_frecuencia, frecuencia_del_curso
from registro.models import Captura, Curso, NivelEducativo, Nino, Observacion
from registro.procesamiento import NOMBRE_TODO_EL_CURSO

HOY = date(2026, 10, 16)
INGRESO = date(2026, 3, 2)


def _ninos(cantidad, ingreso=INGRESO):
    return [SimpleNamespace(pk=i, nombre=f"Niño {i:02}", fecha_ingreso=ingreso) for i in range(cantidad)]


def _fechas(semana, anteriores=0):
    """`semana` observaciones en los últimos 7 días y `anteriores` entre 8 y 14 días atrás."""
    return [HOY - timedelta(days=i % 7) for i in range(semana)] + [HOY - timedelta(days=7 + i % 7) for i in range(anteriores)]


def _curso(semanas, anteriores=None, pendientes=None, ninos=None):
    """Frecuencia de un curso con un niño por elemento de `semanas`."""
    ninos = ninos or _ninos(len(semanas))
    anteriores = anteriores or [0] * len(semanas)
    fechas = {n.pk: _fechas(s, a) for n, s, a in zip(ninos, semanas, anteriores)}
    return calcular_frecuencia(ninos, fechas, pendientes or {}, HOY)


# --- Pocas observaciones en la semana (aviso) ---------------------------------------------


@pytest.mark.parametrize("cantidad, esperado", [
    (6, Gravedad.NORMAL), (5, Gravedad.NORMAL), (4, Gravedad.AVISO), (3, Gravedad.AVISO),
])
def test_con_mediana_6_por_semana_4_o_menos_es_aviso(cantidad, esperado):
    """El ejemplo de la petición: con mediana 6, 3 o 4 piden atención. Las 2 semanas se mantienen sobre ⅓."""
    frecuencia = _curso([6, 6, 6, 6, cantidad], anteriores=[6, 6, 6, 6, 6])
    assert frecuencia.aviso.mediana == 6
    assert frecuencia.filas[-1].gravedad == esperado


def test_el_aviso_dice_cuantas_tiene_y_la_mediana():
    fila = _curso([6, 6, 6, 3], anteriores=[6, 6, 6, 6]).filas[-1]
    assert fila.texto_corto == "Pocas observaciones: 3 en 7 días"
    assert fila.texto == "Pocas observaciones: 3 en 7 días (mediana del curso: 6)"


def test_la_mediana_con_cantidad_par_puede_quedar_en_x5():
    frecuencia = _curso([3, 4, 4, 5], anteriores=[3, 3, 3, 3])
    assert frecuencia.aviso.mediana == 4 and frecuencia.aviso.texto_mediana == "4"
    frecuencia = _curso([3, 3, 4, 4], anteriores=[3, 3, 3, 3])
    assert frecuencia.aviso.texto_mediana == "3,5"


# --- Muy pocas observaciones en 14 días (alerta) -----------------------------------------


@pytest.mark.parametrize("semana, anteriores, esperado", [
    (0, 0, Gravedad.ALERTA),
    (2, 0, Gravedad.ALERTA),
    (2, 2, Gravedad.ALERTA),  # 4 en 14 días: justo ⅓ de 12
    (1, 4, Gravedad.AVISO),   # 5 en 14 días no alcanza la alerta; 1 en 7 días sí es aviso
    (5, 0, Gravedad.NORMAL),  # 5 en 14 días y 5 en 7: ninguna
])
def test_con_mediana_12_en_14_dias_4_o_menos_es_alerta(semana, anteriores, esperado):
    frecuencia = _curso([6, 6, 6, 6, semana], anteriores=[6, 6, 6, 6, anteriores])
    assert frecuencia.alerta.mediana == 12
    assert frecuencia.filas[-1].gravedad == esperado


def test_la_alerta_reemplaza_al_aviso_y_usa_la_ventana_de_14_dias():
    fila = _curso([6, 6, 6, 0], anteriores=[6, 6, 6, 1]).filas[-1]
    assert fila.gravedad == Gravedad.ALERTA
    assert fila.texto == "Muy pocas observaciones: 1 en 14 días (mediana del curso: 12)"


def test_puede_haber_aviso_semanal_sin_alerta_de_14_dias():
    """Bien observado la semana anterior, pero no esta: aviso, no alerta."""
    fila = _curso([6, 6, 6, 1], anteriores=[6, 6, 6, 9]).filas[-1]
    assert (fila.dos_semanas, fila.gravedad) == (10, Gravedad.AVISO)


# --- Ventanas y casos sin referencia -----------------------------------------------------


def test_las_ventanas_cuentan_hoy_y_los_dias_anteriores():
    nino = _ninos(1)[0]
    fechas = {nino.pk: [HOY, HOY - timedelta(days=6), HOY - timedelta(days=7), HOY - timedelta(days=13),
                        HOY - timedelta(days=14), HOY + timedelta(days=1)]}
    fila = calcular_frecuencia([nino], fechas, {}, HOY).filas[0]
    assert (fila.semana, fila.dos_semanas) == (2, 4)


def test_sin_mediana_minima_no_hay_senales():
    """Mediana 1 por semana (bajo 2) y 3 en 14 días (bajo 4): nadie recibe señal, ni el que tiene 0."""
    frecuencia = _curso([1, 1, 1, 0], anteriores=[2, 2, 2, 0])
    assert not frecuencia.aviso.compara and not frecuencia.alerta.compara
    assert {f.gravedad for f in frecuencia.filas} == {Gravedad.NORMAL}
    assert frecuencia.con_senal == []


def test_justo_la_mediana_minima_ya_compara():
    frecuencia = _curso([2, 2, 2, 0], anteriores=[2, 2, 2, 0])
    assert frecuencia.aviso.compara and frecuencia.alerta.compara
    assert frecuencia.filas[-1].gravedad == Gravedad.ALERTA


def test_en_vacaciones_nadie_tiene_senal():
    frecuencia = _curso([0, 0, 0, 0])
    assert frecuencia.aviso.mediana == 0 and frecuencia.con_senal == []


def test_quien_ingreso_dentro_de_la_ventana_no_entra_en_ella():
    ninos = _ninos(4)
    ninos[3].fecha_ingreso = HOY - timedelta(days=10)  # dentro de los 14 días, antes de los 7
    frecuencia = _curso([4, 4, 4, 0], anteriores=[4, 4, 4, 0], ninos=ninos)
    assert frecuencia.alerta.mediana == 8  # sin el recién llegado
    assert frecuencia.filas[3].gravedad == Gravedad.AVISO  # la semana sí lo incluye

    ninos[3].fecha_ingreso = HOY - timedelta(days=3)
    frecuencia = _curso([4, 4, 4, 0], anteriores=[4, 4, 4, 0], ninos=ninos)
    assert frecuencia.filas[3].gravedad == Gravedad.NORMAL


def test_el_primer_dia_de_la_ventana_ya_cuenta_como_ingreso():
    ninos = _ninos(4)
    ninos[3].fecha_ingreso = HOY - timedelta(days=13)
    frecuencia = _curso([4, 4, 4, 0], anteriores=[4, 4, 4, 0], ninos=ninos)
    assert frecuencia.filas[3].gravedad == Gravedad.ALERTA


def test_con_senal_ordena_primero_las_alertas_y_los_menos_observados():
    frecuencia = _curso([6, 6, 6, 6, 3, 2, 0, 1], anteriores=[6, 6, 6, 6, 6, 6, 0, 0])
    assert [f.nino.pk for f in frecuencia.con_senal] == [6, 7, 5, 4]


def test_el_promedio_semanal_es_entre_los_que_comparan():
    ninos = _ninos(3)
    ninos[2].fecha_ingreso = HOY
    frecuencia = _curso([6, 3, 9], ninos=ninos)
    assert frecuencia.texto_promedio_semana == "4,5"


# --- Pendientes ----------------------------------------------------------------------------


def test_muchas_pendientes_frente_al_resto_es_aviso():
    frecuencia = _curso([3] * 5, anteriores=[3] * 5, pendientes={0: 1, 1: 1, 2: 1, 3: 2, 4: 3})
    assert frecuencia.mediana_pendientes == 1
    assert [f.pendientes_gravedad for f in frecuencia.filas] == [Gravedad.NORMAL] * 4 + [Gravedad.AVISO]
    assert frecuencia.filas[4].texto_pendientes == "3 observaciones pendientes de revisar"
    assert [f.nino.pk for f in frecuencia.con_pendientes] == [4]


def test_las_pendientes_necesitan_un_minimo_y_el_doble_de_la_mediana():
    # Todos al día menos uno con 2: no alcanza el mínimo de 3.
    assert _curso([3] * 4, pendientes={3: 2}).filas[3].pendientes_gravedad == Gravedad.NORMAL
    # Mediana 2: hacen falta 4.
    frecuencia = _curso([3] * 5, pendientes={0: 2, 1: 2, 2: 2, 3: 3, 4: 4})
    assert [f.pendientes_gravedad for f in frecuencia.filas] == [Gravedad.NORMAL] * 4 + [Gravedad.AVISO]


# --- Desde la base ---------------------------------------------------------------------------


@pytest.fixture
def curso_observado(curso, educadora):
    """4 niños: 3 con 6 observaciones esta semana y 6 la anterior, y Pedro con las que pida cada test."""
    hoy = timezone.localdate()
    captura = Captura.objects.create(curso=curso, autora=educadora, tipo=Captura.Tipo.TEXTO, texto_original="x")
    ninos = [
        Nino.objects.create(curso=curso, nombre=nombre, fecha_ingreso=hoy - timedelta(days=100))
        for nombre in ("Ana Rojas", "Bruno Soto", "Carla Díaz", "Pedro Salinas")
    ]

    def observar(nino, dias, estado=Observacion.Estado.ACEPTADA, **extra):
        return Observacion.objects.create(
            captura=captura, nino=nino, fecha=hoy - timedelta(days=dias), cita="Cita", estado=estado, **extra
        )

    for nino in ninos[:3]:
        for i in range(6):
            observar(nino, i)
            observar(nino, 7 + i)
    return SimpleNamespace(curso=curso, ninos=ninos, pedro=ninos[3], observar=observar, hoy=hoy)


def _de(frecuencia, nino):
    return next(f for f in frecuencia.filas if f.nino.pk == nino.pk)


def test_cuentan_aceptadas_y_pendientes_pero_no_descartadas_grupales_ni_de_todo_el_curso(curso_observado):
    c = curso_observado
    c.observar(c.pedro, 0)
    c.observar(c.pedro, 1, estado=Observacion.Estado.PENDIENTE)
    c.observar(c.pedro, 1, estado=Observacion.Estado.DESCARTADA)
    c.observar(c.pedro, 2, nombre_detectado=NOMBRE_TODO_EL_CURSO)
    c.observar(c.pedro, 2, estado=Observacion.Estado.PENDIENTE, nombre_detectado=NOMBRE_TODO_EL_CURSO)
    c.observar(None, 2, estado=Observacion.Estado.ACEPTADA, grupal=True)

    fila = _de(frecuencia_del_curso(c.curso, hoy=c.hoy), c.pedro)

    assert (fila.semana, fila.dos_semanas, fila.pendientes) == (2, 2, 1)
    assert fila.gravedad == Gravedad.ALERTA


def test_las_pendientes_cuentan_aunque_sean_antiguas(curso_observado):
    c = curso_observado
    for dias in (30, 40, 50):
        c.observar(c.pedro, dias, estado=Observacion.Estado.PENDIENTE)
    fila = _de(frecuencia_del_curso(c.curso, hoy=c.hoy), c.pedro)
    assert (fila.dos_semanas, fila.pendientes, fila.pendientes_gravedad) == (0, 3, Gravedad.AVISO)


def test_solo_cuenta_los_ninos_del_curso(curso_observado, otra_educadora, jardin):
    otro = Curso.objects.create(jardin=jardin, nombre="Otro", nivel_educativo=NivelEducativo.TRANSICION,
                                educadora=otra_educadora)
    ajeno = Nino.objects.create(curso=otro, nombre="Ajeno", fecha_ingreso=date(2026, 3, 2))
    curso_observado.observar(ajeno, 0)
    frecuencia = frecuencia_del_curso(curso_observado.curso, hoy=curso_observado.hoy)
    assert {f.nino.pk for f in frecuencia.filas} == {n.pk for n in curso_observado.ninos}


def test_hace_una_cantidad_fija_de_consultas(curso_observado, django_assert_num_queries):
    c = curso_observado
    with django_assert_num_queries(2):
        frecuencia_del_curso(c.curso, hoy=c.hoy, ninos=c.ninos)
    for i in range(10):
        c.observar(c.pedro, i % 14, estado=Observacion.Estado.PENDIENTE)
    with django_assert_num_queries(2):
        frecuencia_del_curso(c.curso, hoy=c.hoy, ninos=c.ninos)


# --- Pantallas -----------------------------------------------------------------------------


def _menu(html):
    menu = html[html.index('id="menu-lateral"'):html.index("</dialog>")]
    return menu[menu.index("Para tener presentes"):menu.index('id="titulo-ninos"')]


def test_el_menu_muestra_en_rojo_a_quien_tiene_muy_pocas_observaciones(client, curso_observado, educadora):
    c = curso_observado
    c.observar(c.pedro, 3)
    client.force_login(educadora)

    presentes = _menu(client.get(reverse("curso", args=[c.curso.pk])).content.decode())

    assert "Pedro Salinas" in presentes and "Ana Rojas" not in presentes
    assert 'class="senal-texto-menu senal-menu-alerta"' in presentes
    assert "Muy pocas observaciones: 1 en 14 días" in presentes
    assert 'title="Muy pocas observaciones: 1 en 14 días (mediana del curso: 12)"' in presentes


def test_el_menu_muestra_en_naranjo_a_quien_tiene_pocas_esta_semana(client, curso_observado, educadora):
    c = curso_observado
    for dias in (0, 7, 8, 9, 10, 11, 12):
        c.observar(c.pedro, dias)
    client.force_login(educadora)

    presentes = _menu(client.get(reverse("registrar", args=[c.curso.pk])).content.decode())

    assert 'class="senal-texto-menu senal-menu-aviso"' in presentes
    assert "Pocas observaciones: 1 en 7 días" in presentes


def test_las_muchas_pendientes_solo_las_ve_quien_revisa(client, curso_observado, educadora, asistente_del_curso):
    c = curso_observado
    for dias in range(12):
        c.observar(c.pedro, dias, estado=Observacion.Estado.PENDIENTE)
    url = reverse("registrar", args=[c.curso.pk])

    client.force_login(educadora)
    assert "12 observaciones pendientes de revisar" in _menu(client.get(url).content.decode())

    client.force_login(asistente_del_curso)
    html = client.get(url).content.decode()
    assert "pendientes de revisar" not in html


def test_la_tabla_del_curso_muestra_la_mediana_y_cada_nino(client, curso_observado, educadora):
    c = curso_observado
    c.observar(c.pedro, 1)
    client.force_login(educadora)

    html = client.get(reverse("curso", args=[c.curso.pk])).content.decode()
    seccion = html[html.index('id="titulo-frecuencia"'):html.index('id="titulo-tabla"')]

    assert "mediana del curso de 6 observaciones" in seccion and "mediana de 12" in seccion
    assert "1 niño con pocas observaciones:" in seccion
    assert '<span class="senal senal-alerta">Muy pocas observaciones: 1 en 14 días (mediana del curso: 12)</span>' in seccion
    for nino in c.ninos:
        assert nino.nombre in seccion


def test_otra_educadora_no_ve_el_curso(client, curso_observado, otra_educadora):
    client.force_login(otra_educadora)
    assert client.get(reverse("curso", args=[curso_observado.curso.pk])).status_code == 404
