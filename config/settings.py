"""
Configuración de Django para la tienda de artesanías de Urabá.

Todo lo que cambia entre entornos (o es secreto) se lee del archivo .env.
La lista completa de variables está en .env.example.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def variable_requerida(nombre: str) -> str:
    """Lee una variable de entorno obligatoria y falla temprano si no está."""
    valor = os.environ.get(nombre)
    if not valor:
        raise ImproperlyConfigured(
            f"Falta la variable de entorno {nombre}. Revisa tu .env "
            f"(hay una plantilla en .env.example)."
        )
    return valor


def variable_booleana(nombre: str, por_defecto: bool = False) -> bool:
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí"}


SECRET_KEY = variable_requerida("DJANGO_SECRET_KEY")

DEBUG = variable_booleana("DJANGO_DEBUG", por_defecto=False)

ALLOWED_HOSTS: list[str] = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# Necesario para que el POST del checkout y del admin pasen detrás de HTTPS.
CSRF_TRUSTED_ORIGINS: list[str] = [
    origen.strip()
    for origen in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origen.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalogo",
    "pedidos",
    "pagos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
                "pedidos.context_processors.resumen_del_carrito",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Base de datos (Neon).
#
# DATABASE_URL es la que usa la aplicación. En producción apunta al endpoint
# con pooler; en local y para migraciones conviene la URL directa (sin
# "-pooler"), porque PgBouncer en modo transacción no soporta bien las
# sentencias preparadas ni los cursores del lado del servidor.
# Con USAR_BASE_DIRECTA=1 se usa DIRECT_DATABASE_URL en vez de DATABASE_URL,
# para no tener que editar el .env cada vez que se corre una migración:
#   PowerShell:  $env:USAR_BASE_DIRECTA=1; python manage.py migrate
USAR_BASE_DIRECTA = variable_booleana("USAR_BASE_DIRECTA")

DATABASES = {
    "default": dj_database_url.parse(
        variable_requerida(
            "DIRECT_DATABASE_URL" if USAR_BASE_DIRECTA else "DATABASE_URL"
        ),
        conn_max_age=0 if USAR_BASE_DIRECTA else 600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

DISABLE_SERVER_SIDE_CURSORS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Dónde viven las fotos de producto.
#
# Con CLOUDINARY_URL definida, el ImageField sube a Cloudinary; sin ella, al
# disco local. El disco local alcanza para desarrollo, pero no para producción:
# en un host de sistema de archivos efímero las fotos se pierden en cada
# despliegue. Los modelos no cambian: solo cambia el backend de almacenamiento.
USAR_CLOUDINARY = bool(os.environ.get("CLOUDINARY_URL"))

STORAGES = {
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if USAR_CLOUDINARY
            else "django.core.files.storage.FileSystemStorage"
        )
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Stripe. Se trabaja siempre en modo test: las llaves empiezan por pk_test_
# y sk_test_. No se procesan pagos reales.
STRIPE_CLAVE_PUBLICA = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_CLAVE_SECRETA = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_SECRETO_WEBHOOK = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_MONEDA = os.environ.get("STRIPE_MONEDA", "cop")


# Clave con la que se guarda el carrito en la sesión.
CARRITO_SESSION_ID = "carrito"

LOGIN_REDIRECT_URL = "catalogo:lista_de_productos"
LOGOUT_REDIRECT_URL = "catalogo:lista_de_productos"


if not DEBUG:
    SECURE_SSL_REDIRECT = variable_booleana("DJANGO_SECURE_SSL_REDIRECT", por_defecto=True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
