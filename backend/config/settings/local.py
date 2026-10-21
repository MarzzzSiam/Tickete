import os
from pathlib import Path

from .base import *  # noqa: F403
from .base import env

# Optional portable Windows libraries, installed separately and never committed.
pdf_dlls = Path(__file__).resolve().parents[3] / ".tools" / "pdf-runtime" / "ucrt64" / "bin"
if os.name == "nt" and pdf_dlls.is_dir():
    os.environ.setdefault("WEASYPRINT_DLL_DIRECTORIES", str(pdf_dlls))

DEBUG = True
AUTH_COOKIE_SECURE = False
# Development runs account email tasks directly; no hosted Celery worker needed.
# This is intentionally absent from production and worker settings.
LOCAL_ACCOUNT_EMAIL_SYNC = env.bool("LOCAL_ACCOUNT_EMAIL_SYNC", default=False)
