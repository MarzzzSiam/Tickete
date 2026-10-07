from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="local-only-tickete-never-use-this-in-production")
DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "apps.accounts",
    "apps.core",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {
    "default": env.db(
        "DATABASE_URL", default="postgresql://tickete:tickete_local@127.0.0.1:5432/tickete"
    )
}
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("TICKETÉ requires PostgreSQL; SQLite is not supported.")
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=0)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
DATABASES["default"].setdefault("OPTIONS", {}).update(
    {
        "connect_timeout": 3,
        "prepare_threshold": None,
    }
)
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DISPLAY_TIME_ZONE = "Asia/Dhaka"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"
FRONTEND_ORIGIN = env("FRONTEND_ORIGIN", default="http://127.0.0.1:3000")
CORS_ALLOWED_ORIGINS = [FRONTEND_ORIGIN]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [FRONTEND_ORIGIN]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],  # Cookie JWT endpoints arrive in Phase 1.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
SPECTACULAR_SETTINGS = {
    "TITLE": "TICKETÉ API",
    "DESCRIPTION": "Phase 0 foundation. Business endpoints are not implemented yet.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_SOFT_TIME_LIMIT = 90
CELERY_TASK_TIME_LIMIT = 120
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="TICKETÉ <hello@example.invalid>")
SUPPORT_EMAIL = env("SUPPORT_EMAIL", default="support@example.invalid")
STORAGE_BACKEND = env("STORAGE_BACKEND", default="local")
SUPABASE_URL = env("SUPABASE_URL", default="")
SUPABASE_SERVICE_KEY = env("SUPABASE_SERVICE_KEY", default="")
SUPABASE_PRIVATE_BUCKET = env("SUPABASE_PRIVATE_BUCKET", default="tickets")
PAYMENT_GATEWAY = "dummy"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "apps.core.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
