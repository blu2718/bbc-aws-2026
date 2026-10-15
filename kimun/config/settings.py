"""Configuración de Django.

Todo lo que cambia entre desarrollo y producción se lee de variables de entorno
(ver `.env.example`). En producción (Task 4) se define DJANGO_DEBUG=0 y una
DJANGO_SECRET_KEY generada en el servidor.
La clave también puede venir de Parameter Store (DJANGO_SECRET_KEY_PARAMETRO).
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
# Datos compartidos del repo (currículo y demo). Viven en la raíz, junto a
# scripts/extraer_curriculo.py, que es quien genera el currículo.
DATOS_DIR = Path(os.environ.get("KIMUN_DATOS_DIR", BASE_DIR.parent / "datos"))


def _env_bool(nombre, por_defecto):
    return os.environ.get(nombre, por_defecto).strip().lower() in {"1", "true", "si", "sí", "yes"}


def _env_lista(nombre, por_defecto=""):
    return [v.strip() for v in os.environ.get(nombre, por_defecto).split(",") if v.strip()]


def _secret_key_de_parameter_store(nombre):
    """Lee el SECRET_KEY de un parámetro SecureString. Nunca muestra el valor."""
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    try:
        respuesta = boto3.client("ssm", region_name=region).get_parameter(Name=nombre, WithDecryption=True)
    except (BotoCoreError, ClientError) as error:
        raise ImproperlyConfigured(
            f"No se pudo leer el SECRET_KEY del parámetro {nombre} de Parameter Store "
            f"({error.__class__.__name__})."
        ) from error
    return respuesta["Parameter"]["Value"]


DEBUG = _env_bool("DJANGO_DEBUG", "1")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
# En la EC2 la clave viene de Parameter Store (rol de la instancia). Si
# DJANGO_SECRET_KEY está definida, tiene precedencia (p. ej. check --deploy local).
if not SECRET_KEY and os.environ.get("DJANGO_SECRET_KEY_PARAMETRO"):
    SECRET_KEY = _secret_key_de_parameter_store(os.environ["DJANGO_SECRET_KEY_PARAMETRO"])
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Define DJANGO_SECRET_KEY cuando DJANGO_DEBUG=0.")
    # Solo para desarrollo local. Nunca se usa con DEBUG apagado.
    SECRET_KEY = "dev-inseguro-no-usar-en-produccion"

ALLOWED_HOSTS = _env_lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")
CSRF_TRUSTED_ORIGINS = _env_lista("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "registro",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "registro.contexto.revision",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Fotos y audios subidos (Tasks 8 y 9). Solo se guardan mientras esperan a que el
# proceso de fondo los lea; apenas se leen, se borran y queda solo el texto
# (`registro/lectura.py`). Nunca se publican ni se muestran en la app.
# Con KIMUN_BUCKET definido van al bucket S3 privado (lo define
# infra/remoto/instalar.sh en la EC2); si no, a disco en MEDIA_ROOT.
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
KIMUN_BUCKET = os.environ.get("KIMUN_BUCKET", "").strip()
# La subida queda en memoria hasta este tamaño (sobre el máximo de foto, 3,75 MB, y de
# audio, 15 MB), así Django no escribe copias temporales del archivo en el disco del servidor.
FILE_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024

if KIMUN_BUCKET:
    # Credenciales: las del rol de la instancia (cadena por defecto de boto3).
    _ALMACEN_ARCHIVOS = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": KIMUN_BUCKET,
            "region_name": os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1",
            "signature_version": "s3v4",
            "addressing_style": "virtual",
            "file_overwrite": False,
            "default_acl": None,
        },
    }
else:
    _ALMACEN_ARCHIVOS = {"BACKEND": "django.core.files.storage.FileSystemStorage"}

STORAGES = {
    "default": _ALMACEN_ARCHIVOS,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "login"

# Producción (Task 4): EC2 detrás de CloudFront. Con DJANGO_DEBUG=1 (local y
# tests) no se aplica nada de esto y todo queda como arriba.
if not DEBUG:
    # CloudFront termina HTTPS y llega al origen por HTTP:8000; indica el
    # esquema original en este header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_CLOUDFRONT_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Apagado por defecto: CloudFront ya redirige HTTP a HTTPS y solo CloudFront
    # llega al puerto 8000. Encenderlo solo agrega riesgo de bucle si faltara el header.
    SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", "0")
    # HSTS corto (lo fija el entorno): el dominio *.cloudfront.net es provisorio.
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))

    # Destino de collectstatic fuera del código (lo fija el entorno).
    STATIC_ROOT = Path(os.environ.get("DJANGO_STATIC_ROOT", STATIC_ROOT))

    # WhiteNoise sirve los estáticos desde Gunicorn, justo después de SecurityMiddleware.
    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )
    # Los archivos subidos siguen en el almacenamiento de arriba (S3 si hay KIMUN_BUCKET).
    STORAGES = {
        "default": _ALMACEN_ARCHIVOS,
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

    # SQLite fuera del código, en WAL (web y worker escriben a la vez) y con
    # timeout para esperar el lock en vez de fallar con "database is locked".
    DATABASES["default"]["NAME"] = os.environ.get("DJANGO_DB_PATH", "/var/lib/kimun/db.sqlite3")
    DATABASES["default"]["OPTIONS"] = {
        "timeout": 20,
        "transaction_mode": "IMMEDIATE",
        "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
    }
