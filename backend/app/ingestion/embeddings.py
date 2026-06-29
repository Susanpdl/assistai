"""Embedding seam.

An `Embedder` turns text into a vector. The pipeline depends only on this interface, so
the real model is a Phase-4 decision (see content-ingestion.md "Open questions").

For dev and tests we use `LocalEmbedder`: a deterministic, offline, hashing-based embedder
that needs no API key or network. It maps words into a fixed-size vector (the "hashing
trick") and L2-normalises, so cosine similarity still tracks word overlap — enough to prove
the pipeline and retrieval scoping without a paid model.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from app.config import settings

_WORD = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, preserving order."""
        ...

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text (e.g. a search query)."""
        ...


class LocalEmbedder:
    """Deterministic bag-of-words hashing embedder. Same text → same vector, in any process."""

    def __init__(self, dim: int) -> None:
        self.dim = dim

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _WORD.findall(text.lower()):
            # Stable cross-process hash (Python's built-in hash() is salted per run).
            h = hashlib.md5(token.encode("utf-8")).digest()
            idx = int.from_bytes(h[:4], "big") % self.dim
            sign = 1.0 if h[4] & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            # Empty/symbol-only text: a fixed unit vector keeps the column non-null and valid.
            vec[0] = 1.0
            return vec
        return [v / norm for v in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._vector(text)


def get_embedder() -> Embedder:
    """Return the configured embedder."""
    if settings.embedding_backend == "local":
        return LocalEmbedder(settings.embedding_dim)
    raise ValueError(f"Unknown embedding backend: {settings.embedding_backend}")
