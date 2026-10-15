"""Carga el currículo de Transición, la rúbrica de Integra y un curso de demo con 15 niños ficticios.

La rúbrica de Integra (`datos/rubrica_integra.json`) se carga después del
currículo y reemplaza a la provisoria en los núcleos que trae (hoy, IA).

Se puede correr varias veces: actualiza lo existente y no duplica datos.
Las contraseñas de la educadora y las asistentes se toman de DEMO_PASSWORD o
se generan al azar, y solo se fijan al crear cada usuaria (o con
--cambiar-password).
"""
import json
import os
import secrets
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from registro.curriculo import cargar_curriculo, leer_curriculo
from registro.models import Curso, Jardin, MetaSemestre, Nino, Semestre
from registro.rubrica_integra import cargar_rubrica_integra, leer_rubrica_integra

RUTA_DEMO = Path(settings.DATOS_DIR) / "demo_curso.json"


class Command(BaseCommand):
    help = "Carga currículo, rúbricas (provisoria y de Integra), semestres y un curso de demo (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", type=Path, default=RUTA_DEMO, help="JSON con el curso de demo.")
        parser.add_argument(
            "--cambiar-password", action="store_true",
            help="Vuelve a fijar las contraseñas de las usuarias de demo aunque ya existan.",
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
        demo = json.loads(Path(opciones["demo"]).read_text(encoding="utf-8"))
        self._passwords = []

        for s in demo["semestres"]:
            Semestre.objects.update_or_create(
                nombre=s["nombre"],
                defaults={"inicio": date.fromisoformat(s["inicio"]), "fin": date.fromisoformat(s["fin"])},
            )

        cambiar = opciones["cambiar_password"]
        educadora = self._usuaria(demo["educadora"], cambiar)
        asistentes = [self._usuaria(a, cambiar) for a in demo.get("asistentes", [])]

        jardin, _ = Jardin.objects.get_or_create(nombre=demo["jardin"])
        c = demo["curso"]
        curso, _ = Curso.objects.update_or_create(
            jardin=jardin, nombre=c["nombre"],
            defaults={"nivel_educativo": c["nivel_educativo"], "educadora": educadora},
        )
        curso.asistentes.set(asistentes)
        for semestre, nivel in c["metas"].items():
            MetaSemestre.objects.update_or_create(
                curso=curso, semestre_permanencia=int(semestre), defaults={"nivel_esperado": nivel}
            )

        for n in demo["ninos"]:
            nino = Nino.objects.filter(curso=curso, nombre=n["nombre"]).first()
            if nino is None:
                # save() crea el nivel 1 en todos los núcleos.
                Nino.objects.create(
                    curso=curso, nombre=n["nombre"], alias=n["alias"],
                    fecha_ingreso=date.fromisoformat(n["fecha_ingreso"]),
                )
            else:
                nino.alias = n["alias"]
                nino.fecha_ingreso = date.fromisoformat(n["fecha_ingreso"])
                nino.save(update_fields=["alias", "fecha_ingreso"])

        nombres = ", ".join(u.username for u in [educadora, *asistentes])
        self.stdout.write(self.style.SUCCESS(
            f"Demo cargada: {curso} con {curso.ninos.count()} niños. Usuarias: {nombres}"
        ))
        for usuario, password in self._passwords:
            self.stdout.write(f"Contraseña de {usuario}: {password}")

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
