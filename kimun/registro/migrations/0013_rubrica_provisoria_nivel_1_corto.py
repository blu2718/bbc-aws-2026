"""Nivel 1 de la rúbrica provisoria de Transición: descripción de una línea.

Antes, la descripción del nivel 1 llevaba pegado el párrafo de lo esperado al iniciar
NT1, y la opción 1 del formulario para fijar nivel quedaba mucho más larga que las demás.
Ahora ese párrafo va en `conducta`, como en `registro/rubrica.py`.

Solo cambia descriptores provisorios cuyo texto es exactamente el que generaba el código
anterior: no pisa los editados a mano ni los de la rúbrica de Integra. Los textos son una
copia de `registro/rubrica.py` a la fecha de la migración.
"""
from django.db import migrations

CRITERIO_NIVEL_1 = "Muestra lo esperado al iniciar NT1."


def acortar(apps, schema_editor):
    DescriptorNivel = apps.get_model("registro", "DescriptorNivel")
    descriptores = DescriptorNivel.objects.filter(
        nivel_educativo="transicion", nivel=1, provisorio=True,
    ).select_related("nucleo")
    for d in descriptores:
        esperado = d.nucleo.esperado_inicio_nt1
        if esperado and d.descripcion == f"{CRITERIO_NIVEL_1} {esperado}" and not d.conducta:
            # update() y no save(): el modelo histórico hereda ValidaNivelMixin sin
            # nivel_educativo_para_validar, y save() fallaría. El nivel no cambia.
            DescriptorNivel.objects.filter(pk=d.pk).update(
                descripcion=f"{CRITERIO_NIVEL_1} Núcleo: {d.nucleo.nombre}.", conducta=esperado,
            )


def alargar(apps, schema_editor):
    DescriptorNivel = apps.get_model("registro", "DescriptorNivel")
    descriptores = DescriptorNivel.objects.filter(
        nivel_educativo="transicion", nivel=1, provisorio=True,
    ).select_related("nucleo")
    for d in descriptores:
        esperado = d.nucleo.esperado_inicio_nt1
        if esperado and d.descripcion == f"{CRITERIO_NIVEL_1} Núcleo: {d.nucleo.nombre}." and d.conducta == esperado:
            DescriptorNivel.objects.filter(pk=d.pk).update(descripcion=f"{CRITERIO_NIVEL_1} {esperado}", conducta="")


class Migration(migrations.Migration):

    dependencies = [
        ("registro", "0012_instrumentos_e_historial"),
    ]

    operations = [
        migrations.RunPython(acortar, alargar),
    ]
