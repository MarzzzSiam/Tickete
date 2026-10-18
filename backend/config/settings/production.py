from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import DATABASES, EMAIL_PROVIDER, SECRET_KEY, env

if not env("SECRET_KEY", default="") or len(SECRET_KEY) < 50 or SECRET_KEY.startswith("local-only"):
    raise ImproperlyConfigured("Set a unique production SECRET_KEY of at least 50 characters.")
for required in ("DATABASE_URL", "ALLOWED_HOSTS", "FRONTEND_ORIGIN"):
    if not env(required, default=""):
        raise ImproperlyConfigured(f"Production requires {required}.")
if not env("FRONTEND_ORIGIN").startswith("https://"):
    raise ImproperlyConfigured("Production FRONTEND_ORIGIN must use HTTPS.")
DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
# Set only when the trusted ingress strips client-supplied forwarding headers.
if env.bool("TRUST_PROXY_SSL_HEADER", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
# Never send sensitive links to hosted console logs.
if EMAIL_PROVIDER != "brevo":
    EMAIL_BACKEND = "apps.core.email.UnconfiguredProductionEmailBackend"
