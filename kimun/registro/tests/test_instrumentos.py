"""Instrumentos estandarizados (Task 14): catálogo, validación, cálculos, coherencia y lectura de la hoja.

Bedrock se reemplaza por un cliente falso; las hojas van a un MEDIA_ROOT temporal.
"""
from datetime import date

import pytest
from django.core.files.base import ContentFile

from registro import instrumentos as ins
from registro.historial import entradas, verificar
from registro.ia.instrumento import (
    ErrorLecturaInstrumento, HojaInvalida, construir_herramienta, estructura_para_el_modelo, leer_hoja, validar_hoja,
)
from registro.ia.bedrock import ErrorBedrock
from registro.models import Instrumento, RegistroCambio, ResultadoInstrumento

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200
PDF = b"%PDF-1.7\n" + b"0" * 200


class ClienteFalso:
    def __init__(self, *respuestas):
        self.respuestas, self.llamadas = list(respuestas), []

    def invocar_herramienta(self, system, mensaje, herramienta, imagenes=(), documentos=()):
        self.llamadas.append({"system": system, "mensaje": mensaje, "herramienta": herramienta,
                              "imagenes": list(imagenes), "documentos": list(documentos)})
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.STORAGES = {**settings.STORAGES, "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}
    return settings.MEDIA_ROOT


@pytest.fixture
def catalogo(db):
    ins.cargar_instrumentos(ins.leer_instrumentos())
    return {i.codigo: i for i in Instrumento.objects.all()}


def defi(codigo):
    return next(d for d in ins.leer_instrumentos()["instrumentos"] if d["codigo"] == codigo)


# --- Catálogo ---------------------------------------------------------------------------


def test_el_catalogo_del_repo_es_valido():
    for d in ins.leer_instrumentos()["instrumentos"]:
        ins.validar_definicion(d)


def test_cargar_instrumentos_es_idempotente(catalogo):
    ins.cargar_instrumentos(ins.leer_instrumentos())
    assert Instrumento.objects.count() == len(catalogo) >= 6
    assert catalogo["IEA"].provisorio and not catalogo["TEPSI"].provisorio


def test_definicion_con_cortes_desordenados_se_rechaza():
    d = defi("TEPSI")
    d["categoria"]["opciones"][0]["desde"], d["categoria"]["opciones"][1]["desde"] = 30, 40
    with pytest.raises(ins.DefinicionInvalida):
        ins.validar_definicion(d)


def test_definicion_con_calculo_de_campo_inexistente_se_rechaza():
    d = defi("TEPSI")
    d["campos"][0]["calculo"] = "suma_areas:NO_EXISTE"
    with pytest.raises(ins.DefinicionInvalida):
        ins.validar_definicion(d)


# --- Normalización y cálculos -------------------------------------------------------------


def test_tepsi_normaliza_coma_decimal_y_rechaza_fuera_de_rango_por_area():
    valores, problemas = ins.normalizar_valores(defi("TEPSI"), {
        "campos": {"T": "45"}, "areas": {"C": {"PB": "12"}, "M": {"PB": "13"}, "L": {"PB": "abc"}},
    })
    assert valores["campos"] == {"T": 45}
    assert valores["areas"]["C"] == {"PB": 12}
    assert "M" not in valores["areas"]          # Motricidad tiene 12 ítems: 13 no puede ser
    assert any("Motricidad" in p and "fuera del rango" in p for p in problemas)
    assert any("Lenguaje" in p and "no es un número" in p for p in problemas)


def test_eedp_acepta_cd_escrito_como_razon():
    valores, problemas = ins.normalizar_valores(defi("EEDP"), {"campos": {"CD": "0,92"}})
    assert valores["campos"]["CD"] == 92 and not problemas


def test_categoria_por_nombre_o_codigo_y_rechaza_desconocida():
    valores, _ = ins.normalizar_valores(defi("TEPSI"), {"categoria": "RIESGO", "categorias_area": {"L": "Normal"}})
    assert valores["categoria"] == "riesgo" and valores["categorias_area"] == {"L": "normal"}
    _, problemas = ins.normalizar_valores(defi("TEPSI"), {"categoria": "excelente"})
    assert problemas


@pytest.mark.parametrize("t, esperado", [(40, "normal"), (39, "riesgo"), (30, "riesgo"), (29, "retraso"), (80, "normal")])
def test_cortes_publicados_del_tepsi(t, esperado):
    assert ins.categoria_por_cortes(defi("TEPSI")["categoria"], t) == esperado


@pytest.mark.parametrize("cd, esperado", [(85, "normal"), (84, "riesgo"), (70, "riesgo"), (69, "retraso")])
def test_cortes_publicados_de_la_eedp(cd, esperado):
    assert ins.categoria_por_cortes(defi("EEDP")["categoria"], cd) == esperado


def test_completar_suma_brutos_y_categoriza_total_y_areas():
    d = defi("TEPSI")
    valores = ins.completar(d, {"campos": {"T": 35}, "areas": {"C": {"PB": 10, "T": 45}, "L": {"PB": 8, "T": 28}, "M": {"PB": 6, "T": 41}}}, None)
    assert valores["campos"]["PB"] == 24
    assert valores["categoria"] == "riesgo"
    assert valores["categorias_area"] == {"C": "normal", "L": "retraso", "M": "normal"}


def test_completar_no_suma_si_falta_un_area_ni_pisa_lo_de_la_hoja():
    d = defi("TEPSI")
    valores = ins.completar(d, {"campos": {"T": 50}, "categoria": "riesgo", "areas": {"C": {"PB": 10}}}, None)
    assert "PB" not in valores["campos"]
    assert valores["categoria"] == "riesgo"     # lo de la hoja se guarda; la coherencia avisa aparte


def test_razon_em_ec_de_la_eedp():
    d = defi("EEDP")
    assert ins.calcular(d, {"campos": {"EM": 330}}, 360)["EM_EC"] == 0.92


def test_edad_en_meses_y_texto():
    assert ins.edad_en_meses(date(2020, 5, 14), date(2023, 6, 12)) == 36
    assert ins.edad_en_meses(date(2020, 5, 14), date(2023, 5, 13)) == 35
    assert ins.texto_edad_evaluacion(date(2020, 5, 14), date(2023, 8, 20)) == "3 años y 3 meses"
    assert ins.edad_en_dias(date(2023, 1, 2), date(2023, 1, 1)) is None


def test_avisos_de_coherencia():
    d = defi("TEPSI")
    valores = {"campos": {"T": 35, "PB": 30}, "categoria": "normal",
               "areas": {"C": {"PB": 10, "T": 45}, "L": {"PB": 8, "T": 45}, "M": {"PB": 6, "T": 41}},
               "categorias_area": {"C": "retraso"}}
    avisos = ins.avisos_de_coherencia(d, valores, date(2020, 1, 1), date(2021, 1, 1))
    texto = " ".join(avisos)
    assert "fuera del rango del instrumento" in texto    # tenía 12 meses; el TEPSI es de 24 a 60
    assert "Puntaje bruto total: la hoja dice 30 y Kimün calcula 24" in texto
    assert "corresponde «Riesgo»" in texto
    assert "Coordinación" in texto


def test_coincide_nombre():
    class N:
        nombre = "Sofía Rojas Pérez"
    assert ins.coincide_nombre("SOFIA ROJAS", N())
    assert ins.coincide_nombre("Sofía", N())
    assert not ins.coincide_nombre("Sofía Muñoz", N())
    assert not ins.coincide_nombre("Pedro Rojas", N())


# --- Lectura con IA (sin Django) ----------------------------------------------------------


def test_validar_hoja():
    assert validar_hoja(JPEG) == ("imagen", "jpeg")
    assert validar_hoja(PDF) == ("pdf", None)
    with pytest.raises(HojaInvalida):
        validar_hoja(b"hola")
    with pytest.raises(HojaInvalida):
        validar_hoja(b"")


def test_la_estructura_que_ve_el_modelo_no_trae_textos_de_la_ficha():
    estructura = estructura_para_el_modelo([defi("TEPSI")])
    texto = str(estructura)
    assert "siguiente_paso" not in texto and "texto_ficha" not in texto
    assert estructura[0]["categoria"][0] == {"codigo": "normal", "nombre": "Normal"}
    assert estructura[0]["categoria_area"] == estructura[0]["categoria"]


def test_leer_hoja_pdf_va_como_documento_e_imagen_como_imagen():
    cliente = ClienteFalso({"instrumento": "TEPSI", "campos": {}, "areas": {}, "ilegibles": [], "es_hoja_de_instrumento": True},
                           {"instrumento": "TEPSI", "campos": {}, "areas": {}, "ilegibles": [], "es_hoja_de_instrumento": True})
    leer_hoja(PDF, [defi("TEPSI")], cliente=cliente)
    leer_hoja(JPEG, [defi("TEPSI")], codigo="TEPSI", cliente=cliente)
    assert cliente.llamadas[0]["documentos"] and not cliente.llamadas[0]["imagenes"]
    assert cliente.llamadas[1]["imagenes"][0][0] == "jpeg"
    assert "indicó que la hoja es del instrumento TEPSI" in cliente.llamadas[1]["mensaje"]
    herramienta = construir_herramienta(["TEPSI", "OTRO"])
    assert herramienta["inputSchema"]["json"]["properties"]["instrumento"]["enum"] == ["TEPSI", "OTRO"]


def test_leer_hoja_rechaza_instrumento_inventado_y_convierte_errores_de_bedrock():
    with pytest.raises(ErrorLecturaInstrumento):
        leer_hoja(JPEG, [defi("TEPSI")], cliente=ClienteFalso({"instrumento": "XYZ", "campos": {}, "areas": {}, "ilegibles": []}))
    with pytest.raises(ErrorLecturaInstrumento):
        leer_hoja(JPEG, [defi("TEPSI")], cliente=ClienteFalso(ErrorBedrock("se cayó")))


# --- Proceso de fondo -------------------------------------------------------------------


@pytest.fixture
def hoja_por_leer(catalogo, nino, educadora, media):
    nino.fecha_nacimiento = date(2020, 5, 14)
    nino.save()
    r = ResultadoInstrumento(nino=nino, estado=ResultadoInstrumento.Estado.POR_LEER, registrado_por=educadora)
    r.archivo.save("hoja.jpg", ContentFile(JPEG), save=False)
    r.save()
    return r


LECTURA_TEPSI = {
    "es_hoja_de_instrumento": True, "instrumento": "TEPSI", "fecha_aplicacion": "2023-06-12",
    "aplicado_por": "Enfermera CESFAM", "nombre_en_hoja": "Pedro Salinas", "fecha_nacimiento_en_hoja": "2020-05-14",
    "campos": {"T": "41"}, "areas": {"C": {"PB": "10", "T": "46"}, "L": {"PB": "8", "T": "34"}, "M": {"PB": "8", "T": "47"}},
    "categoria": "Normal", "categorias_area": {"L": "riesgo"}, "observaciones": "Estimular lenguaje.", "ilegibles": [],
}


def test_procesar_lectura_deja_por_revisar_registra_historial_y_borra_la_hoja(hoja_por_leer, media):
    tomado = ins.tomar_siguiente_lectura()
    assert tomado.pk == hoja_por_leer.pk and tomado.estado == ResultadoInstrumento.Estado.LEYENDO
    nombre = tomado.archivo.name
    assert ins.procesar_lectura(tomado, cliente=ClienteFalso(LECTURA_TEPSI))
    r = ResultadoInstrumento.objects.get(pk=hoja_por_leer.pk)
    assert r.estado == ResultadoInstrumento.Estado.POR_REVISAR
    assert r.instrumento.codigo == "TEPSI" and r.fecha_aplicacion == date(2023, 6, 12)
    assert r.valores["campos"] == {"T": 41, "PB": 26}       # el bruto total lo suma Kimün
    assert r.valores["categorias_area"]["C"] == "normal"   # calculada; L viene de la hoja
    assert not r.archivo and not (media / nombre).exists()
    assert [e.accion for e in entradas(RegistroCambio.Objeto.RESULTADO, r.pk)] == ["lectura_ia"]
    assert verificar(r).ok


def test_lectura_avisa_nombre_distinto_e_ilegibles(hoja_por_leer):
    lectura = {**LECTURA_TEPSI, "nombre_en_hoja": "Matías Soto", "ilegibles": ["puntaje T de Motricidad"],
               "fecha_aplicacion": "2099-01-01"}
    r = ins.tomar_siguiente_lectura()
    ins.procesar_lectura(r, cliente=ClienteFalso(lectura))
    r.refresh_from_db()
    texto = " ".join(r.avisos)
    assert "no parece ser el de Pedro Salinas" in texto
    assert "puntaje T de Motricidad" in texto
    assert "posterior a hoy" in texto and r.fecha_aplicacion is None


def test_si_bedrock_falla_la_hoja_se_conserva_para_reintentar(hoja_por_leer, media):
    r = ins.tomar_siguiente_lectura()
    assert not ins.procesar_lectura(r, cliente=ClienteFalso(ErrorBedrock("throttling")))
    r.refresh_from_db()
    assert r.estado == ResultadoInstrumento.Estado.ERROR and r.archivo
    assert ins.reintentar_lectura(r)
    r.refresh_from_db()
    assert r.estado == ResultadoInstrumento.Estado.POR_LEER


def test_una_hoja_invalida_se_borra(catalogo, nino, educadora, media):
    r = ResultadoInstrumento(nino=nino, estado=ResultadoInstrumento.Estado.POR_LEER, registrado_por=educadora)
    r.archivo.save("hoja.jpg", ContentFile(b"no es una foto"), save=False)
    r.save()
    r = ins.tomar_siguiente_lectura()
    assert not ins.procesar_lectura(r, cliente=ClienteFalso())
    r.refresh_from_db()
    assert r.estado == ResultadoInstrumento.Estado.ERROR and not r.archivo
    assert not ins.reintentar_lectura(r)


def test_procesar_capturas_tambien_lee_hojas(hoja_por_leer):
    from django.core.management import call_command

    call_command("procesar_capturas", una_vez=True, cliente=ClienteFalso(LECTURA_TEPSI), catalogo={"nucleos": []})
    hoja_por_leer.refresh_from_db()
    assert hoja_por_leer.estado == ResultadoInstrumento.Estado.POR_REVISAR


def test_resumen_para_mostrar(hoja_por_leer):
    r = ins.tomar_siguiente_lectura()
    ins.procesar_lectura(r, cliente=ClienteFalso(LECTURA_TEPSI))
    r.refresh_from_db()
    resumen = ins.resumir(r)
    assert resumen.principal.valor == "41" and resumen.categoria["codigo"] == "normal"
    assert resumen.edad == "3 años"
    assert [a.nombre for a in resumen.areas] == ["Coordinación", "Lenguaje", "Motricidad"]
    assert resumen.areas[1].categoria["texto_ficha"] == "Con seguimiento del centro de salud"


# --- Bordes (revisión del 16-10) ------------------------------------------------------------


def test_el_historial_no_avisa_adulteracion_mientras_se_lee_la_hoja_o_si_falla(hoja_por_leer, educadora):
    from registro.historial import registrar

    registrar(hoja_por_leer, RegistroCambio.Accion.CREAR, usuario=educadora, motivo="Hoja subida")
    r = ins.tomar_siguiente_lectura()
    assert r.estado == ResultadoInstrumento.Estado.LEYENDO and verificar(r).ok
    ins.procesar_lectura(r, cliente=ClienteFalso(ErrorBedrock("throttling")))
    r.refresh_from_db()
    assert r.estado == ResultadoInstrumento.Estado.ERROR and verificar(r).ok
    # Un cambio real de los valores por fuera de la app sí se detecta.
    ResultadoInstrumento.objects.filter(pk=r.pk).update(valores={"campos": {"T": 60}})
    r.refresh_from_db()
    assert not verificar(r).ok


@pytest.mark.parametrize("crudo", ["NaN", "Infinity", "-inf", "sNaN", "1e999999", float("nan")])
def test_un_numero_no_finito_es_un_problema_y_no_un_error(crudo):
    valores, problemas = ins.normalizar_valores(defi("TEPSI"), {"campos": {"T": crudo}})
    assert "T" not in valores["campos"] and problemas


@pytest.mark.parametrize("crudo, esperado", [("1,00", 100), ("1", 100), ("0,85", 85), ("85", 85)])
def test_eedp_cd_escrito_como_razon_entera(crudo, esperado):
    valores, problemas = ins.normalizar_valores(defi("EEDP"), {"campos": {"CD": crudo}})
    assert valores["campos"]["CD"] == esperado and not problemas


def test_una_lectura_con_otra_forma_no_bota_al_worker(hoja_por_leer):
    """Si Claude devuelve un texto donde se esperaba un objeto, se ignora; un error inesperado deja la hoja en error."""
    # Antes: AttributeError ('str' no tiene .get) y el worker se caía en bucle.
    valores, _ = ins.normalizar_valores(defi("OTRO"), {"areas_libres": ["Motor", {"nombre": "Lenguaje"}]})
    assert [a["nombre"] for a in valores["areas_libres"]] == ["Lenguaje"]
    valores, _ = ins.normalizar_valores(defi("TEPSI"), {"campos": {"T": "41"}, "areas": {"C": "10"}, "categorias_area": "L"})
    assert valores["campos"] == {"T": 41} and not valores["areas"]

    otra = ResultadoInstrumento(nino=hoja_por_leer.nino, estado=ResultadoInstrumento.Estado.POR_LEER,
                                registrado_por=hoja_por_leer.registrado_por)
    otra.archivo.save("hoja.jpg", ContentFile(JPEG), save=False)
    otra.save()
    r = ins.tomar_siguiente_lectura()
    assert not ins.procesar_lectura(r, cliente=ClienteFalso(RuntimeError("inesperado")))
    r.refresh_from_db()
    assert r.estado == ResultadoInstrumento.Estado.ERROR and r.archivo


def test_una_hoja_que_se_interrumpe_muchas_veces_queda_en_error(hoja_por_leer):
    from datetime import timedelta

    from django.utils import timezone

    hace_rato = timezone.now() - ins.UMBRAL_LEYENDO_ATASCADA - timedelta(seconds=1)
    ResultadoInstrumento.objects.filter(pk=hoja_por_leer.pk).update(
        estado=ResultadoInstrumento.Estado.LEYENDO, intentos=ins.MAX_INTENTOS_LECTURA, actualizado=hace_rato,
    )
    assert ins.recuperar_lecturas_atascadas() == 0
    hoja_por_leer.refresh_from_db()
    assert hoja_por_leer.estado == ResultadoInstrumento.Estado.ERROR and hoja_por_leer.archivo
    # Se puede reintentar a mano: la hoja sigue guardada.
    assert ins.reintentar_lectura(hoja_por_leer)


def test_si_descartan_la_hoja_mientras_se_lee_no_se_pisa(hoja_por_leer):
    r = ins.tomar_siguiente_lectura()

    class Descartar(ClienteFalso):
        def invocar_herramienta(self, *args, **kwargs):
            ResultadoInstrumento.objects.filter(pk=r.pk).update(estado=ResultadoInstrumento.Estado.DESCARTADO)
            return super().invocar_herramienta(*args, **kwargs)

    assert not ins.procesar_lectura(r, cliente=Descartar(LECTURA_TEPSI))
    r.refresh_from_db()
    assert r.estado == ResultadoInstrumento.Estado.DESCARTADO
