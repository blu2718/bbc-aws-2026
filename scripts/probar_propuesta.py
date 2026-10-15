"""Procesa una propuesta de nivel contra Bedrock real y audita la petición completa.

Se corre desde la raíz del repo con el entorno de kimun/ y una base aislada.
DJANGO_DB_PATH es obligatoria, para no modificar kimun/db.sqlite3:

    $env:DJANGO_DB_PATH = "$env:TEMP\\kimun-task7.sqlite3"
    kimun\\.venv\\Scripts\\python.exe -X utf8 scripts\\probar_propuesta.py --preparar
    kimun\\.venv\\Scripts\\python.exe -X utf8 scripts\\probar_propuesta.py
    kimun\\.venv\\Scripts\\python.exe -X utf8 scripts\\probar_propuesta.py --sin-red

--preparar agrega a la demo de `cargar_demo` tres observaciones pendientes de
Identidad y Autonomía de Sofía Muñoz (datos ficticios) para aceptarlas en la
revisión. Sin opciones procesa la siguiente solicitud con `procesar_siguiente`,
igual que `manage.py procesar_propuestas --once`, y antes de que botocore firme
y envíe la petición la lee ya serializada: la detiene si trae un nombre, nombre
de pila o alias del curso, un apellido en una cita o un ejemplo reservado.
--sin-red devuelve una propuesta simulada sin llamar a AWS (solo para revisar
la interfaz). Muestra conteos y metadatos; no imprime citas, prompts ni respuestas.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kimun"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

NOTA_DEMO = "Nota de demo de la Task 7: juegos con reglas en el patio y en la sala."
# (días atrás, apoyo, números de OA de IA, cita). Mencionan a otros niños por nombre de pila y alias.
OBSERVACIONES_DEMO = [
    (10, "con_ayuda", [6, 5], "En el patio, Sofía M. dijo «juguemos a la ronda, yo elijo la canción». Cuando Naia "
                              "también quiso elegir, se enojó y la tía tuvo que recordarle que se turnaban."),
    (5, "parcial", [6], "Sofía M. propuso a Benja y a Tomi jugar al almacén y repartió quién vendía y quién compraba. "
                        "Esperó su turno para cobrar; la tía le recordó una vez que no se quitan las monedas."),
    (1, "autonomo", [6, 4], "Sofía M. invitó a Isi a jugar memorice y explicó la regla: «das vuelta dos y si son "
                            "iguales te las quedas». Esperó su turno hasta el final, aunque iba perdiendo, sin que se "
                            "lo recordaran."),
]
CODIGO = re.compile(r"\bN-[0-9A-F]{6}\b")


class EnvioBloqueado(Exception):
    """La petición traía identidades del curso o ejemplos reservados; no se envió."""


def _normal(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.casefold()) if not unicodedata.category(c).startswith("M"))


def _textos(valor):
    """Todas las cadenas de una estructura JSON, incluidas las claves."""
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for clave, contenido in valor.items():
            yield clave
            yield from _textos(contenido)
    elif isinstance(valor, list):
        for elemento in valor:
            yield from _textos(elemento)


def auditar(cuerpo):
    """Revisa la petición serializada de Converse: system, mensaje y herramienta."""
    from registro.models import DescriptorNivel, Nino

    peticion = json.loads(cuerpo)
    mensaje = json.loads(peticion["messages"][0]["content"][0]["text"])
    observaciones = mensaje["observaciones"]
    textos = [*_textos(peticion), *_textos(mensaje)]
    completo = _normal("\n".join(textos))
    citas = _normal("\n".join(o["cita"] for o in observaciones))
    nino = Nino.objects.select_related("curso").get(codigo=mensaje["nino"])
    nombres, apellidos = set(), set()
    for nombre, alias in nino.curso.ninos.values_list("nombre", "alias"):
        partes = nombre.split()
        nombres.update([nombre, partes[0], *alias])
        apellidos.update(partes[1:])

    def aparece(forma, texto):
        return re.search(rf"(?<!\w){re.escape(_normal(forma))}(?!\w)", texto) is not None

    # Apellidos como «Fuentes» o «Reyes» también son palabras comunes de la rúbrica: se buscan solo en las citas.
    identidades = sorted({f for f in nombres if aparece(f, completo)} | {a for a in apellidos if aparece(a, citas)})
    reservados = 0
    if mensaje["rubrica"]["origen"] == "integra":
        for ejemplos in DescriptorNivel.objects.filter(
            nivel_educativo=nino.curso.nivel_educativo, nucleo__sigla=mensaje["nucleo"]["sigla"],
        ).values_list("ejemplos", flat=True):
            reservados += sum(1 for e in ejemplos[1:] if _normal(e) in completo)
    return {
        "observaciones": len(observaciones),
        "ids": {o["id"] for o in observaciones},
        "con_codigo_propio": sum(mensaje["nino"] in o["cita"] for o in observaciones),
        "codigos": len(set(CODIGO.findall("\n".join(textos)))),
        "ambiguas": sum(o["cita"].count("[NINO_AMBIGUO]") for o in observaciones),
        "identidades": identidades,
        "claves": [c for c in ("identidades", "alias") if c in textos],
        "reservados": reservados,
        "origen": mensaje["rubrica"]["origen"],
    }, mensaje


def _simular(mensaje):
    observaciones = mensaje["observaciones"]
    actual, maximo = mensaje["nivel_actual"], mensaje["rubrica"]["nivel_maximo"]
    nivel = min(actual + 1, maximo) if observaciones[-1]["apoyo"] == "autonomo" else actual
    descriptor = next(n for n in mensaje["rubrica"]["niveles"] if n["nivel"] == nivel)
    return {
        "nivel": nivel, "evidencia_suficiente": True, "observaciones_citadas": [o["id"] for o in observaciones],
        "conductas_observadas": [descriptor.get("conducta") or descriptor["descripcion"]],
        "justificacion": "Respuesta simulada sin Bedrock (--sin-red), solo para revisar la interfaz.",
    }


def instalar_auditoria(cliente, *, sin_red, auditorias):
    """Engancha la auditoría al cliente boto3 real, después de validar y serializar y antes de firmar."""
    from botocore.awsrequest import AWSResponse

    def antes_de_enviar(params, **kwargs):
        cuerpo = params["body"] if isinstance(params["body"], bytes) else params["body"].encode("utf-8")
        auditoria, mensaje = auditar(cuerpo)
        auditorias.append(auditoria)
        if auditoria["identidades"] or auditoria["claves"] or auditoria["reservados"]:
            raise EnvioBloqueado("La petición traía identidades del curso o ejemplos reservados.")
        if not sin_red:
            return None  # botocore sigue: firma y envía exactamente este cuerpo.
        entrada = _simular(mensaje)
        respuesta = {
            "output": {"message": {"role": "assistant", "content": [
                {"toolUse": {"toolUseId": "simulada", "name": "proponer_nivel", "input": entrada}},
            ]}},
            "stopReason": "tool_use",
            "usage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0},
            "metrics": {"latencyMs": 0},
        }
        return AWSResponse(params["url"], 200, {}, None), respuesta

    cliente.cliente.meta.events.register_first("before-call.bedrock-runtime.Converse", antes_de_enviar)


def preparar():
    from django.db import transaction
    from django.utils import timezone

    from registro.models import Captura, Curso, ObjetivoAprendizaje, Observacion

    curso = Curso.objects.filter(nombre="Transición Mayor A").first()
    sofia = curso.ninos.filter(nombre="Sofía Muñoz").first() if curso else None
    if sofia is None:
        print("Primero corre `manage.py cargar_demo` en esta base.", file=sys.stderr)
        return 1
    if Captura.objects.filter(curso=curso, texto_original=NOTA_DEMO).exists():
        print("Las observaciones de demo ya existen; no se duplican.")
        return 0
    hoy = timezone.localdate()
    with transaction.atomic():
        captura = Captura.objects.create(curso=curso, autora=curso.asistentes.first() or curso.educadora,
                                         tipo=Captura.Tipo.TEXTO, texto_original=NOTA_DEMO,
                                         estado=Captura.Estado.PROCESADA)
        for hace_dias, apoyo, numeros, cita in OBSERVACIONES_DEMO:
            obs = Observacion.objects.create(captura=captura, nino=sofia, nombre_detectado="Sofía M.",
                                             fecha=hoy - timedelta(days=hace_dias), cita=cita, apoyo=apoyo)
            oas = list(ObjetivoAprendizaje.objects.filter(
                nivel_educativo=curso.nivel_educativo, nucleo__sigla="IA", numero__in=numeros,
            ).select_related("nucleo"))
            obs.oas.set(oas)
            obs.nucleos.set({oa.nucleo for oa in oas})
    print(f"Se crearon {len(OBSERVACIONES_DEMO)} observaciones pendientes de IA de Sofía Muñoz. "
          f"Revisión: /cursos/{curso.pk}/revision/")
    return 0


def procesar(*, sin_red, modelo):
    from registro.ia.bedrock import ClienteBedrock
    from registro.models import PropuestaNivel
    from registro.propuestas import procesar_siguiente

    if PropuestaNivel.objects.filter(estado="solicitada").count() > 1:
        print("La prueba requiere como máximo una solicitud pendiente en la base aislada.", file=sys.stderr)
        return 1
    sdk = None
    if sin_red:
        import boto3
        from botocore import UNSIGNED
        from botocore.config import Config

        # La auditoría devuelve la respuesta antes del envío. No buscar credenciales ni consultar metadatos.
        sdk = boto3.client("bedrock-runtime", region_name="us-east-1",
                           config=Config(signature_version=UNSIGNED, retries={"total_max_attempts": 1}))
    # Sin red, la propuesta guardada no debe aparentar que la generó un modelo real.
    cliente = ClienteBedrock(modelo="simulado-sin-red" if sin_red else modelo,
                             max_intentos=1, cliente=sdk)
    auditorias = []
    instalar_auditoria(cliente, sin_red=sin_red, auditorias=auditorias)
    print(f"Modelo: {cliente.modelo} · región: {cliente.region} · endpoint: {cliente.cliente.meta.endpoint_url}"
          + (" · sin red: respuesta simulada" if sin_red else ""))
    propuesta = procesar_siguiente(cliente=cliente)
    if propuesta is None:
        print("No hay solicitudes pendientes.")
        return 0
    citas = set(propuesta.observaciones_citadas.values_list("pk", flat=True))
    print(f"Propuesta #{propuesta.pk} ({propuesta.nino.codigo}, {propuesta.nucleo.sigla}): {propuesta.get_estado_display()}")
    print(f"  Nivel {propuesta.nivel} · evidencia suficiente: {propuesta.evidencia_suficiente} · "
          f"rúbrica provisoria: {propuesta.rubrica_provisoria} · citas: {len(citas)}")
    print(f"  Modelo guardado: {propuesta.modelo or '-'} · métricas: {propuesta.uso_modelo or '-'}")
    if propuesta.error:
        print(f"  Error guardado: {propuesta.error}")
    for a in auditorias:
        print(f"  Petición: {a['observaciones']} observaciones ({a['con_codigo_propio']} con el código del niño), "
              f"{a['codigos']} códigos, {a['ambiguas']} menciones ambiguas, rúbrica {a['origen']}.")
        print(f"  Identidades del curso: {len(a['identidades'])} · claves de identidad: {len(a['claves'])} · "
              f"ejemplos reservados: {a['reservados']} · citas guardadas dentro de las enviadas: {citas <= a['ids']}")
        if a["identidades"]:
            print(f"  Envío detenido. Declara estas formas como alias o revisa las citas: {', '.join(a['identidades'])}")
    if not auditorias:
        print("  Sin llamada al modelo: no hay observaciones aceptadas para este núcleo.")
    return 1 if propuesta.estado == "error" else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--preparar", action="store_true", help="agrega las observaciones pendientes de la demo")
    grupo.add_argument("--sin-red", action="store_true", help="respuesta simulada, sin llamar a AWS")
    parser.add_argument("--modelo", help="ID del modelo o perfil de inferencia (por defecto BEDROCK_MODEL_ID)")
    args = parser.parse_args()
    if not os.environ.get("DJANGO_DB_PATH"):
        parser.error("define DJANGO_DB_PATH con una base aislada antes de correr este script")
    if Path(os.environ["DJANGO_DB_PATH"]).resolve() == (RAIZ / "kimun" / "db.sqlite3").resolve():
        parser.error("DJANGO_DB_PATH debe ser diferente de la base habitual kimun/db.sqlite3")

    import django

    django.setup()
    return preparar() if args.preparar else procesar(sin_red=args.sin_red, modelo=args.modelo)


if __name__ == "__main__":
    sys.exit(main())
