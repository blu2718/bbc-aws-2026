from django.contrib import admin

from . import models


class ManifestacionInline(admin.TabularInline):
    model = models.Manifestacion
    extra = 0


@admin.register(models.Rubrica)
class RubricaAdmin(admin.ModelAdmin):
    list_display = ["nivel_educativo", "cantidad_niveles", "provisoria"]


@admin.register(models.Nucleo)
class NucleoAdmin(admin.ModelAdmin):
    list_display = ["sigla", "nombre", "orden"]


@admin.register(models.DescriptorNivel)
class DescriptorNivelAdmin(admin.ModelAdmin):
    list_display = ["nucleo", "nivel", "nombre", "nivel_educativo", "provisorio"]
    list_filter = ["nivel_educativo", "nucleo", "provisorio"]
    search_fields = ["nombre", "descripcion", "conducta", "pasos_sugeridos"]


@admin.register(models.ObjetivoAprendizaje)
class ObjetivoAprendizajeAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nivel_educativo", "texto"]
    list_filter = ["nivel_educativo", "nucleo"]
    search_fields = ["texto"]
    inlines = [ManifestacionInline]


@admin.register(models.Manifestacion)
class ManifestacionAdmin(admin.ModelAdmin):
    list_display = ["oa", "anio", "orden", "texto"]
    list_filter = ["anio", "oa__nucleo"]
    search_fields = ["texto"]


class CursoInline(admin.TabularInline):
    model = models.Curso
    extra = 0
    fields = ["nombre", "nivel_educativo", "educadora"]


@admin.register(models.Jardin)
class JardinAdmin(admin.ModelAdmin):
    list_display = ["nombre", "directora"]
    inlines = [CursoInline]


class MetaSemestreInline(admin.TabularInline):
    model = models.MetaSemestre
    extra = 0


class NinoInline(admin.TabularInline):
    model = models.Nino
    extra = 0
    fields = ["nombre", "alias", "fecha_nacimiento", "fecha_ingreso", "codigo"]
    readonly_fields = ["codigo"]


@admin.register(models.Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "jardin", "nivel_educativo", "educadora"]
    filter_horizontal = ["asistentes"]
    inlines = [MetaSemestreInline, NinoInline]


@admin.register(models.Semestre)
class SemestreAdmin(admin.ModelAdmin):
    list_display = ["nombre", "inicio", "fin"]


class NivelValidadoInline(admin.TabularInline):
    model = models.NivelValidado
    extra = 0
    fk_name = "nino"


@admin.register(models.Nino)
class NinoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "curso", "codigo", "fecha_nacimiento", "fecha_ingreso"]
    list_filter = ["curso"]
    search_fields = ["nombre"]
    readonly_fields = ["codigo"]
    inlines = [NivelValidadoInline]


@admin.register(models.NivelValidado)
class NivelValidadoAdmin(admin.ModelAdmin):
    list_display = ["nino", "nucleo", "nivel", "fecha", "validado_por"]
    list_filter = ["nucleo", "nino__curso"]


class ObservacionInline(admin.TabularInline):
    model = models.Observacion
    extra = 0
    fields = ["nino", "nombre_detectado", "fecha", "cita", "apoyo", "efecto", "grupal", "estado"]


@admin.register(models.Captura)
class CapturaAdmin(admin.ModelAdmin):
    list_display = ["id", "tipo", "curso", "autora", "estado", "creada"]
    list_filter = ["tipo", "estado", "curso"]
    readonly_fields = ["error"]
    inlines = [ObservacionInline]


@admin.register(models.Observacion)
class ObservacionAdmin(admin.ModelAdmin):
    list_display = ["fecha", "nino", "nombre_detectado", "apoyo", "efecto", "grupal", "estado"]
    list_filter = ["estado", "grupal", "apoyo", "efecto", "nucleos"]
    search_fields = ["cita", "nombre_detectado"]
    filter_horizontal = ["nucleos", "oas"]


@admin.register(models.PropuestaNivel)
class PropuestaNivelAdmin(admin.ModelAdmin):
    list_display = ["nino", "nucleo", "nivel", "evidencia_suficiente", "estado", "intentos", "creada"]
    list_filter = ["estado", "nucleo", "rubrica_provisoria"]
    filter_horizontal = ["observaciones_citadas"]
    readonly_fields = [
        "nivel_referencia", "huella_entrada", "rubrica_provisoria", "version_prompt",
        "procesamiento_iniciado", "token_procesamiento", "intentos", "uso_modelo",
        "resuelta_por", "resuelta_en", "creada", "actualizada",
    ]


# --- Instrumentos estandarizados (Task 14) ---------------------------------------------


@admin.register(models.Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "ambito", "provisorio", "orden"]


@admin.register(models.ResultadoInstrumento)
class ResultadoInstrumentoAdmin(admin.ModelAdmin):
    """Solo lectura: los cambios se hacen en la app, que los deja en el historial."""

    list_display = ["nino", "instrumento", "fecha_aplicacion", "estado"]
    list_filter = ["estado", "instrumento"]
    exclude = ["archivo"]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.RegistroCambio)
class RegistroCambioAdmin(admin.ModelAdmin):
    """El historial no se edita ni se borra, tampoco desde el panel."""

    list_display = ["objeto_tipo", "objeto_id", "accion", "usuario_nombre", "creado"]
    list_filter = ["objeto_tipo", "accion"]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(models.AvisoProteccion)
class AvisoProteccionAdmin(admin.ModelAdmin):
    """Task 13. El listado no muestra el texto de la nota."""

    list_display = ["id", "estado", "senal", "creado", "resuelto_por", "resuelto_en"]
    list_filter = ["estado", "senal"]
    readonly_fields = ["captura", "creado"]


@admin.register(models.ProtocoloJardin)
class ProtocoloJardinAdmin(admin.ModelAdmin):
    list_display = ["jardin", "nombre_documento", "actualizado_por", "actualizado"]
