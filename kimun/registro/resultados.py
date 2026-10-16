"""Cargar, revisar, corregir y descartar resultados de instrumentos (Task 14).

Toda acción guarda el dato y su entrada en el historial (`historial.registrar`) en la
misma transacción. Una corrección de un resultado ya confirmado exige un motivo. Para
evitar que dos personas se pisen, el formulario lleva el id del último cambio que vio
quien edita; si al guardar hay uno más nuevo, se rechaza.

También están aquí las correcciones de observaciones ya aceptadas (la educadora corrige
un error después de aceptarla), con el mismo historial.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from .historial import entradas, instantanea, registrar
from .ia.instrumento import HojaInvalida, validar_hoja
from .instrumentos import (
    MAX_AREAS_LIBRES, categoria_area, completar, edad_en_dias, normalizar_campo,
)
from .models import Instrumento, Observacion, RegistroCambio, ResultadoInstrumento
from .revision import ObservacionForm

FILAS_AREAS_LIBRES = 6
EXTENSIONES_HOJA = {"jpeg": "jpg", "png": "png", "gif": "gif", "webp": "webp"}


class CambioConcurrente(ValidationError):
    pass


def ultimo_cambio_id(objeto_tipo, objeto_id):
    ultima = entradas(objeto_tipo, objeto_id).last()
    return ultima.pk if ultima else 0


def _revisar_version(objeto_tipo, objeto_id, visto):
    if str(ultimo_cambio_id(objeto_tipo, objeto_id)) != str(visto or 0):
        raise CambioConcurrente("Alguien guardó un cambio mientras editabas. Revisa los datos actuales y vuelve a guardar.")


# --- Formularios ------------------------------------------------------------------------


class SubirHojaForm(forms.Form):
    instrumento = forms.ModelChoiceField(
        queryset=Instrumento.objects.all(), required=False, label="Instrumento",
        empty_label="Que Kimün lo reconozca en la hoja",
    )
    origen = forms.ChoiceField(choices=ResultadoInstrumento.Origen.choices, label="¿Dónde se aplicó?")
    hoja = forms.FileField(
        label="Foto o PDF de la hoja de resultados",
        widget=forms.FileInput(attrs={"accept": "image/*,application/pdf", "aria-describedby": "ayuda-hoja estado-foto"}),
        error_messages={"required": "Toma una foto de la hoja o elige un PDF.", "empty": "El archivo está vacío."},
    )

    def clean_hoja(self):
        archivo = self.cleaned_data["hoja"]
        if archivo.size > 5_000_000:
            raise ValidationError("El archivo pesa más de 5 MB. Toma la foto desde esta página, que la achica.")
        contenido = archivo.read()
        try:
            tipo, formato = validar_hoja(contenido)
        except HojaInvalida as error:
            raise ValidationError(str(error)) from error
        self.contenido = contenido
        self.extension = "pdf" if tipo == "pdf" else EXTENSIONES_HOJA[formato]
        return archivo


class ResultadoForm(forms.Form):
    """Los campos salen de la definición del instrumento: nada está fijo en el código."""

    fecha_aplicacion = forms.DateField(
        label="Fecha de aplicación", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    origen = forms.ChoiceField(choices=ResultadoInstrumento.Origen.choices, label="¿Dónde se aplicó?")
    aplicado_por = forms.CharField(label="Aplicado por (cargo o centro)", required=False, max_length=120)
    observaciones = forms.CharField(label="Observaciones de la hoja", required=False, max_length=2000,
                                    widget=forms.Textarea(attrs={"rows": 2}))
    motivo = forms.CharField(label="Motivo de la corrección", required=False, max_length=500,
                             widget=forms.Textarea(attrs={"rows": 2}))
    version = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, instrumento, resultado=None, requiere_motivo=False, nacimiento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instrumento, self.defi, self.resultado = instrumento, instrumento.definicion, resultado
        self.requiere_motivo, self.nacimiento = requiere_motivo, nacimiento
        self.fields["motivo"].required = requiere_motivo
        if requiere_motivo:
            self.fields["motivo"].help_text = "Queda en el historial: por ejemplo, «el puntaje T de Lenguaje estaba mal copiado»."
        valores = (resultado.valores if resultado else None) or {}
        if resultado and not self.is_bound:
            self.initial.update({
                "fecha_aplicacion": resultado.fecha_aplicacion, "origen": resultado.origen,
                "aplicado_por": resultado.aplicado_por, "observaciones": resultado.observaciones,
                "version": ultimo_cambio_id(RegistroCambio.Objeto.RESULTADO, resultado.pk),
            })
        self.nombres_campos, self.nombres_area = [], []
        for campo in self.defi.get("campos", []):
            nombre = f"campo__{campo['codigo']}"
            self.fields[nombre] = self._campo(campo, (valores.get("campos") or {}).get(campo["codigo"]))
            self.nombres_campos.append(nombre)
        cat = self.defi.get("categoria")
        if cat:
            self.fields["categoria"] = self._opciones(cat["nombre"], cat["opciones"], valores.get("categoria"))
        cat_a = categoria_area(self.defi)
        for area in self.defi.get("areas", []):
            fila = (valores.get("areas") or {}).get(area["codigo"], {})
            nombres = []
            for campo in self.defi.get("campos_area", []):
                nombre = f"area__{area['codigo']}__{campo['codigo']}"
                self.fields[nombre] = self._campo(campo, fila.get(campo["codigo"]), area)
                nombres.append(nombre)
            if cat_a:
                nombre = f"cat_area__{area['codigo']}"
                self.fields[nombre] = self._opciones(
                    "Resultado", cat_a["opciones"], (valores.get("categorias_area") or {}).get(area["codigo"]),
                )
                nombres.append(nombre)
            self.nombres_area.append((area, nombres))
        self.nombres_libres = []
        if self.defi.get("areas_libres"):
            libres = valores.get("areas_libres") or []
            for i in range(max(FILAS_AREAS_LIBRES, len(libres))):
                previo = libres[i] if i < len(libres) else {}
                fila = [f"libre__{i}__nombre"]
                self.fields[fila[0]] = forms.CharField(label="Área o escala", required=False, max_length=80,
                                                       initial=previo.get("nombre"))
                for campo in self.defi.get("campos_area", []):
                    nombre = f"libre__{i}__{campo['codigo']}"
                    self.fields[nombre] = self._campo(campo, previo.get(campo["codigo"]))
                    fila.append(nombre)
                self.nombres_libres.append(fila)

    def _campo(self, campo, inicial, area=None):
        if campo["tipo"] == "opcion":
            return self._opciones(campo["nombre"], campo["opciones"], inicial)
        atributos = {"inputmode": "decimal" if campo.get("decimales") else "numeric"} if campo["tipo"] == "numero" else {}
        ayuda = ""
        if campo["tipo"] == "numero":
            ayuda = f"De {campo.get('min', 0)} a {area.get('maximos', {}).get(campo['codigo'], campo.get('max')) if area else campo.get('max')}."
            if campo.get("calculo"):
                ayuda += " Si la dejas vacía, Kimün la calcula."
        texto = "" if inicial is None else str(inicial).replace(".", ",") if isinstance(inicial, float) else str(inicial)
        return forms.CharField(label=campo["nombre"], required=False, initial=texto, help_text=ayuda,
                               widget=forms.TextInput(attrs=atributos), max_length=campo.get("max_largo", 40))

    def _opciones(self, etiqueta, opciones, inicial):
        return forms.ChoiceField(label=etiqueta, required=False, initial=inicial or "",
                                 choices=[("", "Sin dato")] + [(o["codigo"], o["nombre"]) for o in opciones])

    def clean_fecha_aplicacion(self):
        fecha = self.cleaned_data["fecha_aplicacion"]
        if fecha > timezone.localdate():
            raise ValidationError("La fecha no puede ser posterior a hoy.")
        if self.nacimiento and fecha < self.nacimiento:
            raise ValidationError("La fecha es anterior al nacimiento del niño o niña.")
        return fecha

    def clean(self):
        datos = super().clean()
        valores = {"campos": {}, "areas": {}, "categorias_area": {}}
        for campo in self.defi.get("campos", []):
            nombre = f"campo__{campo['codigo']}"
            valor, problema = normalizar_campo(campo, datos.get(nombre))
            if problema:
                self.add_error(nombre, problema)
            elif valor is not None:
                valores["campos"][campo["codigo"]] = valor
        if datos.get("categoria"):
            valores["categoria"] = datos["categoria"]
        for area, _ in self.nombres_area:
            fila = {}
            for campo in self.defi.get("campos_area", []):
                nombre = f"area__{area['codigo']}__{campo['codigo']}"
                valor, problema = normalizar_campo(campo, datos.get(nombre), area)
                if problema:
                    self.add_error(nombre, problema)
                elif valor is not None:
                    fila[campo["codigo"]] = valor
            if fila:
                valores["areas"][area["codigo"]] = fila
            if datos.get(f"cat_area__{area['codigo']}"):
                valores["categorias_area"][area["codigo"]] = datos[f"cat_area__{area['codigo']}"]
        if self.nombres_libres:
            libres = []
            for fila in self.nombres_libres[:MAX_AREAS_LIBRES]:
                nombre = (datos.get(fila[0]) or "").strip()
                if not nombre:
                    continue
                item = {"nombre": nombre}
                for campo, clave in zip(self.defi.get("campos_area", []), fila[1:]):
                    valor, _ = normalizar_campo(campo, datos.get(clave))
                    if valor is not None:
                        item[campo["codigo"]] = valor
                libres.append(item)
            valores["areas_libres"] = libres
        if not self.errors:
            self.valores = completar(self.defi, valores, edad_en_dias(self.nacimiento, datos.get("fecha_aplicacion")))
        return datos

    def grupos_area(self):
        """[(área, [campos ligados])] para la tabla de áreas."""
        return [(area, [self[n] for n in nombres]) for area, nombres in self.nombres_area]

    def campos_globales(self):
        return [self[n] for n in self.nombres_campos]

    def filas_libres(self):
        return [[self[n] for n in fila] for fila in self.nombres_libres]

    def columnas_area(self):
        columnas = [c["nombre"] for c in self.defi.get("campos_area", [])]
        return columnas + (["Resultado"] if categoria_area(self.defi) else [])


class CorregirObservacionForm(ObservacionForm):
    """Corrección de una observación ya aceptada: los mismos campos más el motivo y la versión."""

    motivo = forms.CharField(label="Motivo de la corrección", max_length=500, widget=forms.Textarea(attrs={"rows": 2}),
                             help_text="Queda en el historial de la observación.")
    version = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["version"] = ultimo_cambio_id(RegistroCambio.Objeto.OBSERVACION, self.instance.pk)


# --- Acciones ---------------------------------------------------------------------------


@transaction.atomic
def subir_hoja(nino, usuario, form):
    resultado = ResultadoInstrumento(
        nino=nino, instrumento=form.cleaned_data.get("instrumento"), origen=form.cleaned_data["origen"],
        estado=ResultadoInstrumento.Estado.POR_LEER, registrado_por=usuario,
    )
    resultado.archivo.save(f"hoja.{form.extension}", ContentFile(form.contenido), save=False)
    resultado.save()
    registrar(resultado, RegistroCambio.Accion.CREAR, usuario=usuario, motivo="Hoja subida para que Kimün la lea.")
    return resultado


def _aplicar_formulario(resultado, form):
    datos = form.cleaned_data
    resultado.instrumento = form.instrumento
    resultado.fecha_aplicacion = datos["fecha_aplicacion"]
    resultado.origen = datos["origen"]
    resultado.aplicado_por = datos.get("aplicado_por", "")
    resultado.observaciones = datos.get("observaciones", "")
    resultado.valores = form.valores


@transaction.atomic
def crear_manual(nino, usuario, form):
    """Ingreso a mano: la educadora lo escribe y confirma en el mismo paso."""
    resultado = ResultadoInstrumento(nino=nino, registrado_por=usuario)
    _aplicar_formulario(resultado, form)
    resultado.estado = ResultadoInstrumento.Estado.CONFIRMADO
    resultado.confirmado_por, resultado.confirmado_en = usuario, timezone.now()
    resultado.save()
    registrar(resultado, RegistroCambio.Accion.CREAR, usuario=usuario, motivo="Ingresado a mano y confirmado.")
    return resultado


@transaction.atomic
def guardar(resultado, usuario, form, *, confirmar=False):
    """Guarda lo revisado. Si estaba por revisar y `confirmar`, lo confirma; si ya estaba confirmado, es una corrección."""
    resultado = ResultadoInstrumento.objects.select_for_update().select_related("nino__curso", "instrumento").get(pk=resultado.pk)
    _revisar_version(RegistroCambio.Objeto.RESULTADO, resultado.pk, form.cleaned_data.get("version"))
    era_confirmado = resultado.estado == ResultadoInstrumento.Estado.CONFIRMADO
    if resultado.estado not in (ResultadoInstrumento.Estado.POR_REVISAR, ResultadoInstrumento.Estado.CONFIRMADO):
        raise ValidationError("Este resultado no se puede editar en su estado actual.")
    antes = instantanea(resultado)
    _aplicar_formulario(resultado, form)
    if era_confirmado:
        accion = RegistroCambio.Accion.EDITAR
    elif confirmar:
        accion = RegistroCambio.Accion.CONFIRMAR
        resultado.estado = ResultadoInstrumento.Estado.CONFIRMADO
        resultado.confirmado_por, resultado.confirmado_en = usuario, timezone.now()
        resultado.avisos = []
    else:
        accion = RegistroCambio.Accion.EDITAR
    if instantanea(resultado) == antes and accion == RegistroCambio.Accion.EDITAR:
        return resultado, False
    resultado.save()
    registrar(resultado, accion, usuario=usuario, motivo=form.cleaned_data.get("motivo", ""), antes=antes)
    return resultado, True


@transaction.atomic
def descartar(resultado, usuario, motivo):
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError("Escribe por qué se descarta: queda en el historial.")
    resultado = ResultadoInstrumento.objects.select_for_update().select_related("nino__curso", "instrumento").get(pk=resultado.pk)
    if resultado.estado == ResultadoInstrumento.Estado.DESCARTADO:
        return resultado
    if resultado.estado in (ResultadoInstrumento.Estado.POR_LEER, ResultadoInstrumento.Estado.LEYENDO):
        raise ValidationError("Espera a que Kimün termine de leer la hoja.")
    antes = instantanea(resultado)
    resultado.estado = ResultadoInstrumento.Estado.DESCARTADO
    resultado.save()
    registrar(resultado, RegistroCambio.Accion.DESCARTAR, usuario=usuario, motivo=motivo, antes=antes)
    transaction.on_commit(lambda: resultado.archivo and resultado.archivo.delete(save=False))
    return resultado


@transaction.atomic
def corregir_observacion(obs, usuario, form):
    """Guarda la corrección de una observación aceptada, con su motivo en el historial."""
    # El formulario ya aplicó los cambios a `form.instance`: el estado anterior se lee de la base.
    actual = Observacion.objects.select_for_update().select_related("captura__curso", "nino").get(pk=obs.pk)
    if actual.estado != Observacion.Estado.ACEPTADA:
        raise ValidationError("Solo se corrigen observaciones aceptadas.")
    _revisar_version(RegistroCambio.Objeto.OBSERVACION, obs.pk, form.cleaned_data.get("version"))
    antes = instantanea(actual)
    obs = form.save()
    if instantanea(obs) == antes:
        return obs, False
    registrar(obs, RegistroCambio.Accion.EDITAR, usuario=usuario, motivo=form.cleaned_data["motivo"], antes=antes)
    return obs, True


@transaction.atomic
def retirar_observacion(obs, usuario, motivo):
    """Saca de la ficha una observación aceptada por error (por ejemplo, de otro niño). Queda en el historial."""
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError("Escribe por qué se retira: queda en el historial.")
    obs = Observacion.objects.select_for_update().select_related("captura__curso", "nino").get(pk=obs.pk)
    if obs.estado != Observacion.Estado.ACEPTADA:
        raise ValidationError("Solo se retiran observaciones aceptadas.")
    antes = instantanea(obs)
    obs.estado = Observacion.Estado.DESCARTADA
    obs.save(update_fields=["estado", "actualizada"])
    registrar(obs, RegistroCambio.Accion.DESCARTAR, usuario=usuario, motivo=motivo, antes=antes)
    return obs
