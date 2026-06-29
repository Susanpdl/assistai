"""The ingestion pipeline: extract → chunk → embed → store, with status transitions.

`process_document` is a plain function (no web request, no queue) so it can be called
directly from the worker *or* from a test. It is idempotent: re-running it replaces the
document's chunks, which is exactly what re-indexing a replaced/failed file needs.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.ingestion.chunking import chunk_segments
from app.ingestion.embeddings import Embedder, get_embedder
from app.ingestion.extract import ExtractionError, extract_segments
from app.models.content import Chunk, Document
from app.models.enums import DocumentStatus
from app.storage import Storage, get_storage

logger = logging.getLogger(__name__)


def process_document(
    db: Session,
    document_id: uuid.UUID,
    *,
    storage: Storage | None = None,
    embedder: Embedder | None = None,
) -> Document | None:
    """Run the full pipeline for one document. Returns the updated Document (or None if gone)."""
    storage = storage or get_storage()
    embedder = embedder or get_embedder()

    doc = db.get(Document, document_id)
    if doc is None:
        logger.warning("process_document: %s no longer exists", document_id)
        return None

    try:
        if not doc.storage_key:
            raise ExtractionError("Document has no stored file")
        data = storage.get(doc.storage_key)

        segments = extract_segments(doc.filename, data, doc.type)
        chunks = chunk_segments(segments)
        vectors = embedder.embed([c.text for c in chunks])

        # Replace any existing chunks (idempotent re-index).
        db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
        db.add_all(
            Chunk(
                document_id=doc.id,
                course_id=doc.course_id,
                chunk_index=c.index,
                text=c.text,
                embedding=vec,
                location=c.location,
            )
            for c, vec in zip(chunks, vectors, strict=True)
        )
        doc.status = DocumentStatus.indexed
        doc.error = None
        db.commit()
        db.refresh(doc)
        logger.info("Indexed document %s (%d chunks)", doc.id, len(chunks))
        return doc

    except Exception as exc:  # noqa: BLE001 — any failure marks the doc failed, never crashes the worker
        db.rollback()
        doc = db.get(Document, document_id)
        if doc is not None:
            doc.status = DocumentStatus.failed
            doc.error = str(exc)[:500]
            db.commit()
            db.refresh(doc)
        logger.exception("Failed to ingest document %s", document_id)
        return doc
