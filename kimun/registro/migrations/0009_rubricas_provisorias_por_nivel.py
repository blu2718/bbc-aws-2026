"""Rúbricas para las bases existentes.

1. Cada nivel educativo con cursos tiene su `Rubrica` (sin ella, las vistas del curso fallan).
2. Sala cuna y medio reciben la rúbrica provisoria sobre sus OA en los núcleos que tienen OA
   en ese nivel y aún no tienen descriptores (sin ellos, las propuestas de nivel fallan).

`cargar_demo` solo corre con la base vacía, por eso se hace aquí. Los textos son una copia
de `registro/rubrica.py` a la fecha de la migración. No pisa descriptores existentes.
"""
from django.db import migrations

NIVELES_PROVISORIOS = 8
MAPEO_PROVISORIO_OA = [
    (1, "Se inicia en los aprendizajes de los OA del núcleo: los muestra ocasionalmente y con ayuda."),
    (2, "Muestra algunas conductas de los OA del núcleo, con ayuda."),
    (3, "Muestra varias conductas de los OA del núcleo, con ayuda."),
    (4, "Muestra varias conductas de los OA del núcleo, algunas de forma autónoma."),
    (5, "Muestra la mayoría de las conductas de los OA del núcleo, con ayuda ocasional."),
    (6, "Muestra la mayoría de las conductas de los OA del núcleo de forma autónoma."),
    (7, "Muestra las conductas de todos los OA del núcleo, la mayoría de forma autónoma."),
    (8, "Muestra las conductas de todos los OA del núcleo de forma autónoma (lo esperado al terminar el nivel)."),
]


def crear_rubricas(apps, schema_editor):
    Curso = apps.get_model("registro", "Curso")
    Rubrica = apps.get_model("registro", "Rubrica")
    DescriptorNivel = apps.get_model("registro", "DescriptorNivel")
    Nucleo = apps.get_model("registro", "Nucleo")
    ObjetivoAprendizaje = apps.get_model("registro", "ObjetivoAprendizaje")

    for nivel_educativo in Curso.objects.values_list("nivel_educativo", flat=True).distinct():
        Rubrica.objects.get_or_create(
            nivel_educativo=nivel_educativo,
            defaults={"cantidad_niveles": NIVELES_PROVISORIOS, "provisoria": True},
        )

    for nivel_educativo in ("sala_cuna", "medio"):
        rubrica = Rubrica.objects.filter(nivel_educativo=nivel_educativo).first()
        if rubrica is None:
            continue
        con_oa = ObjetivoAprendizaje.objects.filter(nivel_educativo=nivel_educativo).values_list("nucleo_id", flat=True)
        for nucleo in Nucleo.objects.filter(pk__in=con_oa):
            if DescriptorNivel.objects.filter(nivel_educativo=nivel_educativo, nucleo=nucleo).exists():
                continue
            DescriptorNivel.objects.bulk_create(
                DescriptorNivel(
                    nivel_educativo=nivel_educativo, nucleo=nucleo, nivel=nivel, nombre=f"Nivel {nivel}",
                    descripcion=f"{texto} Núcleo: {nucleo.nombre}.", provisorio=True,
                )
                for nivel, texto in MAPEO_PROVISORIO_OA if nivel <= rubrica.cantidad_niveles
            )


class Migration(migrations.Migration):

    dependencies = [
        ('registro', '0008_captura_pregunta'),
    ]

    operations = [
        migrations.RunPython(crear_rubricas, migrations.RunPython.noop),
    ]
