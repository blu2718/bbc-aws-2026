"""Informe para la familia (Política de Calidad de Integra, pp. 59 y 96: socializar los resultados de aprendizaje).

Una página imprimible por niño, que arma la educadora con lo que ya validó. No usa IA:
sale de la misma ficha (`ficha.armar_ficha`).

- Por núcleo: el nivel que fijó la educadora (no el nivel 1 automático del ingreso),
  hasta dos observaciones aceptadas recientes que muestran avance o no tienen efecto
  marcado, y en qué se está trabajando (el nivel siguiente de la rúbrica de Integra o,
  en la provisoria, conductas del Programa Pedagógico de los OA sin evidencia).
- No incluye señales de revisión, mediana del curso, nivel esperado ni comparaciones
  con otros niños: es para la familia, no un diagnóstico.
- Las citas pueden nombrar a otros niños del curso: se reemplazan por "un compañero
  o compañera" con el `Seudonimizador` de la Task 7, que reconoce nombres, apellidos y alias.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ia.seudonimo import MARCADOR_AMBIGUO, Seudonimizador
from .models import Efecto, Nino

# Para que quepa en una página A4 con 8 núcleos.
OBSERVACIONES_POR_NUCLEO = 1
CONDUCTAS_POR_NUCLEO = 1
OTRO_NINO = "un compañero o compañera"
NINO_SIN_PRECISAR = "un niño o niña"
_CODIGO = re.compile(r"N-[0-9A-F]{6}")


@dataclass(frozen=True)
class NucleoInforme:
    nucleo: object
    texto_nivel: str            # "3 · Desarrollando", o "" si la educadora todavía no fija un nivel
    descripcion: str            # qué describe ese nivel en la rúbrica de Integra; "" en la provisoria
    observaciones: list         # [(fecha, cita)] con los otros niños sin nombre
    trabajando: list = field(default_factory=list)  # textos de qué se está trabajando


@dataclass(frozen=True)
class Informe:
    nino: object
    nucleos: list

    @property
    def nombre_de_pila(self):
        return self.nino.nombre.split()[0]


class Anonimizador:
    """Deja el nombre del niño y reemplaza el de los demás niños del curso en una cita."""

    def __init__(self, nino):
        identidades = list(Nino.objects.filter(curso_id=nino.curso_id).values("codigo", "nombre", "alias"))
        self._propio = nino.codigo
        self._pila = nino.nombre.split()[0]
        self._seudonimizador = Seudonimizador(identidades)

    def texto(self, cita):
        con_codigos = self._seudonimizador.texto(cita)

        def reemplazo(coincidencia):
            return self._pila if coincidencia.group(0) == self._propio else OTRO_NINO

        return _CODIGO.sub(reemplazo, con_codigos).replace(MARCADOR_AMBIGUO, NINO_SIN_PRECISAR)


def armar_informe(ficha):
    """`Informe` a partir de una `ficha.Ficha` ya armada. Solo transforma; la única consulta es la del curso."""
    anonimizador = Anonimizador(ficha.nino)
    nucleos = []
    usadas = set()  # una observación con varios núcleos se muestra solo en el primero
    for nf in ficha.nucleos:
        validado = nf.actual is not None and nf.actual.validado_por_id is not None
        descripcion = ""
        if validado and nf.descriptor_actual and not nf.descriptor_actual.provisorio:
            descripcion = nf.descriptor_actual.descripcion
        elegidas = [
            o for o in nf.observaciones if o.efecto != Efecto.POR_REFORZAR and o.pk not in usadas
        ][:OBSERVACIONES_POR_NUCLEO]
        usadas.update(o.pk for o in elegidas)
        observaciones = [(o.fecha, anonimizador.texto(o.cita)) for o in elegidas]
        trabajando = []
        if nf.descriptor_siguiente and not nf.descriptor_siguiente.provisorio:
            trabajando = [nf.descriptor_siguiente.descripcion]
        elif nf.para_avanzar.prioritarias:
            trabajando = [c for oa in nf.para_avanzar.prioritarias for c in oa.conductas][:CONDUCTAS_POR_NUCLEO]
        nucleos.append(NucleoInforme(
            nucleo=nf.nucleo, texto_nivel=nf.texto_actual if validado else "", descripcion=descripcion,
            observaciones=observaciones, trabajando=trabajando,
        ))
    return Informe(nino=ficha.nino, nucleos=nucleos)
