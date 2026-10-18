"""Disposable browser-test services only; never load against hosted data."""

from django.core.exceptions import ImproperlyConfigured

from .local import *  # noqa: F403
from .local import DATABASES, REDIS_URL, REST_FRAMEWORK, env

if (
    env("AUTH_E2E_LIVE", default="") != "1"
    or DATABASES["default"]["HOST"] not in ("127.0.0.1", "localhost")
    or not REDIS_URL.startswith("redis://127.0.0.1:")
):
    raise ImproperlyConfigured(
        "Browser tests require explicitly enabled loopback PostgreSQL and Redis."
    )

# Browser workers share one loopback IP. Backend tests separately exercise the
# normal abuse limits; the UI integration suite needs an independent budget.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {"auth_ip": "1000/min", "auth_email": "1000/hour"},
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
