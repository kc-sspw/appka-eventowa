import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DEBUG", "0") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise ImproperlyConfigured(
        "Set SECRET_KEY (at least 32 characters); run scripts/init_local.py."
    )
EVENT_DOMAIN = os.environ.get("EVENT_DOMAIN", "events.localhost")
PLATFORM_HOST = os.environ.get("PLATFORM_HOST", "platform.localhost")
PUBLIC_SCHEME = os.environ.get("PUBLIC_SCHEME", "https")
PUBLIC_PORT = os.environ.get("PUBLIC_PORT", "")
ALLOWED_HOSTS = [PLATFORM_HOST, "." + EVENT_DOMAIN]
USE_X_FORWARDED_HOST = False
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "events",
    "accounts",
    "information",
    "game",
    "media_storage",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "events.middleware.HostMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "events.middleware.EventAccessMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
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
                "information.services.navigation",
            ]
        },
    }
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PGDATABASE", "event_poc"),
        "USER": os.environ.get("PGUSER", "event_poc"),
        "PASSWORD": os.environ.get("PGPASSWORD", ""),
        "HOST": os.environ.get("PGHOST", "127.0.0.1"),
        "PORT": os.environ.get("PGPORT", "5432"),
        "CONN_MAX_AGE": 0,
    }
}
if DEBUG and os.environ.get("LOCAL_SQLITE_SMOKE") == "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / ".private/smoke.sqlite3",
        }
    }
AUTH_USER_MODEL = "accounts.Account"
AUTHENTICATION_BACKENDS = ["accounts.backends.EventBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 16},
    }
]
LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 12
SECURE_SSL_REDIRECT = not DEBUG
# Enable only behind a trusted TLS proxy that replaces this header.
if os.environ.get("TRUST_PROXY_TLS") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
PRIVATE_ROOT = Path(os.environ.get("PRIVATE_ROOT", BASE_DIR / ".private"))
PRIVATE_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
FILE_UPLOAD_TEMP_DIR = str(PRIVATE_ROOT / "incoming")
Path(FILE_UPLOAD_TEMP_DIR).mkdir(mode=0o700, exist_ok=True)
FILE_UPLOAD_HANDLERS = [
    "media_storage.uploads.BoundedUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 1
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "drive")
if STORAGE_BACKEND not in {"fake", "drive"} or (STORAGE_BACKEND == "fake" and not DEBUG):
    raise ImproperlyConfigured("FakeStorage is allowed only with DEBUG=1.")
TOKEN_KEY = os.environ.get("TOKEN_KEY", "")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
STORAGE_MAX_BUDGET = 20 * 1024**3
UPLOAD_MAX_BYTES = 15 * 1024**2
PHOTO_MAX_BYTES = 1024**2
THUMBNAIL_CACHE_BYTES = 256 * 1024**2
THUMBNAIL_TTL = 3600
LOGIN_URL = "/auth/login"
# No request payload, URL query or provider exception logging (OAuth codes/passwords).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "loggers": {
        "django.request": {"handlers": ["null"], "propagate": False},
        "django.server": {"handlers": ["null"], "propagate": False},
        "httpx": {"handlers": ["null"], "propagate": False},
    },
}
