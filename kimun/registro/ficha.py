"""Datos de la ficha del niño (PLAN.md, Task 3; spec `.kiro/specs/task3-ficha-nino`).

`armar_ficha` junta, por núcleo, el nivel actual, la rúbrica de ese nivel y del
siguiente, la evolución, la cobertura por OA, las observaciones aceptadas y el
formulario para fijar un nivel. Las plantillas solo muestran.

La comparación con lo esperado y con los pares sale de `alertas.tabla_del_curso`
(Task 2), la misma que usa la tabla del curso, para que la ficha y la tabla
muestren siempre las mismas señales.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from django.utils import timezone
from django.db.models import OuterRef, Prefetch, Subquery

from .alertas import DIAS_DATOS_RECIENTES, EstadoDatos, tabla_del_curso, texto_nivel_general
from .avanzar import ParaAvanzar, manifestaciones_por_oa, para_avanzar
from .cobertura import CoberturaOA, cobertura_del_nino
from .forms import FijarNivelForm, etiqueta_nivel
from .grafico import Evolucion, evolucion_del_nino
from .models import DescriptorNivel, NivelValidado, Nino, Nucleo, Observacion, PropuestaNivel, Rubrica
from .permisos import puede_validar
from .propuestas import niveles_completos

AVISOS_DATOS = {
    EstadoDatos.SIN_DATOS: "Sin observaciones aceptadas en este núcleo",
    EstadoDatos.DESACTUALIZADO: f"Sin observaciones aceptadas en los últimos {DIAS_DATOS_RECIENTES} días",
}
SIN_NIVEL = "Sin nivel validado"


@dataclass(frozen=True)
class SituacionNucleo:
    """Dónde está el niño en un núcleo frente al curso y a lo esperado.

    - senales: `alertas.Brecha` con texto (aviso o alerta), primero la de pares.
    """

    esperado: int | None
    mediana_curso: float | int | None
    texto_mediana: str
    senales: list
    datos: EstadoDatos


@dataclass(frozen=True)
class NucleoFicha:
    nucleo: Nucleo
    actual: NivelValidado | None
    texto_actual: str                             # "3 · Desarrollando", o "3" si es provisorio
    descriptor_actual: DescriptorNivel | None
    descriptor_siguiente: DescriptorNivel | None  # None en el nivel máximo o si falta
    provisorio: bool                              # muestra la etiqueta "Rúbrica provisoria"
    situacion: SituacionNucleo | None             # None si el niño o el núcleo no están en la tabla
    evolucion: Evolucion
    cobertura: list[CoberturaOA]
    observaciones: list[Observacion]              # aceptadas, no grupales, más recientes primero
    form: FijarNivelForm | None                   # solo para la educadora del curso
    propuesta: PropuestaNivel | None = None
    texto_propuesto: str = ""
    evidencia_propuesta: list = field(default_factory=list)
    form_propuesta: FijarNivelForm | None = None
    validacion_propuesta: NivelValidado | None = None
    texto_validado_propuesta: str = ""
    error_propuesta: str = ""
    texto_siguiente: str = ""                     # "4 · Afianzando", o "4" si es provisorio
    para_avanzar: ParaAvanzar = field(default_factory=ParaAvanzar)
    rubrica_completa: bool = True                 # sin ella no se pueden pedir propuestas

    @property
    def pasos_sugeridos(self) -> str:
        return getattr(self.descriptor_actual, "pasos_sugeridos", "") or ""

    @property
    def aviso_datos(self) -> str:
        if self.situacion is None:
            return ""
        return AVISOS_DATOS.get(self.situacion.datos, "")

    @property
    def oas_con_evidencia(self) -> int:
        return sum(1 for c in self.cobertura if not c.sin_evidencia)


@dataclass(frozen=True)
class Ficha:
    nino: Nino
    nucleos: list[NucleoFicha]  # en el orden de Nucleo
    puede_validar: bool

    @property
    def texto_nivel_general(self) -> str:
        """Promedio de los núcleos con nivel validado ("4,4"), como referencia. Igual que en la tabla del curso."""
        return texto_nivel_general([nf.actual.nivel if nf.actual else None for nf in self.nucleos])

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


def situaciones_desde_tabla(tabla):
    """{id del niño: {sigla: SituacionNucleo}} a partir de `alertas.TablaCurso`. Pura."""
    medianas = {d.nucleo.sigla: d for d in tabla.distribuciones}
    resultado = {}
    for fila in tabla.filas:
        por_nucleo = {}
        for celda in fila.celdas:
            d = medianas.get(celda.nucleo.sigla)
            por_nucleo[celda.nucleo.sigla] = SituacionNucleo(
                esperado=fila.nivel_esperado,
                mediana_curso=d.mediana if d else None,
                texto_mediana=d.texto_mediana if d else "–",
                senales=celda.senales,
                datos=celda.datos,
            )
        resultado[fila.nino.pk] = por_nucleo
    return resultado


def _situaciones(curso, hoy: date):
    """Situación de todos los niños del curso, con la misma tabla que la vista del curso."""
    return situaciones_desde_tabla(tabla_del_curso(curso, hoy=hoy))


def _nucleos_de(observacion):
    """Ids de los núcleos de una observación: los etiquetados y los de sus OA, como en alertas.py."""
    return {n.pk for n in observacion.nucleos.all()} | {oa.nucleo_id for oa in observacion.oas.all()}


def descriptores_del_nucleo(nivel_educativo, nucleo):
    """{nivel: DescriptorNivel} de un núcleo."""
    return {d.nivel: d for d in DescriptorNivel.objects.filter(nivel_educativo=nivel_educativo, nucleo=nucleo)}


def armar_ficha(nino, usuario, hoy=None, formularios=None, formularios_propuesta=None, errores_propuesta=None):
    """Ficha completa del niño. Cantidad fija de consultas.

    - formularios: {sigla: FijarNivelForm ligado}, para volver a mostrar uno con
      errores. Los demás se crean sin ligar, con el nivel actual marcado.
    """
    hoy = hoy or timezone.localdate()
    formularios = formularios or {}
    formularios_propuesta = formularios_propuesta or {}
    errores_propuesta = errores_propuesta or {}
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
    manifestaciones = manifestaciones_por_oa(nivel_educativo=nivel_educativo)
    observaciones = list(
        Observacion.objects.filter(nino=nino, estado=Observacion.Estado.ACEPTADA, grupal=False)
        .prefetch_related("nucleos", "oas")
        .order_by("-fecha", "-creada", "-id")
    )
    situaciones = _situaciones(curso, hoy).get(nino.pk, {})
    propuestas = {}
    if valida:
        ultima = PropuestaNivel.objects.filter(nino=nino, nucleo_id=OuterRef("nucleo_id")).order_by("-creada", "-pk")
        candidatas = PropuestaNivel.objects.filter(nino=nino, pk=Subquery(ultima.values("pk")[:1])).select_related(
            "resuelta_por",
        ).prefetch_related(
            Prefetch("observaciones_citadas", queryset=Observacion.objects.only("pk").order_by("pk"), to_attr="_citas_ficha"),
            Prefetch("validaciones", queryset=NivelValidado.objects.order_by("pk"), to_attr="_validaciones_ficha"),
        )
        propuestas = {p.nucleo_id: p for p in candidatas}

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
        propuesta = propuestas.get(nucleo.pk)
        observaciones_nucleo = [o for o in observaciones if nucleo.pk in _nucleos_de(o)]
        form_propuesta, evidencia_propuesta, validacion_propuesta = None, [], None
        texto_propuesto, texto_validado = "", ""
        if propuesta:
            if propuesta.nivel is not None:
                texto_propuesto = etiqueta_nivel(propuesta.nivel, None if propuesta.rubrica_provisoria else del_nucleo.get(propuesta.nivel))
            citadas = {o.pk for o in propuesta._citas_ficha}
            evidencia_propuesta = [o for o in observaciones_nucleo if o.pk in citadas]
            validacion_propuesta = next(iter(propuesta._validaciones_ficha), None)
            if validacion_propuesta:
                texto_validado = etiqueta_nivel(validacion_propuesta.nivel, del_nucleo.get(validacion_propuesta.nivel))
            if propuesta.estado == PropuestaNivel.Estado.LISTA and propuesta.evidencia_suficiente:
                form_propuesta = formularios_propuesta.get(propuesta.pk) or FijarNivelForm(
                    prefix=f"propuesta-{propuesta.pk}", initial={"nivel": propuesta.nivel},
                    nivel_maximo=nivel_maximo, descriptores=del_nucleo,
                )
        provisorio = es_provisorio(del_nucleo)
        cobertura_nucleo = cobertura.get(nucleo.sigla, [])
        resultado.append(NucleoFicha(
            nucleo=nucleo,
            actual=actual,
            texto_actual=etiqueta_nivel(nivel, descriptor_actual) if actual else SIN_NIVEL,
            descriptor_actual=descriptor_actual,
            descriptor_siguiente=descriptor_siguiente,
            texto_siguiente=etiqueta_nivel(descriptor_siguiente.nivel, descriptor_siguiente) if descriptor_siguiente else "",
            para_avanzar=para_avanzar(
                cobertura_nucleo, manifestaciones,
                descriptor_siguiente.nivel if descriptor_siguiente else None, provisorio,
            ),
            provisorio=provisorio,
            situacion=situaciones.get(nucleo.sigla),
            evolucion=evoluciones[nucleo.sigla],
            cobertura=cobertura_nucleo,
            observaciones=observaciones_nucleo,
            form=form,
            propuesta=propuesta, texto_propuesto=texto_propuesto, evidencia_propuesta=evidencia_propuesta,
            form_propuesta=form_propuesta, validacion_propuesta=validacion_propuesta,
            texto_validado_propuesta=texto_validado, error_propuesta=errores_propuesta.get(nucleo.sigla, ""),
            rubrica_completa=niveles_completos(del_nucleo, nivel_maximo),
        ))
    return Ficha(nino=nino, nucleos=resultado, puede_validar=valida)
