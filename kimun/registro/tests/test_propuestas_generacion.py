"""Preparación ORM y generación de la Task 7, punto 3. Sin servicios externos."""
import json
from datetime import date

import pytest
from django.db import connection

from registro.ia.propuesta import ErrorConfiguracionPropuesta
from registro.models import DescriptorNivel, Manifestacion, NivelEducativo, NivelValidado, Nino, ObjetivoAprendizaje, Observacion, PropuestaNivel
from registro.propuestas import generar_propuesta, huella_entrada, preparar_evidencia


class ClienteFalso:
    modelo = "modelo-de-prueba"
    ultimo_uso = {"tokens_entrada": 40, "tokens_salida": 10}

    def __init__(self, ids=()):
        self.ids = list(ids)
        self.llamadas = []

    def invocar_herramienta(self, system, mensaje, herramienta):
        self.llamadas.append((system, mensaje, herramienta, connection.in_atomic_block))
        return {"nivel": 3, "evidencia_suficiente": True, "observaciones_citadas": self.ids,
                "conductas_observadas": ["Se viste de forma autónoma"], "justificacion": "Evidencia de autonomía."}


def test_selecciona_aceptadas_individuales_del_nino_y_nucleo(nino, nucleos, observar_en):
    ia, lv, _ = nucleos
    tardia = observar_en(nino, date(2026, 5, 1), [ia])
    primera = observar_en(nino, date(2026, 4, 1), [ia])
    misma_fecha = observar_en(nino, date(2026, 4, 1), [ia])
    for estado, grupal in [("pendiente", False), ("descartada", False), ("aceptada", True)]:
        observar_en(nino, date(2026, 4, 1), [ia], estado=estado, grupal=grupal)
    observar_en(nino, date(2026, 4, 1), [lv])
    otro = Nino.objects.create(curso=nino.curso, nombre="Otro niño", fecha_ingreso=date(2026, 3, 1))
    observar_en(otro, date(2026, 4, 1), [ia])
    datos = preparar_evidencia(nino, ia).datos
    assert [o["id"] for o in datos["evidencia"]] == [primera.pk, misma_fecha.pk, tardia.pk]


def test_oa_indirecto_se_incluye_una_vez_con_codigo_y_solo_nivel_educativo_actual(nino, nucleos, observar_en):
    oa = ObjetivoAprendizaje.objects.create(nucleo=nucleos[0], nivel_educativo=NivelEducativo.TRANSICION, numero=1, texto="OA")
    otra_oa = ObjetivoAprendizaje.objects.create(nucleo=nucleos[0], nivel_educativo=NivelEducativo.MEDIO, numero=1, texto="Otro tramo")
    indirecta = observar_en(nino, date(2026, 4, 1), [], oas=[oa])
    directa = observar_en(nino, date(2026, 4, 1), [nucleos[0]], oas=[oa])
    observar_en(nino, date(2026, 4, 1), [], oas=[otra_oa])
    datos = preparar_evidencia(nino, nucleos[0]).datos
    assert [o["id"] for o in datos["evidencia"]] == [indirecta.pk, directa.pk]
    assert all(o["oas"] == ["OA 1 IA"] for o in datos["evidencia"])


@pytest.mark.django_db(transaction=True)
def test_generacion_seudonimizada_fuera_de_transaccion_no_persiste_niveles(nino, nucleos, descriptores, observar_en):
    nino.alias = ["Pedrito"]
    nino.save()
    obs = observar_en(nino, date(2026, 4, 1), [nucleos[0]],
                      cita="Pedrito se vistió solo. Pedro Salinas eligió su ropa.")
    cliente = ClienteFalso([obs.pk])
    antes = NivelValidado.objects.count()
    resultado = generar_propuesta(nino, nucleos[0], cliente=cliente)
    assert resultado.respuesta["nivel"] == 3 and resultado.modelo == cliente.modelo
    assert resultado.uso == cliente.ultimo_uso
    assert resultado.entrada.huella == huella_entrada(nino, nucleos[0])
    assert resultado.entrada.nivel_referencia == nino.nivel_actual(nucleos[0])
    assert cliente.llamadas[0][3] is False
    envio = json.dumps(cliente.llamadas[0][:3], ensure_ascii=False)
    assert "Pedro" not in envio and "Pedrito" not in envio and "Salinas" not in envio
    assert nino.codigo in envio and "Ejemplo IA 1 a" in envio and "Ejemplo IA 1 b" not in envio
    assert NivelValidado.objects.count() == antes and PropuestaNivel.objects.count() == 0
    assert "Pedrito" not in repr(resultado)  # Evitar exponer evidencia cruda en el repr.


def test_sin_evidencia_no_hay_llamadas_ni_modelo(nino, nucleos):
    cliente = ClienteFalso()
    generado = generar_propuesta(nino, nucleos[0], cliente=cliente)
    assert generado.respuesta["nivel"] is None
    assert generado.modelo == "" and generado.uso == {} and cliente.llamadas == []


def test_rubrica_de_nueve_niveles_y_nivel_actual(nino, nucleos, descriptores, rubrica, observar_en):
    rubrica.cantidad_niveles = 9
    rubrica.save()
    DescriptorNivel.objects.create(nucleo=nucleos[0], nivel_educativo=nino.curso.nivel_educativo, nivel=9,
                                    nombre="Nivel nuevo", descripcion="Descripción", conducta="Conducta", provisorio=False)
    NivelValidado.objects.create(nino=nino, nucleo=nucleos[0], nivel=5, fecha=date(2026, 4, 1))
    obs = observar_en(nino, date(2026, 4, 1), [nucleos[0]])
    cliente = ClienteFalso([obs.pk])
    generar_propuesta(nino, nucleos[0], cliente=cliente)
    contexto = json.loads(cliente.llamadas[0][1])
    assert contexto["nivel_actual"] == 5 and contexto["rubrica"]["nivel_maximo"] == 9


def test_provisoria_incompleta_no_llama_al_cliente(nino, nucleos, descriptores, observar_en):
    obs = observar_en(nino, date(2026, 4, 1), [nucleos[1]])
    cliente = ClienteFalso([obs.pk])
    with pytest.raises(ErrorConfiguracionPropuesta, match="trayectoria"):
        generar_propuesta(nino, nucleos[1], cliente=cliente)
    assert cliente.llamadas == []


def test_provisoria_con_datos_del_programa(nino, nucleos, descriptores, observar_en):
    lv = nucleos[1]
    lv.esperado_inicio_nt1 = "Comunica sus necesidades"
    lv.save()
    oa = ObjetivoAprendizaje.objects.create(nucleo=lv, nivel_educativo=nino.curso.nivel_educativo, numero=1, texto="Objetivo")
    for anio in ["NT1", "NT2"]:
        Manifestacion.objects.create(oa=oa, anio=anio, orden=0, texto=f"Conducta de {anio}")
    obs = observar_en(nino, date(2026, 4, 1), [lv], oas=[oa])
    cliente = ClienteFalso([obs.pk])
    generado = generar_propuesta(nino, lv, cliente=cliente)
    assert generado.entrada.rubrica_provisoria is True
    assert json.loads(cliente.llamadas[0][1])["rubrica"]["conductas_programa"][0]["NT2"] == ["Conducta de NT2"]


def test_cambio_del_archivo_prompt_cambia_la_huella(nino, nucleos, monkeypatch):
    from unittest.mock import Mock
    from registro.ia import propuesta

    ruta = Mock()
    ruta.read_text.side_effect = ["Versión A", "Versión B"]
    monkeypatch.setattr(propuesta, "RUTA_PROMPT", ruta)
    antes = huella_entrada(nino, nucleos[0])
    assert huella_entrada(nino, nucleos[0]) != antes
