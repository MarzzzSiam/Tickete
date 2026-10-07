from pathlib import Path, PurePosixPath
from typing import Protocol
from urllib.parse import quote

import httpx
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def validate_key(key: str) -> str:
    path = PurePosixPath(key)
    if (
        not key
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in key
        or ":" in key
        or "\x00" in key
    ):
        raise ValueError("Invalid storage key.")
    return key


class Storage(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> str: ...
    def read(self, key: str) -> bytes: ...


class LocalStorage:
    """Private development storage. Callers must authorize before reading."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def _path(self, key):
        path = (self.root / validate_key(key)).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Storage path escapes root.")
        return path

    def put(self, key, content, content_type):
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    def read(self, key):
        return self._path(key).read_bytes()


class SupabaseStorage:
    """Server-only private bucket access; never exposes a service key to clients."""

    def __init__(self, url, service_key, bucket):
        if not url.startswith("https://") or not service_key or not bucket:
            raise ImproperlyConfigured("Set HTTPS Supabase URL, service key and private bucket.")
        self.base = url.rstrip("/") + "/storage/v1/object/" + quote(bucket, safe="")
        self.headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}

    def put(self, key, content, content_type):
        response = httpx.post(
            self.base + "/" + quote(validate_key(key), safe="/"),
            content=content,
            headers={**self.headers, "Content-Type": content_type, "x-upsert": "true"},
            timeout=20,
        )
        response.raise_for_status()
        return key

    def read(self, key):
        response = httpx.get(
            self.base + "/" + quote(validate_key(key), safe="/"), headers=self.headers, timeout=20
        )
        response.raise_for_status()
        return response.content


def get_storage() -> Storage:
    if settings.STORAGE_BACKEND == "local":
        return LocalStorage(settings.MEDIA_ROOT)
    if settings.STORAGE_BACKEND == "supabase":
        return SupabaseStorage(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY, settings.SUPABASE_PRIVATE_BUCKET
        )
    raise ImproperlyConfigured("Unknown STORAGE_BACKEND.")
