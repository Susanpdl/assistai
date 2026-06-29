"""Document and Chunk — uploaded course material and its searchable, embedded pieces."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.models.base import Base, TimestampMixin, uuid_pk
from app.models.enums import DocumentStatus


class Document(Base, TimestampMixin):
    __tablename__ = "document"

    id: Mapped[uuid.UUID] = uuid_pk()
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status"),
        default=DocumentStatus.processing,
        nullable=False,
    )
    # Where the original file lives in object storage (the storage key/path).
    storage_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    # Why ingestion failed, when status == failed. Surfaced in the UI; null otherwise.
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Chunk(Base):
    __tablename__ = "chunk"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document.id"), nullable=False, index=True
    )
    # Denormalised from the parent document so retrieval can filter by course directly,
    # guaranteeing one course's search can never surface another course's material (NFR-5).
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course.id"), nullable=False, index=True
    )
    # Position within the document (0-based), so chunks have a stable order.
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # The vector used for similarity search in pgvector.
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim), nullable=False)
    # Human-readable source, e.g. "Week 4, p.12" — this becomes the answer's citation.
    location: Mapped[str] = mapped_column(String(200), nullable=False)
