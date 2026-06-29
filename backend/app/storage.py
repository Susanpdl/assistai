"""Object storage seam.

The ingestion pipeline only ever talks to the `Storage` interface, so the actual backing
store is swappable. Today that's the local filesystem (`LocalStorage`); a future S3/GCS
backend implements the same three methods and nothing upstream changes.

A "key" is the storage path, e.g. ``"<course_id>/<document_id>.pdf"`` — the analogue of an
S3 object key.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.config import settings


class Storage(Protocol):
    def put(self, key: str, data: bytes) -> str:
        """Store bytes under `key`; return the key."""
        ...

    def get(self, key: str) -> bytes:
        """Read the bytes stored under `key`."""
        ...

    def delete(self, key: str) -> None:
        """Remove `key`. Missing keys are ignored (idempotent)."""
        ...


class LocalStorage:
    """Stores files under a base directory on local disk."""

    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Resolve and confirm the key stays inside the base dir (no path traversal).
        path = (self._base / key).resolve()
        if not str(path).startswith(str(self._base)):
            raise ValueError("Invalid storage key")
        return path

    def put(self, key: str, data: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


def get_storage() -> Storage:
    """Return the configured storage backend (FastAPI dependency / direct call)."""
    if settings.storage_backend == "local":
        return LocalStorage(settings.storage_dir)
    raise ValueError(f"Unknown storage backend: {settings.storage_backend}")
