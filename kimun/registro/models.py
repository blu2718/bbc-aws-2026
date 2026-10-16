"""Modelo de datos del MVP (ver PLAN.md, sección "Entidades").

Se definen todas las entidades del plan desde el inicio para que las tareas
2 a 9 trabajen en paralelo sin chocar en las migraciones.

La cantidad de niveles no es una constante: sale de `Rubrica` según el nivel
educativo (hoy 8, Integra podría pasar a 9). La base de datos solo exige
nivel >= 1; el máximo se valida en el código para poder cambiarlo sin
migración. La cantidad de núcleos sale de los datos (Integra tendrá 10).
"""
import re
import secrets
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from .rubrica import NIVELES_PROVISORIOS

NIVEL_MIN = 1
# Un nivel educativo dura 2 años (4 semestres); el máximo deja margen para quien repitió o tuvo pausas.
SEMESTRES_PREVIOS_MAX = 8


def texto_nivel(nivel, nombre=""):
    """Cómo se muestra un nivel en la app: "3 · Desarrollando", o "3" si no tiene nombre."""
    return f"{nivel} · {nombre}" if nombre else str(nivel)


def _nivel_desde_1(campo="nivel"):
    return Q(**{f"{campo}__gte": NIVEL_MIN})


class NivelEducativo(models.TextChoices):
    SALA_CUNA = "sala_cuna", "Sala cuna"
    MEDIO = "medio", "Nivel medio"
    TRANSICION = "transicion", "Transición"


# --- Currículo y rúbrica -------------------------------------------------------


class Rubrica(models.Model):
    """Parámetros de la rúbrica de un nivel educativo. Única fuente del nivel máximo."""

    nivel_educativo = models.CharField(max_length=12, choices=NivelEducativo.choices, unique=True)
    cantidad_niveles = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2), MaxValueValidator(20)],
        help_text="Hoy 8. Integra podría pasar a 9.",
    )
    provisoria = models.BooleanField(default=True)

    class Meta:
        ordering = ["nivel_educativo"]
        verbose_name = "rúbrica"
        verbose_name_plural = "rúbricas"
        constraints = [
            models.CheckConstraint(condition=Q(cantidad_niveles__gte=2), name="rubrica_al_menos_2_niveles"),
        ]

    def __str__(self):
        return f"{self.get_nivel_educativo_display()}: {self.cantidad_niveles} niveles"

    @classmethod
    def nivel_maximo(cls, nivel_educativo):
        rubrica = cls.objects.filter(nivel_educativo=nivel_educativo).first()
        if rubrica is None:
            raise ValidationError(f"No hay rúbrica para el nivel educativo «{nivel_educativo}».")
        return rubrica.cantidad_niveles


def validar_nivel(nivel, nivel_educativo, campo="nivel"):
    """Lanza ValidationError si el nivel no está entre 1 y el máximo de la rúbrica."""
    if nivel is None:
        return
    maximo = Rubrica.nivel_maximo(nivel_educativo)
    if not NIVEL_MIN <= nivel <= maximo:
        raise ValidationError({campo: f"El nivel debe estar entre {NIVEL_MIN} y {maximo}."})


class ValidaNivelMixin:
    """Valida el nivel contra la rúbrica en clean() y también en save().

    save() lo repite para que el código que no pasa por formularios tampoco
    guarde niveles fuera de rango. bulk_create no lo aplica.
    """

    campo_nivel = "nivel"

    def nivel_educativo_para_validar(self):
        raise NotImplementedError

    def _validar_nivel(self):
        try:
            nivel_educativo = self.nivel_educativo_para_validar()
        except ObjectDoesNotExist:
            # Falta el curso o el niño: Django reportará ese error por su cuenta.
            return
        validar_nivel(getattr(self, self.campo_nivel), nivel_educativo, self.campo_nivel)

    def clean(self):
        super().clean()
        self._validar_nivel()

    def save(self, *args, **kwargs):
        self._validar_nivel()
        super().save(*args, **kwargs)


class Nucleo(models.Model):
    sigla = models.CharField(max_length=4, unique=True)
    nombre = models.CharField(max_length=80, unique=True)
    orden = models.PositiveSmallIntegerField(default=0)
    # Trayectoria educativa del Programa Pedagógico de Transición.
    esperado_inicio_nt1 = models.TextField(blank=True, help_text="Lo esperado al iniciar NT1.")
    continuidad_basica = models.TextField(blank=True, help_text="Cómo continúan estos aprendizajes en Enseñanza Básica.")

    class Meta:
        ordering = ["orden", "sigla"]
        verbose_name = "núcleo"
        verbose_name_plural = "núcleos"

    def __str__(self):
        return f"{self.nombre} ({self.sigla})"


class DescriptorNivel(ValidaNivelMixin, models.Model):
    """Una celda de la rúbrica: qué significa el nivel N de un núcleo."""

    nivel_educativo = models.CharField(max_length=12, choices=NivelEducativo.choices)
    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="descriptores")
    nivel = models.PositiveSmallIntegerField()
    nombre = models.CharField(
        max_length=40, blank=True, help_text='Por ejemplo "Desarrollando". En la rúbrica provisoria, "Nivel N".'
    )
    descripcion = models.TextField()
    conducta = models.TextField(blank=True, help_text="Conducta observable típica del nivel.")
    ejemplos = models.JSONField(
        default=list, blank=True, help_text="Situaciones de ejemplo, escritas como registros anecdóticos."
    )
    pasos_sugeridos = models.TextField(
        blank=True, help_text='Qué observar o proponer después: las "orientaciones" de la rúbrica de Integra.'
    )
    provisorio = models.BooleanField(default=True)

    class Meta:
        ordering = ["nivel_educativo", "nucleo", "nivel"]
        verbose_name = "descriptor de nivel"
        verbose_name_plural = "descriptores de nivel"
        constraints = [
            models.UniqueConstraint(
                fields=["nivel_educativo", "nucleo", "nivel"], name="descriptor_unico"
            ),
            models.CheckConstraint(condition=_nivel_desde_1(), name="descriptor_nivel_desde_1"),
        ]

    def __str__(self):
        return f"{self.nucleo.sigla} nivel {self.nivel} ({self.get_nivel_educativo_display()})"

    def nivel_educativo_para_validar(self):
        return self.nivel_educativo

    @classmethod
    def nombres_por_nucleo(cls, nivel_educativo):
        """{sigla del núcleo: {nivel: nombre}}, solo de los descriptores oficiales.

        Los provisorios se omiten porque su nombre ("Nivel N") repetiría el
        número: con `texto_nivel` se muestran como "3" y no como "3 · Nivel 3".
        """
        nombres = {}
        filas = (
            cls.objects.filter(nivel_educativo=nivel_educativo, provisorio=False)
            .exclude(nombre="")
            .values_list("nucleo__sigla", "nivel", "nombre")
        )
        for sigla, nivel, nombre in filas:
            nombres.setdefault(sigla, {})[nivel] = nombre
        return nombres


class ObjetivoAprendizaje(models.Model):
    nivel_educativo = models.CharField(max_length=12, choices=NivelEducativo.choices)
    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="oas")
    numero = models.PositiveSmallIntegerField()
    texto = models.TextField()

    class Meta:
        ordering = ["nivel_educativo", "nucleo", "numero"]
        verbose_name = "objetivo de aprendizaje"
        verbose_name_plural = "objetivos de aprendizaje"
        constraints = [
            models.UniqueConstraint(
                fields=["nivel_educativo", "nucleo", "numero"], name="oa_unico"
            ),
        ]

    @property
    def codigo(self):
        """Cómo se cita en la app: "OA 4 LV"."""
        return f"OA {self.numero} {self.nucleo.sigla}"

    def __str__(self):
        return self.codigo


class Manifestacion(models.Model):
    """Conducta observable de un OA para NT1 o NT2."""

    class Anio(models.TextChoices):
        NT1 = "NT1", "NT1"
        NT2 = "NT2", "NT2"

    oa = models.ForeignKey(ObjetivoAprendizaje, on_delete=models.CASCADE, related_name="manifestaciones")
    anio = models.CharField(max_length=3, choices=Anio.choices)
    orden = models.PositiveSmallIntegerField(default=0)
    texto = models.TextField()

    class Meta:
        ordering = ["oa", "anio", "orden"]
        verbose_name = "manifestación"
        verbose_name_plural = "manifestaciones"
        constraints = [
            models.UniqueConstraint(fields=["oa", "anio", "orden"], name="manifestacion_unica"),
        ]

    def __str__(self):
        return f"{self.oa.codigo} {self.anio} #{self.orden}"


# --- Organización -------------------------------------------------------------


class Jardin(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    directora = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="jardines_dirigidos", help_text="Ve los cursos del jardín; no valida niveles.",
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "jardín"
        verbose_name_plural = "jardines"

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    jardin = models.ForeignKey(Jardin, on_delete=models.CASCADE, related_name="cursos")
    nombre = models.CharField(max_length=80)
    nivel_educativo = models.CharField(max_length=12, choices=NivelEducativo.choices)
    educadora = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cursos",
        help_text="Revisa observaciones y valida niveles.",
    )
    asistentes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="cursos_asistidos",
        help_text="Asistentes de párvulo: registran observaciones, no las revisan ni validan niveles.",
    )

    class Meta:
        ordering = ["jardin", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["jardin", "nombre"], name="curso_unico_por_jardin"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.jardin})"

    def save(self, *args, **kwargs):
        # Todas las vistas del curso necesitan el nivel máximo de su rúbrica (Rubrica.nivel_maximo).
        # Un curso creado en el panel antes de cargar el currículo de su nivel parte con la provisoria.
        Rubrica.objects.get_or_create(
            nivel_educativo=self.nivel_educativo,
            defaults={"cantidad_niveles": NIVELES_PROVISORIOS, "provisoria": True},
        )
        super().save(*args, **kwargs)


class Semestre(models.Model):
    nombre = models.CharField(max_length=20, unique=True, help_text='Por ejemplo "2026-1".')
    inicio = models.DateField()
    fin = models.DateField()

    class Meta:
        ordering = ["inicio"]
        constraints = [
            models.CheckConstraint(condition=Q(fin__gt=models.F("inicio")), name="semestre_fin_despues_inicio"),
        ]

    def __str__(self):
        return self.nombre


class MetaSemestre(ValidaNivelMixin, models.Model):
    """Nivel esperado según el semestre de permanencia del niño en el curso."""

    campo_nivel = "nivel_esperado"

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="metas")
    semestre_permanencia = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    nivel_esperado = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["curso", "semestre_permanencia"]
        verbose_name = "meta por semestre"
        verbose_name_plural = "metas por semestre"
        constraints = [
            models.UniqueConstraint(fields=["curso", "semestre_permanencia"], name="meta_unica"),
            models.CheckConstraint(condition=Q(semestre_permanencia__gte=1), name="meta_semestre_desde_1"),
            models.CheckConstraint(condition=_nivel_desde_1("nivel_esperado"), name="meta_nivel_desde_1"),
        ]

    def __str__(self):
        return f"{self.curso}: semestre {self.semestre_permanencia} → {self.nivel_esperado}"

    def nivel_educativo_para_validar(self):
        return self.curso.nivel_educativo


def _nuevo_codigo_nino():
    return f"N-{secrets.token_hex(3).upper()}"


class Nino(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="ninos")
    nombre = models.CharField(max_length=120)
    alias = models.JSONField(
        default=list, blank=True, help_text='Variantes de escritura y apodos, por ejemplo ["Nayara"].'
    )
    codigo = models.CharField(
        max_length=12, unique=True, default=_nuevo_codigo_nino, editable=False,
        help_text="Seudónimo que se envía a Bedrock en lugar del nombre.",
    )
    fecha_ingreso = models.DateField()
    fecha_nacimiento = models.DateField(
        null=True, blank=True, help_text="Para mostrar la edad en el perfil. No se envía a Bedrock."
    )
    semestres_previos = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(SEMESTRES_PREVIOS_MAX)],
        help_text=(
            "Semestres de este mismo nivel educativo que cursó en otro jardín o sala cuna antes de llegar. "
            "Se suman a su semestre de permanencia para calcular el nivel esperado."
        ),
    )
    procedencia = models.CharField(
        max_length=160, blank=True, help_text="De dónde viene, por ejemplo «Jardín Las Araucarias, Temuco»."
    )

    class Meta:
        ordering = ["curso", "nombre"]
        verbose_name = "niño o niña"
        verbose_name_plural = "niños y niñas"
        constraints = [
            models.UniqueConstraint(fields=["curso", "nombre"], name="nino_unico_por_curso"),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        nuevo = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            if nuevo:
                # Todo niño entra en nivel 1 en todos los núcleos (PLAN.md).
                NivelValidado.objects.bulk_create(
                    NivelValidado(
                        nino=self, nucleo=nucleo, nivel=NIVEL_MIN,
                        fecha=self.fecha_ingreso, comentario="Nivel inicial al ingresar.",
                    )
                    for nucleo in Nucleo.objects.all()
                )

    def nivel_actual(self, nucleo):
        """Último NivelValidado del núcleo, o None si no hay."""
        return self.niveles.filter(nucleo=nucleo).order_by("-fecha", "-creado", "-id").first()

    def niveles_actuales(self):
        """{sigla del núcleo: NivelValidado más reciente}."""
        actuales = {}
        for nv in self.niveles.select_related("nucleo").order_by("nucleo", "-fecha", "-creado", "-id"):
            actuales.setdefault(nv.nucleo.sigla, nv)
        return actuales


# --- Captura y observaciones ---------------------------------------------------

_EXTENSION_SEGURA = re.compile(r"\.[a-z0-9]{1,5}")


def ruta_original(instancia, nombre):
    """originales/AAAA/MM/<aleatorio>.<ext>: el nombre del archivo subido no se conserva.

    El nombre original puede traer el nombre de un niño ("sofia-postit.jpg") y
    quedaría a la vista en la clave de S3. Solo se conserva la extensión, si es simple.
    """
    extension = Path(nombre or "").suffix.lower()
    if not _EXTENSION_SEGURA.fullmatch(extension):
        extension = ""
    return f"originales/{timezone.localtime():%Y/%m}/{uuid.uuid4().hex}{extension}"


class Captura(models.Model):
    class Tipo(models.TextChoices):
        TEXTO = "texto", "Texto"
        FOTO = "foto", "Foto"
        AUDIO = "audio", "Audio"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PROCESANDO = "procesando", "Procesando"
        PROCESADA = "procesada", "Procesada"
        ERROR = "error", "Error"
        # Posible vulneración de derechos (Task 13): no genera observaciones y queda fuera de la evaluación.
        EN_RESGUARDO = "en_resguardo", "En resguardo"

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="capturas")
    autora = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="capturas",
        help_text="Educadora o asistente que registró.",
    )
    tipo = models.CharField(max_length=5, choices=Tipo.choices)
    archivo = models.FileField(
        upload_to=ruta_original, blank=True, max_length=200,
        help_text="Foto mientras espera a ser leída. Se borra apenas se lee; no se muestra en la app.",
    )
    texto_original = models.TextField(blank=True, help_text="Lo que se escribió (tipo texto).")
    texto_extraido = models.TextField(blank=True, help_text="Texto leído de la foto o transcrito del audio.")
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    error = models.TextField(blank=True)
    pregunta = models.TextField(
        blank=True, help_text="Si al ordenar faltó contexto clave, lo que Claude le pregunta a quien registró.",
    )
    intentos = models.PositiveSmallIntegerField(default=0)
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada"]
        indexes = [models.Index(fields=["estado", "creada"])]

    def __str__(self):
        return f"{self.get_tipo_display()} #{self.pk} ({self.get_estado_display()})"


@receiver(post_delete, sender=Captura)
def _borrar_archivo_de_captura(sender, instance, **kwargs):
    """Si se borra una captura que todavía tenía foto (por ejemplo, desde el admin o al
    borrar su curso), la foto se borra también: no queda guardada en ninguna parte."""
    if instance.archivo:
        instance.archivo.delete(save=False)


class Apoyo(models.TextChoices):
    """Escala del Programa Pedagógico de Transición."""

    AUTONOMO = "autonomo", "Autónomo"
    CON_AYUDA = "con_ayuda", "Con ayuda"
    PARCIAL = "parcial", "Parcial con ayuda"
    NO_LO_REALIZA = "no_lo_realiza", "No lo realiza"
    SIN_DATO = "sin_dato", "Sin dato"


class Efecto(models.TextChoices):
    """Qué muestra el suceso sobre el aprendizaje del niño en sus OA.

    Describe lo observado, no al niño: por eso "por reforzar" y no "negativo",
    "sin juicios perentorios" (Bases Curriculares).
    """

    AVANCE = "avance", "Muestra avance"
    POR_REFORZAR = "por_reforzar", "Por reforzar"
    SIN_DATO = "sin_dato", "Sin dato"


class ObservacionManager(models.Manager):
    """Oculta las observaciones de capturas en resguardo (Task 13).

    Es el manager por defecto, así que lo usan `Observacion.objects` y las relaciones
    inversas (`nino.observaciones`, `captura.observaciones`): ninguna vista, alerta,
    cobertura ni propuesta de nivel puede usar como evidencia una nota que podría
    describir una vulneración de derechos. Para verlas todas, `Observacion.todas`.
    """

    def get_queryset(self):
        return super().get_queryset().exclude(captura__estado="en_resguardo")


class Observacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente de revisión"
        ACEPTADA = "aceptada", "Aceptada"
        DESCARTADA = "descartada", "Descartada"

    objects = ObservacionManager()
    todas = models.Manager()

    captura = models.ForeignKey(Captura, on_delete=models.CASCADE, related_name="observaciones")
    nino = models.ForeignKey(
        Nino, on_delete=models.CASCADE, null=True, blank=True, related_name="observaciones",
        help_text="Vacío si el nombre es ambiguo o desconocido, o si es una nota grupal.",
    )
    nombre_detectado = models.CharField(max_length=120, blank=True)
    fecha = models.DateField()
    cita = models.TextField(help_text="Lo que el niño hizo o dijo, tal como quedó registrado.")
    interpretacion = models.TextField(blank=True, help_text="Interpretación de quien registró, si la hay.")
    nucleos = models.ManyToManyField(Nucleo, blank=True, related_name="observaciones")
    oas = models.ManyToManyField(ObjetivoAprendizaje, blank=True, related_name="observaciones")
    apoyo = models.CharField(max_length=14, choices=Apoyo.choices, default=Apoyo.SIN_DATO)
    efecto = models.CharField(
        max_length=12, choices=Efecto.choices, default=Efecto.SIN_DATO,
        help_text="Si el suceso muestra un avance o algo por reforzar en sus OA. Lo propone Claude y lo corrige la educadora.",
    )
    grupal = models.BooleanField(default=False, help_text="Contexto del curso; no se usa para evaluar.")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-creada"]
        verbose_name = "observación"
        verbose_name_plural = "observaciones"
        indexes = [models.Index(fields=["nino", "estado", "fecha"])]
        constraints = [
            # Una observación individual no se puede aceptar sin niño asignado.
            models.CheckConstraint(
                condition=~Q(estado="aceptada") | Q(grupal=True) | Q(nino__isnull=False),
                name="observacion_aceptada_con_nino",
            ),
        ]

    def __str__(self):
        quien = self.nino or self.nombre_detectado or "grupo"
        return f"{quien} {self.fecha:%Y-%m-%d}: {self.cita[:40]}"


class AvisoProteccion(models.Model):
    """Aviso de que una captura podría describir una vulneración de derechos (PLAN.md, Task 13).

    Kimün no detecta ni califica: solo avisa. Lo ven la educadora del curso y la directora
    del jardín (`permisos.avisos_que_ve`). Mientras exista y no se descarte, la captura queda
    en resguardo, sin observaciones y fuera de toda evaluación.
    """

    class Senal(models.TextChoices):
        RELATO = "relato", "Relato del niño o niña"
        FISICO = "fisico", "Indicador físico"
        PSICOLOGICO = "psicologico", "Maltrato psicológico"
        NEGLIGENCIA = "negligencia", "Negligencia"
        SEXUAL = "sexual", "Contenido sexual"
        OTRA = "otra", "Otra"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PROTOCOLO = "protocolo", "Se informó a la directora / se activó el protocolo"
        NO_ES = "no_es", "No es una vulneración"

    captura = models.OneToOneField(Captura, on_delete=models.CASCADE, related_name="aviso_proteccion")
    senal = models.CharField(max_length=12, choices=Senal.choices, default=Senal.OTRA)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    motivo = models.TextField(blank=True, help_text='Obligatorio al marcar "No es una vulneración".')
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="avisos_resueltos",
    )
    resuelto_en = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "aviso de protección"
        verbose_name_plural = "avisos de protección"

    def __str__(self):
        return f"Aviso #{self.pk} ({self.get_estado_display()})"


class ProtocoloJardin(models.Model):
    """Protocolo de protección de derechos del jardín, que carga su directora (Task 13).

    Cada jardín debe tener el suyo en su reglamento interno (Circular 860 de la
    Superintendencia de Educación). Si existe, el aviso de protección muestra estos pasos;
    si no, los provisorios de `datos/protocolo_proteccion.json`.
    """

    jardin = models.OneToOneField(Jardin, on_delete=models.CASCADE, related_name="protocolo_proteccion")
    nombre_documento = models.CharField(
        max_length=200, blank=True, help_text='Por ejemplo "Protocolo de actuación ante vulneración de derechos, 2026".',
    )
    pasos = models.TextField(help_text="Un paso por línea, en el orden en que se siguen.")
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="protocolos_actualizados",
    )
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "protocolo del jardín"
        verbose_name_plural = "protocolos de los jardines"

    def __str__(self):
        return f"Protocolo de {self.jardin}"

    def lista_de_pasos(self):
        """Los pasos sin líneas vacías ni la numeración o viñeta con que se hayan pegado."""
        # Primero se quita la numeración y después se filtran las vacías: "1." solo no es un paso.
        # La numeración exige un espacio después, para no comerse el "1" de "1.5 horas".
        limpias = (re.sub(r"^\s*(\d+[.)](?=\s|$)|[-•*])\s*", "", linea).strip() for linea in self.pasos.splitlines())
        return [linea for linea in limpias if linea]


# --- Niveles -------------------------------------------------------------------


class PropuestaNivel(ValidaNivelMixin, models.Model):
    class Estado(models.TextChoices):
        SOLICITADA = "solicitada", "Solicitada"
        PROCESANDO = "procesando", "Procesando"
        LISTA = "lista", "Lista para revisar"
        ACEPTADA = "aceptada", "Aceptada"
        AJUSTADA = "ajustada", "Resuelta con otro nivel"
        RECHAZADA = "rechazada", "Rechazada"
        ERROR = "error", "Error"
        OBSOLETA = "obsoleta", "Obsoleta"

    nino = models.ForeignKey(Nino, on_delete=models.CASCADE, related_name="propuestas")
    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="propuestas")
    nivel = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Vacío si la evidencia no alcanza para proponer un nivel.",
    )
    evidencia_suficiente = models.BooleanField(default=False)
    justificacion = models.TextField(blank=True)
    conductas_observadas = models.JSONField(default=list, blank=True)
    observaciones_citadas = models.ManyToManyField(Observacion, blank=True, related_name="propuestas")
    modelo = models.CharField(max_length=120, blank=True, help_text="Modelo de Bedrock que la generó.")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.SOLICITADA)
    error = models.TextField(blank=True)
    nivel_referencia = models.ForeignKey(
        "NivelValidado", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="propuestas_de_referencia",
        help_text="Nivel validado al preparar la entrada de la propuesta.",
    )
    huella_entrada = models.CharField(
        max_length=64, blank=True, help_text="SHA-256 de evidencia, rúbrica y contexto; no guarda las citas.",
    )
    rubrica_provisoria = models.BooleanField(
        null=True, blank=True, help_text="Procedencia al generar; vacío si aún no se preparó la entrada.",
    )
    version_prompt = models.CharField(max_length=80, blank=True)
    procesamiento_iniciado = models.DateTimeField(null=True, blank=True)
    token_procesamiento = models.UUIDField(null=True, blank=True, editable=False)
    intentos = models.PositiveIntegerField(default=0)
    uso_modelo = models.JSONField(default=dict, blank=True, help_text="Métricas de uso devueltas por el cliente.")
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="propuestas_resueltas",
    )
    resuelta_en = models.DateTimeField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada"]
        verbose_name = "propuesta de nivel"
        verbose_name_plural = "propuestas de nivel"
        constraints = [
            models.CheckConstraint(
                condition=Q(nivel__isnull=True) | _nivel_desde_1(), name="propuesta_nivel_desde_1"
            ),
            models.UniqueConstraint(
                fields=["nino", "nucleo"], condition=Q(estado__in=["solicitada", "procesando"]),
                name="propuesta_solicitud_activa_unica",
            ),
            models.CheckConstraint(
                condition=(Q(evidencia_suficiente=False, nivel__isnull=True)
                           | Q(evidencia_suficiente=True, nivel__isnull=False)),
                name="propuesta_nivel_coherente",
            ),
            models.CheckConstraint(
                condition=~Q(estado__in=["aceptada", "ajustada"]) | Q(evidencia_suficiente=True, nivel__isnull=False),
                name="propuesta_resuelta_con_nivel",
            ),
            models.CheckConstraint(
                condition=(~Q(estado="procesando")
                           | Q(procesamiento_iniciado__isnull=False, intentos__gte=1)),
                name="propuesta_procesando_con_inicio",
            ),
            models.CheckConstraint(
                condition=(Q(resuelta_por__isnull=True, resuelta_en__isnull=True)
                           | Q(resuelta_por__isnull=False, resuelta_en__isnull=False)),
                name="propuesta_resolucion_completa",
            ),
        ]

    def __str__(self):
        return f"{self.nino} {self.nucleo.sigla}: {self.nivel or 'sin nivel'} ({self.get_estado_display()})"

    def nivel_educativo_para_validar(self):
        return self.nino.curso.nivel_educativo

    def _validar_contrato(self):
        if self.estado not in self.Estado.values:
            raise ValidationError({"estado": "Estado de propuesta desconocido."})
        if self.evidencia_suficiente != (self.nivel is not None):
            raise ValidationError({"nivel": "La evidencia suficiente requiere un nivel; si no alcanza, debe quedar vacío."})
        if self.estado == self.Estado.PROCESANDO and (
            self.procesamiento_iniciado is None or self.intentos < 1
        ):
            raise ValidationError("El procesamiento requiere fecha de inicio y al menos un intento.")
        if self.nivel_referencia_id is not None:
            referencia = self.nivel_referencia
            if (referencia.nino_id, referencia.nucleo_id) != (self.nino_id, self.nucleo_id):
                raise ValidationError({"nivel_referencia": "El nivel de referencia debe ser del mismo niño y núcleo."})
        if bool(self.resuelta_por_id) != (self.resuelta_en is not None):
            raise ValidationError("La resolución requiere usuaria y fecha juntas.")
        if self.estado in (self.Estado.ACEPTADA, self.Estado.AJUSTADA, self.Estado.RECHAZADA):
            if not self.resuelta_por_id or self.resuelta_en is None:
                raise ValidationError("La resolución requiere usuaria y fecha.")
        if self.estado in (self.Estado.ACEPTADA, self.Estado.AJUSTADA):
            if not self.evidencia_suficiente or self.nivel is None:
                raise ValidationError("No se puede aceptar una propuesta sin evidencia suficiente y nivel.")
            anterior = type(self).objects.filter(pk=self.pk).values_list("estado", flat=True).first()
            # Una resolución histórica no pierde validez al registrarse su NivelValidado.
            if anterior in (self.Estado.ACEPTADA, self.Estado.AJUSTADA) and anterior != self.estado:
                raise ValidationError("La propuesta ya fue resuelta.")
            if anterior not in (self.Estado.ACEPTADA, self.Estado.AJUSTADA):
                from .propuestas import entrada_vigente

                if anterior != self.Estado.LISTA or not entrada_vigente(self):
                    raise ValidationError("Solo se puede aceptar una propuesta lista con entrada vigente.")

    def clean(self):
        super().clean()
        self._validar_contrato()

    def save(self, *args, **kwargs):
        self._validar_contrato()
        super().save(*args, **kwargs)


class NivelValidado(ValidaNivelMixin, models.Model):
    """Historial de niveles fijados por la educadora. El actual es el más reciente."""

    nino = models.ForeignKey(Nino, on_delete=models.CASCADE, related_name="niveles")
    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="niveles_validados")
    nivel = models.PositiveSmallIntegerField()
    fecha = models.DateField()
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="niveles_validados", help_text="Vacío en el nivel inicial automático.",
    )
    comentario = models.TextField(blank=True)
    propuesta = models.ForeignKey(
        PropuestaNivel, on_delete=models.SET_NULL, null=True, blank=True, related_name="validaciones"
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nino", "nucleo", "-fecha", "-creado"]
        verbose_name = "nivel validado"
        verbose_name_plural = "niveles validados"
        indexes = [models.Index(fields=["nino", "nucleo", "fecha"])]
        constraints = [
            models.CheckConstraint(condition=_nivel_desde_1(), name="nivel_validado_desde_1"),
            models.UniqueConstraint(fields=["propuesta"], condition=Q(propuesta__isnull=False),
                                    name="nivel_validado_propuesta_unica"),
        ]

    def __str__(self):
        return f"{self.nino} {self.nucleo.sigla}: {self.nivel} ({self.fecha:%Y-%m-%d})"

    def nivel_educativo_para_validar(self):
        return self.nino.curso.nivel_educativo


# --- Instrumentos estandarizados (Task 14) -----------------------------------------
#
# El catálogo de instrumentos es un dato (datos/instrumentos.json), como la rúbrica:
# áreas, campos de puntaje, rangos y categorías no están fijos en el código.
# La lógica (validar, calcular, categorizar) está en `instrumentos.py`.


class Instrumento(models.Model):
    class Ambito(models.TextChoices):
        SALUD = "salud", "Salud (lo aplica el centro de salud)"
        EDUCATIVO = "educativo", "Educativo (lo aplica el jardín)"
        OTRO = "otro", "Otro"

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    ambito = models.CharField(max_length=10, choices=Ambito.choices)
    definicion = models.JSONField(help_text="Áreas, campos, rangos y categorías (ver datos/instrumentos.json).")
    provisorio = models.BooleanField(
        default=False, help_text="La estructura no está confirmada con el material oficial del instrumento.",
    )
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "codigo"]
        verbose_name = "instrumento estandarizado"
        verbose_name_plural = "instrumentos estandarizados"

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"


def ruta_hoja(instancia, nombre):
    """originales/hojas/AAAA/MM/<aleatorio>.<ext>, como `ruta_original`: no conserva el nombre subido.

    Bajo `originales/` porque es el único prefijo en que el rol de la instancia escribe y borra.
    """
    extension = Path(nombre or "").suffix.lower()
    if not _EXTENSION_SEGURA.fullmatch(extension):
        extension = ""
    return f"originales/hojas/{timezone.localtime():%Y/%m}/{uuid.uuid4().hex}{extension}"


class ResultadoInstrumento(models.Model):
    """El resultado de un instrumento aplicado a un niño, tal como lo trae la hoja.

    No es evidencia de aprendizaje: no entra en la propuesta de nivel, las alertas
    ni la tabla del curso. Solo se muestra en la ficha (educadora y directora).
    Cada cambio queda en `RegistroCambio`.
    """

    class Estado(models.TextChoices):
        POR_LEER = "por_leer", "Esperando lectura"
        LEYENDO = "leyendo", "Leyendo la hoja"
        POR_REVISAR = "por_revisar", "Por revisar"
        CONFIRMADO = "confirmado", "Confirmado"
        DESCARTADO = "descartado", "Descartado"
        ERROR = "error", "No se pudo leer"

    class Origen(models.TextChoices):
        JARDIN = "jardin", "Aplicado en el jardín"
        SALUD = "salud", "Del centro de salud (lo trajo la familia)"
        OTRO = "otro", "Otro"

    nino = models.ForeignKey(Nino, on_delete=models.CASCADE, related_name="resultados_instrumento")
    instrumento = models.ForeignKey(
        Instrumento, on_delete=models.PROTECT, null=True, blank=True, related_name="resultados",
        help_text="Vacío mientras Kimün detecta el instrumento en la hoja.",
    )
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.POR_REVISAR)
    origen = models.CharField(max_length=8, choices=Origen.choices, default=Origen.SALUD)
    fecha_aplicacion = models.DateField(null=True, blank=True)
    aplicado_por = models.CharField(
        max_length=120, blank=True, help_text="Quién aplicó el instrumento (cargo o centro), como figura en la hoja.",
    )
    valores = models.JSONField(
        default=dict, blank=True,
        help_text='{"campos": {...}, "areas": {"C": {...}}, "categoria": "...", "categorias_area": {...}}',
    )
    observaciones = models.TextField(blank=True)
    avisos = models.JSONField(default=list, blank=True, help_text="Lo que Kimün no pudo leer o no calza.")
    archivo = models.FileField(
        upload_to=ruta_hoja, blank=True, max_length=200,
        help_text="Foto o PDF de la hoja mientras espera ser leída. Se borra apenas se lee.",
    )
    error = models.TextField(blank=True)
    intentos = models.PositiveSmallIntegerField(default=0)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="resultados_registrados",
    )
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="resultados_confirmados",
    )
    confirmado_en = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_aplicacion", "-creado"]
        verbose_name = "resultado de instrumento"
        verbose_name_plural = "resultados de instrumentos"
        indexes = [models.Index(fields=["estado", "creado"]), models.Index(fields=["nino", "estado"])]
        constraints = [
            models.CheckConstraint(
                condition=~Q(estado="confirmado") | Q(
                    instrumento__isnull=False, fecha_aplicacion__isnull=False,
                    confirmado_por__isnull=False, confirmado_en__isnull=False,
                ),
                name="resultado_confirmado_completo",
            ),
        ]

    def __str__(self):
        cual = self.instrumento.codigo if self.instrumento_id else "instrumento por detectar"
        return f"{self.nino} · {cual} ({self.get_estado_display()})"


@receiver(post_delete, sender=ResultadoInstrumento)
def _borrar_hoja(sender, instance, **kwargs):
    if instance.archivo:
        instance.archivo.delete(save=False)


# --- Historial de cambios a prueba de adulteración (Task 14) -----------------------


class RegistroCambioQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("El historial de cambios no se puede modificar.")

    def delete(self):
        raise ValidationError("El historial de cambios no se puede borrar.")


class RegistroCambio(models.Model):
    """Una entrada del historial de un dato editable (resultado de instrumento u observación).

    Es de solo agregar: la app no permite modificar ni borrar entradas, y la base de datos
    rechaza cualquier UPDATE (trigger de la migración 0012). Cada entrada guarda el estado
    completo antes y después del cambio y un SHA-256 encadenado con la entrada anterior del
    mismo objeto, así que borrar o alterar una entrada, o cambiar el dato por fuera de la app,
    se detecta al verificar (`historial.verificar`). No usa claves foráneas para sobrevivir
    al dato que describe.
    """

    class Objeto(models.TextChoices):
        RESULTADO = "resultado", "Resultado de instrumento"
        OBSERVACION = "observacion", "Observación"
        TRAYECTORIA = "trayectoria", "Trayectoria previa del niño"

    class Accion(models.TextChoices):
        CREAR = "crear", "Creado"
        LECTURA_IA = "lectura_ia", "Leído por Kimün"
        EDITAR = "editar", "Editado"
        CONFIRMAR = "confirmar", "Confirmado"
        DESCARTAR = "descartar", "Descartado"
        REABRIR = "reabrir", "Vuelto a revisar"

    objeto_tipo = models.CharField(max_length=12, choices=Objeto.choices)
    objeto_id = models.PositiveIntegerField()
    curso_id = models.PositiveIntegerField(help_text="Para filtrar por permisos sin clave foránea.")
    accion = models.CharField(max_length=12, choices=Accion.choices)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="cambios_registrados", help_text="Vacío si lo hizo Kimün (lectura de la hoja).",
    )
    usuario_nombre = models.CharField(max_length=150, blank=True)
    motivo = models.TextField(blank=True)
    antes = models.JSONField(null=True, blank=True)
    despues = models.JSONField()
    creado = models.DateTimeField()
    hash_anterior = models.CharField(max_length=64, blank=True)
    hash = models.CharField(max_length=64, unique=True)

    objects = RegistroCambioQuerySet.as_manager()

    class Meta:
        ordering = ["objeto_tipo", "objeto_id", "creado", "id"]
        verbose_name = "registro de cambio"
        verbose_name_plural = "historial de cambios"
        indexes = [models.Index(fields=["objeto_tipo", "objeto_id", "creado"])]
        constraints = [
            # Dos escrituras simultáneas no pueden colgar de la misma entrada: la cadena no se bifurca.
            models.UniqueConstraint(
                fields=["objeto_tipo", "objeto_id", "hash_anterior"], name="registro_cambio_cadena_lineal",
            ),
        ]

    def __str__(self):
        return f"{self.get_objeto_tipo_display()} #{self.objeto_id}: {self.get_accion_display()} ({self.creado:%Y-%m-%d %H:%M})"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("El historial de cambios no se puede modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("El historial de cambios no se puede borrar.")
