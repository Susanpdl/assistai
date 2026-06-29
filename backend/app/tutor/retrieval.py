"""Retrieval: find the course material most relevant to a question.

Embeds the question with the same embedder used at ingestion, then runs a vector
similarity search in pgvector — **always filtered by course_id** so one course's search can
never surface another course's material (NFR-5). Returns chunks with a similarity score and
a citation label (document filename + in-document location, e.g. "Week 5.pptx — slide 17").
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.embeddings import get_embedder
from app.models.content import Chunk, Document


@dataclass
class Retrieved:
    text: str
    location: str
    filename: str
    similarity: float  # cosine similarity in [-1, 1]; ~1 means very relevant

    @property
    def citation(self) -> str:
        return f"{self.filename} — {self.location}"


def retrieve(db: Session, course_id: uuid.UUID, question: str, k: int | None = None) -> list[Retrieved]:
    k = k or settings.tutor_top_k
    query_vec = get_embedder().embed_one(question)

    # cosine_distance = 1 - cosine_similarity; order ascending (closest first).
    distance = Chunk.embedding.cosine_distance(query_vec)
    rows = db.execute(
        select(Chunk, Document.filename, distance.label("distance"))
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.course_id == course_id)
        .order_by(distance)
        .limit(k)
    ).all()

    return [
        Retrieved(
            text=chunk.text,
            location=chunk.location,
            filename=filename,
            similarity=1.0 - float(dist),
        )
        for chunk, filename, dist in rows
    ]
