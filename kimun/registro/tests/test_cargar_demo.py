import json
import os
import re
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.db import transaction
from django.urls import reverse

from registro.alertas import EstadoDatos, Gravedad, resumen_del_jardin, tabla_del_curso
from registro.cobertura import cobertura_del_nino, cobertura_quincena_del_curso, oas_sin_evidencia, quincena_de
from registro.frecuencia import frecuencia_del_curso
from registro.pantallas import para_tener_presentes
from registro.management.commands.cargar_demo import RUTA_DEMO
from registro.models import (
    Captura,
    Curso,
    DescriptorNivel,
    Jardin,
    Manifestacion,
    MetaSemestre,
    NivelEducativo,
    NivelValidado,
    Nino,
    Nucleo,
    ObjetivoAprendizaje,
    Observacion,
    Rubrica,
    Semestre,
)

MODELOS = [
    Rubrica, Nucleo, ObjetivoAprendizaje, Manifestacion, DescriptorNivel, Semestre, Jardin, Curso, MetaSemestre,
    Nino, NivelValidado, Captura, Observacion,
]
HOY = date(2026, 10, 16)  # día de la demo


def _curso_a():
    """El curso de la demo con observaciones (Tasks 2 a 6)."""
    return Curso.objects.get(nombre="Transición Mayor A")


def _conteos():
    return {m.__name__: m.objects.count() for m in MODELOS} | {
        "User": get_user_model().objects.count(),
        "asistentes": Curso.asistentes.through.objects.count(),
    }


@pytest.fixture(scope="module")
def _demo_del_modulo(django_db_setup, django_db_blocker):
    """Corre cargar_demo una sola vez para todo el módulo (tarda unos 2 s) y lo deshace al final.

    La carga queda dentro de una transacción abierta. Cada test, con el
    fixture `db`, corre en un savepoint dentro de ella y se deshace al
    terminar, así que los tests que vuelven a cargar o editan datos no afectan
    a los demás.
    """
    password_anterior = os.environ.get("DEMO_PASSWORD")
    os.environ["DEMO_PASSWORD"] = "clave-demo-de-prueba"
    try:
        with django_db_blocker.unblock(), transaction.atomic():
            call_command("cargar_demo", verbosity=0, hoy=HOY)
            yield
            transaction.set_rollback(True)
    finally:
        if password_anterior is None:
            os.environ.pop("DEMO_PASSWORD", None)
        else:
            os.environ["DEMO_PASSWORD"] = password_anterior


@pytest.fixture
def cargada(_demo_del_modulo, db, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "clave-demo-de-prueba")


def test_carga_curriculo_y_rubrica(cargada):
    rubrica = Rubrica.objects.get(nivel_educativo=NivelEducativo.TRANSICION)
    assert (rubrica.cantidad_niveles, rubrica.provisoria) == (8, True)
    assert Nucleo.objects.count() == 8
    assert ObjetivoAprendizaje.objects.count() == 85
    transicion = DescriptorNivel.objects.filter(nivel_educativo=NivelEducativo.TRANSICION)
    assert transicion.count() == 8 * 8
    # IA viene de la rúbrica de Integra; los otros 7 núcleos siguen provisorios.
    assert set(transicion.filter(provisorio=False).values_list("nucleo__sigla", flat=True)) == {"IA"}
    assert transicion.get(nucleo__sigla="IA", nivel=3).nombre == "Desarrollando"
    assert Manifestacion.objects.filter(anio="NT1").exists()
    assert Manifestacion.objects.filter(anio="NT2").exists()


def test_carga_la_rubrica_de_integra_en_los_3_niveles_educativos(cargada):
    assert Rubrica.objects.count() == 3
    assert DescriptorNivel.objects.filter(nucleo__sigla="IA", provisorio=False).count() == 3 * 8


def test_cada_nucleo_trae_su_trayectoria(cargada):
    for nucleo in Nucleo.objects.all():
        assert nucleo.esperado_inicio_nt1.startswith("Al iniciar"), nucleo.sigla
        assert nucleo.continuidad_basica.startswith("Durante"), nucleo.sigla


def test_carga_curso_de_15_ninos_con_nivel_inicial(cargada):
    curso = _curso_a()
    assert curso.ninos.count() == 15
    iniciales = NivelValidado.objects.filter(validado_por__isnull=True, nino__curso=curso)
    assert iniciales.count() == 15 * 8
    assert set(iniciales.values_list("nivel", flat=True)) == {1}
    assert list(curso.metas.values_list("semestre_permanencia", "nivel_esperado")) == [(1, 1), (2, 3), (3, 5), (4, 7)]
    assert Semestre.objects.count() == 3


def test_carga_educadora_y_asistente(cargada, client):
    curso = _curso_a()
    assert curso.educadora.username == "educadora"
    assert list(curso.asistentes.values_list("username", flat=True)) == ["asistente"]
    assert client.login(username="educadora", password="clave-demo-de-prueba")
    assert client.login(username="asistente", password="clave-demo-de-prueba")


def test_incluye_casos_dificiles_de_nombres(cargada):
    assert Nino.objects.filter(nombre__startswith="Sofía").count() == 2
    assert "Nayara" in Nino.objects.get(nombre__startswith="Naiara").alias
    assert len(set(Nino.objects.values_list("fecha_ingreso", flat=True))) > 1


def test_correr_dos_veces_no_duplica(cargada):
    antes = _conteos()
    call_command("cargar_demo", verbosity=0)
    assert _conteos() == antes


def test_volver_a_cargar_respeta_los_descriptores_editados(cargada):
    """Un descriptor editado en el panel (no provisorio) no vuelve al texto provisorio."""
    d = DescriptorNivel.objects.get(nivel_educativo=NivelEducativo.TRANSICION, nucleo__sigla="LV", nivel=3)
    d.descripcion, d.provisorio, d.pasos_sugeridos = "Texto de Integra", False, "Observar X"
    d.save()

    call_command("cargar_demo", verbosity=0)

    d.refresh_from_db()
    assert (d.descripcion, d.provisorio, d.pasos_sugeridos) == ("Texto de Integra", False, "Observar X")


def test_si_la_rubrica_cambia_de_cantidad_de_niveles_falla_sin_cambiar_nada(cargada):
    """Si alguien pasa Transición a 9 niveles en el panel, cargar_demo no la devuelve a 8 ni deja
    la rúbrica de Integra (8 niveles) a medias: avisa que hay que igualarlas."""
    Rubrica.objects.filter(nivel_educativo=NivelEducativo.TRANSICION).update(cantidad_niveles=9)
    antes = _conteos()

    with pytest.raises(CommandError, match="trae 8 niveles y la de la app tiene 9"):
        call_command("cargar_demo", verbosity=0)

    assert Rubrica.nivel_maximo(NivelEducativo.TRANSICION) == 9
    assert _conteos() == antes


def test_sin_demo_password_genera_y_muestra_contrasenas(cargada, monkeypatch, capsys, client):
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    # Las usuarias ya existen (carga del módulo): --cambiar-password las vuelve a fijar.
    call_command("cargar_demo", cambiar_password=True)
    mostradas = dict(re.findall(r"^Contraseña de (\S+): (\S+)$", capsys.readouterr().out, re.MULTILINE))
    assert set(mostradas) == {"educadora", "asistente", "directora", "educadora_b", "educadora_c"}
    assert len(set(mostradas.values())) == len(mostradas)  # una al azar para cada una
    # Directora, educadora_b y educadora_c usan el mismo mecanismo que las demás.
    for usuario in ("directora", "educadora_b", "educadora_c"):
        assert client.login(username=usuario, password=mostradas[usuario]), usuario
        assert not client.login(username=usuario, password="clave-demo-de-prueba"), usuario


def test_las_usuarias_de_demo_no_traen_contrasena_escrita():
    """El JSON de la demo no trae contraseñas: salen de DEMO_PASSWORD o se generan al azar."""
    demo = json.loads(RUTA_DEMO.read_text(encoding="utf-8"))
    usuarias = [demo["educadora"], *demo["asistentes"], demo["directora"], *(c["educadora"] for c in demo["otros_cursos"])]
    assert {u["usuario"] for u in usuarias} == {"educadora", "asistente", "directora", "educadora_b", "educadora_c"}
    for u in usuarias:
        assert set(u) == {"usuario", "nombre", "apellido", "email"}, u["usuario"]


@pytest.mark.parametrize(
    "modelo", ["rubrica", "curso", "nino", "objetivoaprendizaje", "manifestacion", "descriptornivel", "nivelvalidado", "jardin"]
)
def test_el_admin_muestra_lo_cargado(cargada, admin_client, modelo):
    """Demo de la Task 1: el panel muestra curso, niños, OA y rúbrica."""
    respuesta = admin_client.get(f"/admin/registro/{modelo}/")
    assert respuesta.status_code == 200


def test_el_admin_abre_las_fichas(cargada, admin_client):
    urls = [
        f"/admin/registro/nino/{Nino.objects.first().pk}/change/",
        f"/admin/registro/objetivoaprendizaje/{ObjetivoAprendizaje.objects.first().pk}/change/",
        f"/admin/registro/curso/{_curso_a().pk}/change/",
        f"/admin/registro/rubrica/{Rubrica.objects.get(nivel_educativo=NivelEducativo.TRANSICION).pk}/change/",
        f"/admin/registro/descriptornivel/{DescriptorNivel.objects.filter(provisorio=False).first().pk}/change/",
    ]
    for url in urls:
        assert admin_client.get(url).status_code == 200, url


# --- Datos de demo de la Task 2 -----------------------------------------------------------


def _celda(tabla, nombre, sigla):
    fila = next(f for f in tabla.filas if f.nino.nombre == nombre)
    return fila.celdas[[n.sigla for n in tabla.nucleos].index(sigla)]


def test_demo_trae_unas_80_observaciones_aceptadas_con_nucleos_y_oa(cargada):
    individuales = Observacion.objects.filter(estado=Observacion.Estado.ACEPTADA, grupal=False)
    assert 75 <= individuales.count() <= 85
    assert all(o.nucleos.exists() and o.oas.exists() for o in individuales)
    # Cada OA etiquetado va con su núcleo.
    for o in individuales:
        assert set(o.oas.values_list("nucleo", flat=True)) <= set(o.nucleos.values_list("pk", flat=True))
    grupal = Observacion.objects.get(grupal=True)
    assert grupal.nino is None and not grupal.nucleos.exists()
    assert Captura.objects.filter(autora__username="asistente").exists()


def test_demo_muestra_un_nino_bajo_sus_pares_en_lenguaje(cargada):
    tabla = tabla_del_curso(_curso_a(), hoy=HOY)
    lv = _celda(tabla, "Matías Lagos", "LV")
    assert (lv.nivel, lv.pares.gravedad, lv.esperado.gravedad) == (2, Gravedad.ALERTA, Gravedad.ALERTA)
    assert lv.pares.texto == "Revisar: 3 niveles bajo la mediana del curso"


def test_demo_muestra_todos_los_estados(cargada):
    tabla = tabla_del_curso(_curso_a(), hoy=HOY)
    celdas = [c for f in tabla.filas for c in f.celdas]
    assert {c.gravedad for c in celdas} == {Gravedad.NORMAL, Gravedad.AVISO, Gravedad.ALERTA}
    assert {c.datos for c in celdas} == {EstadoDatos.AL_DIA, EstadoDatos.DESACTUALIZADO, EstadoDatos.SIN_DATOS}
    # Los semestres de permanencia varían: ingresos en 2025-2, 2026-1 y 2026-2.
    assert {f.semestre for f in tabla.filas} == {1, 2, 3}
    # La gran mayoría no tiene alertas: las señales se destacan.
    assert sum(1 for c in celdas if c.gravedad != Gravedad.NORMAL) <= 8


def test_demo_en_ia_usa_los_nombres_de_integra_y_benjamin_esta_en_desarrollando(cargada):
    tabla = tabla_del_curso(_curso_a(), hoy=HOY)
    ia = _celda(tabla, "Benjamín Soto", "IA")
    assert ia.texto_nivel == "3 · Desarrollando"
    assert ia.esperado.texto == "Observar: 2 niveles bajo lo esperado"
    assert _celda(tabla, "Benjamín Soto", "LV").texto_nivel == "5"  # rúbrica provisoria


def test_demo_tiene_historial_de_niveles(cargada):
    matias = Nino.objects.get(nombre="Matías Lagos")
    historial = list(matias.niveles.filter(nucleo__sigla="LV").order_by("fecha").values_list("nivel", flat=True))
    assert historial == [1, 1, 2, 2]
    assert matias.niveles.filter(comentario="Revisión de septiembre").count() == 8


def test_demo_deja_oa_sin_evidencia_a_proposito(cargada):
    cobertura = cobertura_del_nino(Nino.objects.get(nombre="Matías Lagos"))
    assert oas_sin_evidencia(cobertura["LV"])
    assert not any(c.cantidad for c in cobertura["CES"])
    con_evidencia = ObjetivoAprendizaje.objects.filter(observaciones__estado=Observacion.Estado.ACEPTADA).distinct()
    assert 0 < con_evidencia.count() < ObjetivoAprendizaje.objects.count()


def test_demo_la_quincena_actual_tiene_nucleos_sin_observaciones(cargada):
    cobertura = cobertura_quincena_del_curso(_curso_a(), quincena_de(HOY))
    assert any(c.sin_observaciones for c in cobertura)
    assert any(not c.sin_observaciones for c in cobertura)


def test_demo_muestra_ninos_con_pocas_observaciones_y_con_pendientes(cargada):
    curso = _curso_a()
    frecuencia = frecuencia_del_curso(curso, hoy=HOY)
    assert (frecuencia.aviso.mediana, frecuencia.alerta.mediana) == (3, 5)
    senales = {f.nino.nombre: f.gravedad for f in frecuencia.con_senal}
    assert senales == {"Agustín Pérez": Gravedad.ALERTA, "Emilio Vargas": Gravedad.AVISO, "Matías Lagos": Gravedad.AVISO}
    assert [f.nino.nombre for f in frecuencia.con_pendientes] == ["Tomás Herrera"]
    assert Observacion.objects.filter(nino__nombre="Tomás Herrera", estado=Observacion.Estado.PENDIENTE).count() == 3

    presentes = {p.nino.nombre: p for p in para_tener_presentes(tabla_del_curso(curso, hoy=HOY), frecuencia, ver_pendientes=True)}
    for nombre in ("Agustín Pérez", "Emilio Vargas", "Matías Lagos", "Tomás Herrera"):
        assert nombre in presentes, nombre
    assert presentes["Matías Lagos"].revisar and presentes["Matías Lagos"].pocas_observaciones


def test_las_observaciones_de_ia_no_copian_los_ejemplos_de_integra(cargada):
    ejemplos = {
        e for d in DescriptorNivel.objects.filter(nucleo__sigla="IA", provisorio=False) for e in d.ejemplos
    }
    citas = set(Observacion.objects.filter(nucleos__sigla="IA").values_list("cita", flat=True))
    assert citas and not citas & ejemplos


def test_volver_a_cargar_otro_dia_mueve_las_fechas_sin_duplicar(cargada):
    antes = _conteos()
    call_command("cargar_demo", verbosity=0, hoy=HOY + timedelta(days=3))
    assert _conteos() == antes
    assert Observacion.objects.order_by("-fecha").first().fecha == HOY + timedelta(days=3)


def test_volver_a_cargar_conserva_un_nivel_fijado_a_mano(cargada):
    benjamin = Nino.objects.get(nombre="Benjamín Soto")
    ia = Nucleo.objects.get(sigla="IA")
    NivelValidado.objects.create(
        nino=benjamin, nucleo=ia, nivel=4, fecha=HOY, validado_por=_curso_a().educadora
    )
    call_command("cargar_demo", verbosity=0, hoy=HOY)
    assert benjamin.nivel_actual(ia).nivel == 4


# --- Datos de demo de la Task 12 (vista de la directora) ----------------------------------

ALERTAS_DEMO = [
    # A muestra 4,7 y B 6,0 en los dos núcleos; C muestra 3,0: el resto queda en 5,4 (5,35 redondeado).
    "Revisar: Transición Mayor C, 2,4 niveles bajo el resto del jardín en Lenguaje Verbal",
    "Revisar: Transición Mayor C, 2,4 niveles bajo el resto del jardín en Pensamiento Matemático",
]


def test_demo_tiene_3_salas_de_transicion_en_el_jardin(cargada):
    jardin = _curso_a().jardin
    cursos = list(jardin.cursos.all())
    assert [c.nombre for c in cursos] == ["Transición Mayor A", "Transición Mayor B", "Transición Mayor C"]
    assert {c.nivel_educativo for c in cursos} == {NivelEducativo.TRANSICION}
    assert _curso_a().ninos.count() == 15
    nucleos = Nucleo.objects.count()
    for curso, usuario in zip(cursos[1:], ["educadora_b", "educadora_c"]):
        assert 8 <= curso.ninos.count() <= 10
        assert curso.educadora.username == usuario
        assert not curso.asistentes.exists()
        assert not Observacion.objects.filter(nino__curso=curso).exists()
        # Cada niño tiene niveles validados por la educadora de su sala en todos los núcleos.
        for nino in curso.ninos.all():
            validados = nino.niveles.filter(validado_por=curso.educadora)
            assert validados.values("nucleo").distinct().count() == nucleos, nino


def test_demo_carga_la_directora_del_jardin(cargada, client):
    jardin = _curso_a().jardin
    assert jardin.directora.username == "directora"
    assert client.login(username="directora", password="clave-demo-de-prueba")
    assert client.login(username="educadora_b", password="clave-demo-de-prueba")
    assert client.login(username="educadora_c", password="clave-demo-de-prueba")


def test_demo_muestra_la_alerta_de_la_sala_rezagada(cargada):
    resumen = resumen_del_jardin(_curso_a().jardin)
    assert [a.texto_alerta for a in resumen.alertas] == ALERTAS_DEMO
    b = next(c for c in resumen.grupos[0].cursos if c.nombre == "Transición Mayor B")
    assert {celda.texto_promedio for fila in resumen.grupos[0].filas for celda in fila.celdas if celda.curso == b} == {"6,0"}


def test_en_la_demo_todas_las_salas_tienen_niveles_validados_suficientes(cargada):
    """Las 3 salas entran en la comparación de todos los núcleos: cada niño tiene nivel validado por su educadora."""
    resumen = resumen_del_jardin(_curso_a().jardin)
    celdas = [celda for fila in resumen.grupos[0].filas for celda in fila.celdas]
    assert len(celdas) == 3 * Nucleo.objects.count()
    for celda in celdas:
        assert celda.suficiente, (celda.curso.nombre, celda.nucleo.sigla)
        assert celda.validados == celda.ninos == celda.curso.ninos.count(), (celda.curso.nombre, celda.nucleo.sigla)
    for curso in _curso_a().jardin.cursos.all():
        for nino in curso.ninos.all():
            validados = nino.niveles.filter(validado_por=curso.educadora)
            assert validados.values("nucleo").distinct().count() == Nucleo.objects.count(), nino


def test_demo_la_directora_ve_la_alerta_en_la_vista_del_jardin(cargada, client):
    jardin = _curso_a().jardin
    url = reverse("jardin", args=[jardin.pk])
    assert client.login(username="directora", password="clave-demo-de-prueba")

    respuesta = client.get(url)

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    for texto in ALERTAS_DEMO:
        assert texto in html
    assert html.count('class="celda-alerta"') == 2

    client.logout()
    assert client.login(username="educadora", password="clave-demo-de-prueba")
    assert client.get(url).status_code == 404


def test_volver_a_cargar_no_duplica_las_salas_ni_la_directora(cargada):
    antes = _conteos()
    jardin = _curso_a().jardin
    call_command("cargar_demo", verbosity=0, hoy=HOY)
    assert _conteos() == antes
    assert Curso.objects.count() == 3
    assert get_user_model().objects.filter(username="directora").count() == 1
    jardin.refresh_from_db()
    assert jardin.directora.username == "directora"


def test_carga_instrumentos_y_resultados_de_demo_con_historial(cargada):
    """Task 14: el catálogo de instrumentos y unos resultados confirmados, sin duplicar al recargar."""
    from registro.historial import verificar
    from registro.models import Instrumento, ResultadoInstrumento

    assert Instrumento.objects.filter(codigo__in=["EEDP", "TEPSI", "IEA"]).count() == 3
    resultados = ResultadoInstrumento.objects.filter(estado=ResultadoInstrumento.Estado.CONFIRMADO)
    assert resultados.count() == 4
    emilio = resultados.filter(nino__nombre="Emilio Vargas").order_by("fecha_aplicacion")
    assert [r.valores["categorias_area"]["L"] for r in emilio] == ["riesgo", "normal"]
    assert all(verificar(r).ok for r in resultados)
    call_command("cargar_demo", verbosity=0, hoy=HOY)
    assert ResultadoInstrumento.objects.count() == 4
