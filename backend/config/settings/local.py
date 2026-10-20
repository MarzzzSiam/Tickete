from .base import *  # noqa: F403
from .base import env

DEBUG = True
AUTH_COOKIE_SECURE = False
# Development runs account email tasks directly; no hosted Celery worker needed.
# This is intentionally absent from production and worker settings.
LOCAL_ACCOUNT_EMAIL_SYNC = env.bool("LOCAL_ACCOUNT_EMAIL_SYNC", default=False)
