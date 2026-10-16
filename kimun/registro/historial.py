"""Historial de cambios a prueba de adulteración (Task 14).

Toda edición de un resultado de instrumento o de una observación aceptada pasa por
`registrar()`, que agrega un `RegistroCambio` con el estado completo antes y después,
quién, cuándo y por qué. Nada se sobrescribe sin dejar rastro:

- La app no permite modificar ni borrar entradas, y la base de datos rechaza los UPDATE
  (trigger de la migración 0012).
- Cada entrada lleva un SHA-256 de su contenido encadenado con el de la entrada anterior
  del mismo objeto. `verificar()` recalcula la cadena y compara el último estado
  registrado con el dato actual: si alguien borró o alteró una entrada, o cambió el dato
  por fuera de la app (SQL directo, panel de administración), la verificación falla y la
  pantalla del historial lo muestra.

No es una firma criptográfica: quien tenga acceso de escritura a la base y conozca el
algoritmo podría rehacer la cadena completa. Para eso habría que guardar el último hash
fuera de la base (por ejemplo, en un bucket con bloqueo de objetos), lo que queda fuera
del MVP.
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Observacion, RegistroCambio, ResultadoInstrumento


def _json(valor):
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _normalizar(valor):
    """El mismo dato antes y después de pasar por un JSONField (fechas a texto, tuplas a listas)."""
    return json.loads(_json(valor))


# --- Instantáneas -------------------------------------------------------------------


def instantanea_resultado(resultado):
    return _normalizar({
        "instrumento": resultado.instrumento.codigo if resultado.instrumento_id else None,
        "estado": resultado.estado,
        "origen": resultado.origen,
        "fecha_aplicacion": resultado.fecha_aplicacion,
        "aplicado_por": resultado.aplicado_por,
        "observaciones": resultado.observaciones,
        "valores": resultado.valores or {},
    })


def instantanea_observacion(obs):
    return _normalizar({
        "nino": obs.nino.nombre if obs.nino_id else None,
        "nino_id": obs.nino_id,
        "estado": obs.estado,
        "fecha": obs.fecha,
        "cita": obs.cita,
        "interpretacion": obs.interpretacion,
        "nucleos": sorted(obs.nucleos.values_list("sigla", flat=True)),
        "oas": sorted(oa.codigo for oa in obs.oas.select_related("nucleo")),
        "apoyo": obs.apoyo,
        "efecto": obs.efecto,
        "grupal": obs.grupal,
    })


def _tipo_y_curso(objeto):
    if isinstance(objeto, ResultadoInstrumento):
        return RegistroCambio.Objeto.RESULTADO, objeto.nino.curso_id, instantanea_resultado(objeto)
    if isinstance(objeto, Observacion):
        return RegistroCambio.Objeto.OBSERVACION, objeto.captura.curso_id, instantanea_observacion(objeto)
    raise TypeError(f"Sin historial para {type(objeto).__name__}.")


def instantanea(objeto):
    return _tipo_y_curso(objeto)[2]


# --- Cadena de hashes ---------------------------------------------------------------


def calcular_hash(*, hash_anterior, objeto_tipo, objeto_id, accion, usuario_id, motivo, antes, despues, creado):
    contenido = {
        "hash_anterior": hash_anterior, "objeto_tipo": objeto_tipo, "objeto_id": objeto_id,
        "accion": accion, "usuario_id": usuario_id, "motivo": motivo,
        "antes": antes, "despues": despues,
        "creado": creado.isoformat() if isinstance(creado, datetime) else str(creado),
    }
    return hashlib.sha256(_json(contenido).encode("utf-8")).hexdigest()


def _hash_de(entrada):
    return calcular_hash(
        hash_anterior=entrada.hash_anterior, objeto_tipo=entrada.objeto_tipo, objeto_id=entrada.objeto_id,
        accion=entrada.accion, usuario_id=entrada.usuario_id, motivo=entrada.motivo,
        antes=entrada.antes, despues=entrada.despues, creado=entrada.creado,
    )


def entradas(objeto_tipo, objeto_id):
    return RegistroCambio.objects.filter(objeto_tipo=objeto_tipo, objeto_id=objeto_id).order_by("creado", "id")


def registrar(objeto, accion, *, usuario=None, motivo="", antes=None):
    """Agrega una entrada al historial del objeto con su estado actual (ya guardado) como `despues`.

    `antes` es la instantánea previa al cambio (`instantanea(objeto)` tomada antes de
    editar); si se omite, se usa el `despues` de la última entrada. Debe llamarse dentro de
    la misma transacción que guardó el cambio, para que el dato y su historial queden juntos.
    """
    tipo, curso_id, despues = _tipo_y_curso(objeto)
    ultima = entradas(tipo, objeto.pk).last()
    if antes is None and ultima is not None:
        antes = ultima.despues
    creado = timezone.now().replace(microsecond=0)
    datos = {
        "hash_anterior": ultima.hash if ultima else "",
        "objeto_tipo": tipo, "objeto_id": objeto.pk, "accion": accion,
        "usuario_id": usuario.pk if usuario else None, "motivo": motivo.strip(),
        "antes": _normalizar(antes) if antes is not None else None, "despues": despues, "creado": creado,
    }
    try:
        with transaction.atomic():
            return RegistroCambio.objects.create(
                curso_id=curso_id,
                usuario_nombre=(usuario.get_full_name() or usuario.username) if usuario else "Kimün",
                hash=calcular_hash(**datos), **datos,
            )
    except IntegrityError as error:
        # Otra escritura colgó de la misma entrada al mismo tiempo: la cadena no se bifurca.
        raise ConflictoHistorial("Otra persona guardó un cambio al mismo tiempo. Vuelve a cargar la página.") from error


class ConflictoHistorial(Exception):
    pass


# --- Verificación -------------------------------------------------------------------


@dataclass
class Integridad:
    ok: bool
    total: int
    problemas: list = field(default_factory=list)

    @property
    def texto(self):
        if not self.total:
            return "Sin cambios registrados."
        if self.ok:
            return f"Historial íntegro: {self.total} cambio{'s' if self.total != 1 else ''} verificado{'s' if self.total != 1 else ''}."
        return "El historial no calza: " + " ".join(self.problemas)


# Estados por los que pasa una hoja mientras el proceso de fondo la lee (o si la lectura falla
# y se reintenta). Esos pasos no se registran: no son cambios del dato, y compararlos haría que
# la pantalla avise "se modificó por fuera de la app" mientras la hoja se lee.
_ESTADOS_DE_LECTURA = {
    ResultadoInstrumento.Estado.POR_LEER, ResultadoInstrumento.Estado.LEYENDO, ResultadoInstrumento.Estado.ERROR,
}


def _comparable(instantanea_):
    """Sin el nombre del niño, que es solo para leer el historial: renombrarlo no es adulterar el dato."""
    comparable = {k: v for k, v in (instantanea_ or {}).items() if k != "nino"}
    if comparable.get("origen") is not None and comparable.get("estado") in _ESTADOS_DE_LECTURA:
        comparable["estado"] = "lectura"  # solo los resultados tienen "origen"
    return comparable


def verificar(objeto):
    """Recalcula la cadena del objeto y la compara con su estado actual."""
    tipo, _, actual = _tipo_y_curso(objeto)
    lista = list(entradas(tipo, objeto.pk))
    problemas = []
    anterior = ""
    for i, entrada in enumerate(lista, start=1):
        if entrada.hash_anterior != anterior:
            problemas.append(f"Falta una entrada antes del cambio {i}.")
        if _hash_de(entrada) != entrada.hash:
            problemas.append(f"El cambio {i} fue alterado después de registrarse.")
        anterior = entrada.hash
    if lista and _comparable(lista[-1].despues) != _comparable(actual):
        problemas.append("El dato actual no coincide con el último cambio registrado: se modificó por fuera de la app.")
    return Integridad(ok=not problemas, total=len(lista), problemas=problemas)


# --- Cambios legibles ---------------------------------------------------------------

ETIQUETAS_OBSERVACION = {
    "nino": "Niño o niña", "estado": "Estado", "fecha": "Fecha", "cita": "Lo que hizo o dijo",
    "interpretacion": "Interpretación", "nucleos": "Núcleos", "oas": "OA", "apoyo": "Nivel de apoyo",
    "efecto": "Efecto", "grupal": "Nota del grupo",
}


def _etiquetar_observacion(clave):
    return ETIQUETAS_OBSERVACION.get(clave, clave)


_ESTADOS_OBSERVACION = dict(Observacion.Estado.choices)
_APOYOS = dict(Observacion._meta.get_field("apoyo").choices)
_EFECTOS = dict(Observacion._meta.get_field("efecto").choices)
_etiquetar_observacion.formatear = lambda clave, valor: {
    "estado": _ESTADOS_OBSERVACION, "apoyo": _APOYOS, "efecto": _EFECTOS,
}.get(clave, {}).get(valor, valor) if isinstance(valor, str) else valor


def _aplanar(datos, prefijo=""):
    plano = {}
    for clave, valor in (datos or {}).items():
        ruta = f"{prefijo}{clave}"
        if isinstance(valor, dict):
            plano.update(_aplanar(valor, f"{ruta}."))
        else:
            plano[ruta] = valor
    return plano


def _texto(valor):
    if valor in (None, "", []):
        return "–"
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, list):
        return ", ".join(str(v) for v in valor)
    return str(valor)


def diferencias(antes, despues, etiquetar=None):
    """[(campo legible, antes, después)] de lo que cambió entre dos instantáneas.

    Si `etiquetar` tiene el atributo `formatear(clave, valor)`, los valores se muestran con él
    (por ejemplo, "Por revisar" en vez de "por_revisar").
    """
    a, d = _aplanar(antes), _aplanar(despues)
    formatear = getattr(etiquetar, "formatear", None) or (lambda clave, valor: valor)
    filas = []
    for clave in sorted(set(a) | set(d)):
        if clave == "nino_id" or a.get(clave) == d.get(clave):
            continue
        etiqueta = etiquetar(clave) if etiquetar else clave
        filas.append((etiqueta, _texto(formatear(clave, a.get(clave))), _texto(formatear(clave, d.get(clave)))))
    return filas


@dataclass
class EntradaLegible:
    entrada: RegistroCambio
    cambios: list


def historial_legible(objeto, etiquetar=None):
    tipo, _, _ = _tipo_y_curso(objeto)
    if etiquetar is None and tipo == RegistroCambio.Objeto.OBSERVACION:
        etiquetar = _etiquetar_observacion
    return [
        EntradaLegible(e, diferencias(e.antes, e.despues, etiquetar) if e.antes is not None else [])
        for e in entradas(tipo, objeto.pk).select_related("usuario")
    ]


__all__ = [
    "ConflictoHistorial", "EntradaLegible", "Integridad", "calcular_hash", "diferencias", "entradas",
    "historial_legible", "instantanea", "registrar", "verificar",
]
