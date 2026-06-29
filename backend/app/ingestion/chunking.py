"""Step 2 of the pipeline: split labelled segments into overlapping chunks.

We split because a good answer needs one relevant passage, not a whole document; the
overlap keeps a sentence's meaning from being cut exactly in half at a boundary. Sizes are
approximated in characters (~4 chars/token) to avoid pulling in a tokenizer dependency —
see `settings.chunk_chars` / `chunk_overlap_chars`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.ingestion.extract import Segment


@dataclass
class TextChunk:
    index: int
    text: str
    location: str


def chunk_segments(
    segments: list[Segment],
    *,
    size: int | None = None,
    overlap: int | None = None,
) -> list[TextChunk]:
    """Chunk each segment independently so a chunk's `location` stays accurate.

    Chunking within a segment (not across) means a chunk never straddles two pages, so its
    citation points at exactly one place.
    """
    size = size or settings.chunk_chars
    overlap = overlap or settings.chunk_overlap_chars
    if overlap >= size:
        raise ValueError("overlap must be smaller than chunk size")

    chunks: list[TextChunk] = []
    step = size - overlap
    for seg in segments:
        text = seg.text
        if len(text) <= size:
            chunks.append(TextChunk(len(chunks), text, seg.location))
            continue
        start = 0
        while start < len(text):
            piece = text[start : start + size]
            chunks.append(TextChunk(len(chunks), piece.strip(), seg.location))
            start += step
    return [c for c in chunks if c.text]
