"""Datos de la ficha del niño (PLAN.md, Task 3; spec `.kiro/specs/task3-ficha-nino`).

`armar_ficha` junta, por núcleo, el nivel actual, la rúbrica de ese nivel y del
siguiente, la evolución, la cobertura por OA, las observaciones aceptadas y el
formulario para fijar un nivel. Las plantillas solo muestran.

La comparación con lo esperado y con los pares viene de `registro/alertas.py`,
que entrega la Task 2. Mientras no exista, la ficha se arma igual y deja
`situacion` en None (ver `_situaciones`). Cuando llegue, se usa sin cambiar
este archivo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from django.utils import timezone

from .cobertura import CoberturaOA, cobertura_del_nino
from .forms import FijarNivelForm, etiqueta_nivel
from .grafico import Evolucion, evolucion_del_nino
from .models import DescriptorNivel, NivelValidado, Nino, Nucleo, Observacion, Rubrica
from .permisos import puede_validar

if TYPE_CHECKING:
    from .alertas import SituacionNucleo

# Textos del aviso de datos según `EstadoDatos.value` de alertas.py. Se compara
# por valor para no importar el módulo de la Task 2.
AVISOS_DATOS = {
    "sin_datos": "Sin observaciones aceptadas en este núcleo",
    "desactualizados": "Sin observaciones aceptadas en los últimos 14 días",
}
SIN_NIVEL = "Sin nivel validado"


@dataclass(frozen=True)
class NucleoFicha:
    nucleo: Nucleo
    actual: NivelValidado | None
    texto_actual: str                             # "3 · Desarrollando", o "3" si es provisorio
    descriptor_actual: DescriptorNivel | None
    descriptor_siguiente: DescriptorNivel | None  # None en el nivel máximo o si falta
    provisorio: bool                              # muestra la etiqueta "Rúbrica provisoria"
    situacion: SituacionNucleo | None             # None sin alertas.py o sin datos del núcleo
    evolucion: Evolucion
    cobertura: list[CoberturaOA]
    observaciones: list[Observacion]              # aceptadas, no grupales, más recientes primero
    form: FijarNivelForm | None                   # solo para la educadora del curso

    @property
    def pasos_sugeridos(self) -> str:
        return getattr(self.descriptor_actual, "pasos_sugeridos", "") or ""

    @property
    def aviso_datos(self) -> str:
        if self.situacion is None:
            return ""
        return AVISOS_DATOS.get(self.situacion.datos.value, "")

    @property
    def oas_con_evidencia(self) -> int:
        return sum(1 for c in self.cobertura if not c.sin_evidencia)


@dataclass(frozen=True)
class Ficha:
    nino: Nino
    nucleos: list[NucleoFicha]  # en el orden de Nucleo
    puede_validar: bool

    def nucleo(self, sigla: str) -> NucleoFicha:
        for nf in self.nucleos:
            if nf.nucleo.sigla == sigla:
                return nf
        raise KeyError(sigla)


def descriptores_vecinos(descriptores, nivel, nivel_maximo=None):
    """(descriptor del nivel, descriptor del nivel siguiente). Cualquiera puede ser None.

    No hay siguiente si el nivel ya es el máximo de la rúbrica, aunque quede un
    descriptor más alto de cuando la rúbrica tenía más niveles.
    """
    if nivel is None:
        return None, None
    siguiente = None
    if nivel_maximo is None or nivel < nivel_maximo:
        siguiente = descriptores.get(nivel + 1)
    return descriptores.get(nivel), siguiente


def es_provisorio(descriptores):
    """Verdadero si el núcleo no tiene descriptores o alguno es provisorio."""
    return not descriptores or any(d.provisorio for d in descriptores.values())


def _situaciones(curso, hoy: date):
    """Situación del curso según alertas.py, o {} mientras la Task 2 no lo entregue."""
    try:
        from .alertas import situacion_del_curso
    except ModuleNotFoundError as error:
        if error.name != f"{__package__}.alertas":
            raise  # falta otro módulo dentro de alertas.py: no se oculta
        return {}
    return situacion_del_curso(curso, hoy)


def descriptores_del_nucleo(nivel_educativo, nucleo):
    """{nivel: DescriptorNivel} de un núcleo."""
    return {d.nivel: d for d in DescriptorNivel.objects.filter(nivel_educativo=nivel_educativo, nucleo=nucleo)}


def armar_ficha(nino, usuario, hoy=None, formularios=None):
    """Ficha completa del niño. Cantidad fija de consultas.

    - formularios: {sigla: FijarNivelForm ligado}, para volver a mostrar uno con
      errores. Los demás se crean sin ligar, con el nivel actual marcado.
    """
    hoy = hoy or timezone.localdate()
    formularios = formularios or {}
    curso = nino.curso
    nivel_educativo = curso.nivel_educativo
    nivel_maximo = Rubrica.nivel_maximo(nivel_educativo)
    valida = puede_validar(usuario, curso)

    descriptores = {}
    for d in DescriptorNivel.objects.filter(nivel_educativo=nivel_educativo):
        descriptores.setdefault(d.nucleo_id, {})[d.nivel] = d
    nucleos = list(Nucleo.objects.all())
    nombres = {
        n.sigla: {nivel: d.nombre for nivel, d in descriptores.get(n.pk, {}).items() if not d.provisorio and d.nombre}
        for n in nucleos
    }

    evoluciones = evolucion_del_nino(nino, hasta=hoy, nombres=nombres)
    actuales = nino.niveles_actuales()
    cobertura = cobertura_del_nino(nino)
    observaciones = list(
        Observacion.objects.filter(nino=nino, estado=Observacion.Estado.ACEPTADA, grupal=False)
        .prefetch_related("nucleos")
        .order_by("-fecha", "-creada", "-id")
    )
    situaciones = _situaciones(curso, hoy).get(nino.pk, {})

    resultado = []
    for nucleo in nucleos:
        del_nucleo = descriptores.get(nucleo.pk, {})
        actual = actuales.get(nucleo.sigla)
        nivel = actual.nivel if actual else None
        descriptor_actual, descriptor_siguiente = descriptores_vecinos(del_nucleo, nivel, nivel_maximo)
        form = None
        if valida:
            form = formularios.get(nucleo.sigla) or FijarNivelForm(
                prefix=nucleo.sigla, initial={"nivel": nivel}, nivel_maximo=nivel_maximo, descriptores=del_nucleo,
            )
        resultado.append(NucleoFicha(
            nucleo=nucleo,
            actual=actual,
            texto_actual=etiqueta_nivel(nivel, descriptor_actual) if actual else SIN_NIVEL,
            descriptor_actual=descriptor_actual,
            descriptor_siguiente=descriptor_siguiente,
            provisorio=es_provisorio(del_nucleo),
            situacion=situaciones.get(nucleo.sigla),
            evolucion=evoluciones[nucleo.sigla],
            cobertura=cobertura.get(nucleo.sigla, []),
            observaciones=[o for o in observaciones if any(n.pk == nucleo.pk for n in o.nucleos.all())],
            form=form,
        ))
    return Ficha(nino=nino, nucleos=resultado, puede_validar=valida)
