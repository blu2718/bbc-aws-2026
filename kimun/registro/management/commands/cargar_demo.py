"""Carga el currículo de Transición, la rúbrica de Integra y un curso de demo con 15 niños ficticios.

La rúbrica de Integra (`datos/rubrica_integra.json`) se carga después del
currículo y reemplaza a la provisoria en los núcleos que trae (hoy, IA).

El curso trae niveles históricos validados y unas 80 observaciones aceptadas
(Task 2), para que la tabla muestre todos los estados: un niño bajo sus pares
en lenguaje, avisos, datos desactualizados, núcleos sin datos y OA sin
evidencia. Las de las últimas dos semanas hacen que "Para tener presentes"
muestre un niño con muy pocas observaciones, dos con pocas y uno con varias
pendientes de revisar (`frecuencia.py`). Las fechas de las observaciones se cuentan hacia atrás desde el día
de la carga (o desde --hoy).

Para la vista de la directora (Task 12), el jardín tiene una directora y dos
salas más de Transición (`otros_cursos`), cada una con su educadora, niños y
niveles validados, sin observaciones. Una queda bajo las demás en algunos
núcleos, para que aparezca la sugerencia de revisión.

Se puede correr varias veces: actualiza lo existente y no duplica datos.
Las contraseñas de las educadoras, las asistentes y la directora se toman de
DEMO_PASSWORD o se generan al azar, y solo se fijan al crear cada usuaria (o
con --cambiar-password).
"""
import json
import os
import re
import secrets
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from registro.curriculo import cargar_curriculo, leer_curriculo, leer_curriculo_de
from registro.models import (
    Apoyo,
    Captura,
    Curso,
    Efecto,
    Instrumento,
    Jardin,
    MetaSemestre,
    NivelEducativo,
    NivelValidado,
    Nino,
    Nucleo,
    ObjetivoAprendizaje,
    Observacion,
    PropuestaNivel,
    RegistroCambio,
    ResultadoInstrumento,
    Semestre,
)
from registro.instrumentos import cargar_instrumentos, completar, edad_en_dias, leer_instrumentos
from registro.propuestas import rubrica_completa, solicitar_propuesta
from registro.rubrica_integra import cargar_rubrica_integra, leer_rubrica_integra

RUTA_DEMO = Path(settings.DATOS_DIR) / "demo_curso.json"
RUTA_DEMO_INSTRUMENTOS = Path(settings.DATOS_DIR) / "demo_instrumentos.json"
CODIGO_OA = re.compile(r"^OA (\d+) ([A-Z]+)$")


class Command(BaseCommand):
    help = "Carga currículo, rúbricas (provisoria y de Integra), semestres y el jardín de demo (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", type=Path, default=RUTA_DEMO, help="JSON con los cursos de demo.")
        parser.add_argument(
            "--cambiar-password", action="store_true",
            help="Vuelve a fijar las contraseñas de las usuarias de demo aunque ya existan.",
        )
        parser.add_argument(
            "--hoy", type=date.fromisoformat, default=None,
            help="Fecha (AAAA-MM-DD) desde la que se cuentan los días de las observaciones. Por defecto, hoy.",
        )

    @transaction.atomic
    def handle(self, *args, **opciones):
        cargar_curriculo(leer_curriculo())
        try:
            omitidos = cargar_rubrica_integra(leer_rubrica_integra())
        except ValidationError as error:
            # Al salir con error, la transacción deshace todo lo cargado.
            raise CommandError(f"No se cargó la rúbrica de Integra. {' '.join(error.messages)}") from error
        for nivel_educativo, sigla in omitidos:
            self.stderr.write(self.style.WARNING(
                f"Rúbrica de Integra: se omitió {sigla} en {nivel_educativo} porque ese núcleo no existe."
            ))
        cargar_instrumentos(leer_instrumentos())
        demo = json.loads(Path(opciones["demo"]).read_text(encoding="utf-8"))
        nivel_demo = demo["curso"]["nivel_educativo"]
        if nivel_demo != NivelEducativo.TRANSICION:
            # Cursos de sala cuna o medio (por ejemplo --demo datos/demo_sala_cuna.json): sus OA salen de las Bases.
            cargar_curriculo(leer_curriculo_de(nivel_demo), nivel_educativo=nivel_demo)
        self._passwords = []

        for s in demo["semestres"]:
            Semestre.objects.update_or_create(
                nombre=s["nombre"],
                defaults={"inicio": date.fromisoformat(s["inicio"]), "fin": date.fromisoformat(s["fin"])},
            )

        cambiar = opciones["cambiar_password"]
        educadora = self._usuaria(demo["educadora"], cambiar)
        asistentes = [self._usuaria(a, cambiar) for a in demo.get("asistentes", [])]
        revisiones = demo.get("revisiones", {})

        jardin, _ = Jardin.objects.get_or_create(nombre=demo["jardin"])
        todas = [educadora, *asistentes]
        if "directora" in demo:
            directora = self._usuaria(demo["directora"], cambiar)
            todas.append(directora)
            if jardin.directora_id != directora.pk:
                jardin.directora = directora
                jardin.save(update_fields=["directora"])

        curso, ninos = self._curso(jardin, demo["curso"], demo["ninos"], educadora, asistentes, revisiones)
        otros = []
        for c in demo.get("otros_cursos", []):
            educadora_sala = self._usuaria(c["educadora"], cambiar)
            todas.append(educadora_sala)
            otros.append(self._curso(jardin, c, c["ninos"], educadora_sala, [], revisiones)[0])

        usuarias = {u.username: u for u in [educadora, *asistentes]}
        hoy = opciones["hoy"] or timezone.localdate()
        aceptadas = self._observaciones(curso, demo.get("observaciones", []), ninos, educadora, usuarias, hoy)
        self._capturas_pendientes(curso, demo.get("capturas_pendientes", []), educadora, usuarias)
        self._propuestas_solicitadas(curso, demo.get("propuestas_solicitadas", []), ninos)
        if opciones["demo"] == RUTA_DEMO and RUTA_DEMO_INSTRUMENTOS.exists():
            self._resultados_instrumentos(ninos, educadora)

        nombres = ", ".join(u.username for u in todas)
        resumen_otros = "".join(f"; {c} con {c.ninos.count()} niños" for c in otros)
        self.stdout.write(self.style.SUCCESS(
            f"Demo cargada: {curso} con {curso.ninos.count()} niños y {aceptadas} observaciones aceptadas"
            f"{resumen_otros}. Usuarias: {nombres}"
        ))
        for usuario, password in self._passwords:
            self.stdout.write(f"Contraseña de {usuario}: {password}")

    def _curso(self, jardin, datos, ninos_demo, educadora, asistentes, revisiones):
        """Crea o actualiza un curso con sus metas, niños y niveles. Devuelve (curso, {nombre: niño})."""
        curso, _ = Curso.objects.update_or_create(
            jardin=jardin, nombre=datos["nombre"],
            defaults={"nivel_educativo": datos["nivel_educativo"], "educadora": educadora},
        )
        curso.asistentes.set(asistentes)
        for semestre, nivel in datos["metas"].items():
            MetaSemestre.objects.update_or_create(
                curso=curso, semestre_permanencia=int(semestre), defaults={"nivel_esperado": nivel}
            )

        ninos = {}
        for n in ninos_demo:
            nino = Nino.objects.filter(curso=curso, nombre=n["nombre"]).first()
            nacimiento = date.fromisoformat(n["fecha_nacimiento"]) if n.get("fecha_nacimiento") else None
            if nino is None:
                # save() crea el nivel 1 en todos los núcleos.
                nino = Nino.objects.create(
                    curso=curso, nombre=n["nombre"], alias=n["alias"],
                    fecha_ingreso=date.fromisoformat(n["fecha_ingreso"]), fecha_nacimiento=nacimiento,
                )
            else:
                nino.alias = n["alias"]
                nino.fecha_ingreso = date.fromisoformat(n["fecha_ingreso"])
                nino.fecha_nacimiento = nacimiento
                nino.save(update_fields=["alias", "fecha_ingreso", "fecha_nacimiento"])
            ninos[nino.nombre] = nino
            self._niveles(nino, n.get("niveles", {}), revisiones, educadora)
        return curso, ninos

    def _niveles(self, nino, niveles, revisiones, educadora):
        """Niveles históricos validados por la educadora en cada revisión.

        `niveles` es {"todos": {fecha: nivel}, sigla: {fecha: nivel}}: la sigla
        reemplaza a "todos" en ese núcleo. Se identifican por niño, núcleo,
        fecha y educadora, así que volver a cargar no duplica ni borra los
        niveles fijados a mano durante la demo.
        """
        if not niveles:
            return
        nucleos = list(Nucleo.objects.all())
        siglas = {n.sigla for n in nucleos}
        desconocidas = set(niveles) - siglas - {"todos"}
        if desconocidas:
            raise CommandError(f"{nino}: núcleos desconocidos en los niveles de demo: {', '.join(sorted(desconocidas))}.")
        for nucleo in nucleos:
            for texto_fecha, nivel in niveles.get(nucleo.sigla, niveles.get("todos", {})).items():
                fecha = date.fromisoformat(texto_fecha)
                if fecha < nino.fecha_ingreso:
                    raise CommandError(f"{nino}: nivel validado el {fecha}, antes de su ingreso.")
                NivelValidado.objects.update_or_create(
                    nino=nino, nucleo=nucleo, fecha=fecha, validado_por=educadora,
                    defaults={"nivel": nivel, "comentario": revisiones.get(texto_fecha, "")},
                )

    def _observaciones(self, curso, observaciones, ninos, educadora, usuarias, hoy):
        """Observaciones aceptadas (o pendientes, si traen "estado"), cada una con su captura de texto.

        La fecha es `hoy - hace_dias`, para que los avisos de 14 días y la
        quincena se vean igual cualquier día que se cargue la demo. Cada
        observación se identifica por su cita: si el JSON la cambia, se crea
        otra. Devuelve cuántas observaciones aceptadas e individuales hay.
        """
        nucleos = {n.sigla: n for n in Nucleo.objects.all()}
        oas = {
            (oa.numero, oa.nucleo.sigla): oa
            for oa in ObjetivoAprendizaje.objects.filter(nivel_educativo=curso.nivel_educativo).select_related("nucleo")
        }
        for o in observaciones:
            nino = ninos.get(o["nino"]) if o.get("nino") else None
            grupal = o.get("grupal", False)
            if nino is None and not grupal:
                raise CommandError(f"Observación de demo sin niño conocido: «{o['cita'][:40]}».")
            etiquetas_oa = []
            for codigo in o.get("oas", []):
                coincide = CODIGO_OA.match(codigo)
                oa = coincide and oas.get((int(coincide.group(1)), coincide.group(2)))
                if not oa:
                    raise CommandError(f"OA desconocido en la demo: «{codigo}».")
                etiquetas_oa.append(oa)
            try:
                etiquetas = [nucleos[s] for s in o.get("nucleos", [])]
            except KeyError as error:
                raise CommandError(f"Núcleo desconocido en la demo: {error}.") from error
            if o.get("apoyo", "sin_dato") not in Apoyo.values:
                raise CommandError(f"Nivel de apoyo desconocido en la demo: «{o['apoyo']}».")
            # Sin "efecto" en el JSON: lo hecho de forma autónoma cuenta como avance; lo demás, sin dato.
            efecto = o.get("efecto") or (Efecto.AVANCE if o.get("apoyo") == Apoyo.AUTONOMO else Efecto.SIN_DATO)
            if efecto not in Efecto.values or (grupal and efecto != Efecto.SIN_DATO):
                raise CommandError(f"Efecto inválido en la demo: «{efecto}» en «{o['cita'][:40]}».")
            estado = o.get("estado", Observacion.Estado.ACEPTADA)
            if estado not in (Observacion.Estado.ACEPTADA, Observacion.Estado.PENDIENTE) or (grupal and estado != Observacion.Estado.ACEPTADA):
                raise CommandError(f"Estado inválido en la demo: «{estado}» en «{o['cita'][:40]}».")
            if "autora" in o and o["autora"] not in usuarias:
                raise CommandError(f"Autora desconocida en la demo: «{o['autora']}».")
            # Un OA implica su núcleo.
            etiquetas += [oa.nucleo for oa in etiquetas_oa if oa.nucleo not in etiquetas]

            captura, _ = Captura.objects.update_or_create(
                curso=curso, tipo=Captura.Tipo.TEXTO, texto_original=o["cita"],
                defaults={
                    "autora": usuarias[o["autora"]] if "autora" in o else educadora,
                    "estado": Captura.Estado.PROCESADA,
                },
            )
            existente = Observacion.objects.filter(captura=captura).first()
            if existente and RegistroCambio.objects.filter(
                objeto_tipo=RegistroCambio.Objeto.OBSERVACION, objeto_id=existente.pk,
            ).exists():
                # La educadora la corrigió o la retiró: se respeta, y pisarla dejaría el
                # historial sin calzar (la ficha mostraría "se modificó por fuera de la app").
                continue
            observacion, _ = Observacion.objects.update_or_create(
                captura=captura,
                defaults={
                    "nino": nino,
                    "nombre_detectado": nino.nombre.split()[0] if nino else "",
                    "fecha": hoy - timedelta(days=o["hace_dias"]),
                    "cita": o["cita"],
                    "interpretacion": o.get("interpretacion", ""),
                    "apoyo": o.get("apoyo", "sin_dato"),
                    "efecto": efecto,
                    "grupal": grupal,
                    "estado": estado,
                },
            )
            observacion.nucleos.set(etiquetas)
            observacion.oas.set(etiquetas_oa)
        return Observacion.objects.filter(
            nino__curso=curso, estado=Observacion.Estado.ACEPTADA, grupal=False
        ).count()

    def _capturas_pendientes(self, curso, capturas, educadora, usuarias):
        """Notas escritas que quedan pendientes para que las ordene `procesar_capturas` con Bedrock real.

        No se escriben resultados de IA: solo el texto, como lo escribiría la educadora.
        Se identifican por su texto. Si ya existen (en cualquier estado, por ejemplo ya
        ordenadas en una demo anterior), no se tocan: volver a cargar no las duplica ni
        las devuelve a pendiente.
        """
        for c in capturas:
            if "autora" in c and c["autora"] not in usuarias:
                raise CommandError(f"Autora desconocida en la demo: «{c['autora']}».")
            Captura.objects.get_or_create(
                curso=curso, tipo=Captura.Tipo.TEXTO, texto_original=c["texto"],
                defaults={"autora": usuarias.get(c.get("autora"), educadora), "estado": Captura.Estado.PENDIENTE},
            )

    def _propuestas_solicitadas(self, curso, solicitudes, ninos):
        """Propuestas de nivel en estado "solicitada", para que las genere `procesar_propuestas` con Bedrock real.

        No se escribe ningún resultado de IA. Solo se pide si ese niño y núcleo
        nunca tuvo una propuesta: volver a cargar no duplica ni vuelve a pedir
        una que ya se generó o que la educadora ya decidió.
        """
        nucleos = {n.sigla: n for n in Nucleo.objects.all()}
        for s in solicitudes:
            nino, nucleo = ninos.get(s["nino"]), nucleos.get(s["nucleo"])
            if nino is None or nucleo is None:
                raise CommandError(f"Propuesta de demo para un niño o núcleo desconocido: {s}.")
            if not rubrica_completa(curso.nivel_educativo, nucleo):
                raise CommandError(f"{nucleo.sigla} no tiene una rúbrica completa: no se puede pedir una propuesta.")
            if not PropuestaNivel.objects.filter(nino=nino, nucleo=nucleo).exists():
                solicitar_propuesta(nino, nucleo)

    def _resultados_instrumentos(self, ninos, educadora):
        """Resultados ficticios de instrumentos (Task 14), confirmados y con su historial. Idempotente."""
        from registro.historial import registrar

        datos = json.loads(RUTA_DEMO_INSTRUMENTOS.read_text(encoding="utf-8"))
        instrumentos = {i.codigo: i for i in Instrumento.objects.all()}
        for r in datos["resultados"]:
            nino, instrumento = ninos.get(r["nino"]), instrumentos.get(r["instrumento"])
            fecha = date.fromisoformat(r["fecha_aplicacion"])
            if nino is None or instrumento is None or ResultadoInstrumento.objects.filter(
                nino=nino, instrumento=instrumento, fecha_aplicacion=fecha,
            ).exists():
                continue
            resultado = ResultadoInstrumento.objects.create(
                nino=nino, instrumento=instrumento, fecha_aplicacion=fecha, origen=r["origen"],
                aplicado_por=r.get("aplicado_por", ""), observaciones=r.get("observaciones", ""),
                valores=completar(instrumento.definicion, r["valores"], edad_en_dias(nino.fecha_nacimiento, fecha)),
                estado=ResultadoInstrumento.Estado.CONFIRMADO, registrado_por=educadora,
                confirmado_por=educadora, confirmado_en=timezone.now(),
            )
            registrar(resultado, RegistroCambio.Accion.CONFIRMAR, usuario=educadora, motivo="Datos de demo.")

    def _usuaria(self, datos, cambiar_password):
        User = get_user_model()
        usuaria, creada = User.objects.get_or_create(
            username=datos["usuario"],
            defaults={"first_name": datos["nombre"], "last_name": datos["apellido"], "email": datos["email"]},
        )
        if not (creada or cambiar_password):
            return usuaria
        desde_entorno = os.environ.get("DEMO_PASSWORD")
        password = desde_entorno or secrets.token_urlsafe(12)
        usuaria.set_password(password)
        usuaria.save()
        if not desde_entorno:
            # Solo se muestra si la generamos nosotros.
            self._passwords.append((usuaria.username, password))
        return usuaria
