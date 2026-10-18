"""Hosted worker settings; this process does not serve HTTP requests."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import DATABASES, EMAIL_PROVIDER, SECRET_KEY, env

for required in ("SECRET_KEY", "DATABASE_URL", "REDIS_URL"):
    if not env(required, default=""):
        raise ImproperlyConfigured(f"Hosted worker requires {required}.")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("local-only"):
    raise ImproperlyConfigured("Set a unique worker SECRET_KEY of at least 50 characters.")

DEBUG = False
DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
if EMAIL_PROVIDER != "brevo":
    EMAIL_BACKEND = "apps.core.email.UnconfiguredProductionEmailBackend"
