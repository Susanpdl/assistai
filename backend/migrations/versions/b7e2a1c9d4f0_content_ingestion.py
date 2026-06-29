"""content ingestion: failed status, chunk.course_id/chunk_index, document.storage_key/error

Revision ID: b7e2a1c9d4f0
Revises: c68ab4705fc6
Create Date: 2026-06-24 10:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e2a1c9d4f0"
down_revision: str | None = "c68ab4705fc6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # New document_status value for ingestion failures (PG12+ allows ADD VALUE in a txn).
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'failed'")

    # Document: where the original file lives, and why ingestion failed (if it did).
    op.add_column("document", sa.Column("storage_key", sa.String(length=700), nullable=True))
    op.add_column("document", sa.Column("error", sa.String(length=500), nullable=True))

    # Chunk: course scoping (NFR-5) + stable ordering within a document.
    op.add_column("chunk", sa.Column("course_id", sa.UUID(), nullable=True))
    op.add_column(
        "chunk",
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
    )
    # Backfill course_id from the parent document for any existing rows, then enforce NOT NULL.
    op.execute(
        "UPDATE chunk SET course_id = document.course_id "
        "FROM document WHERE document.id = chunk.document_id"
    )
    op.alter_column("chunk", "course_id", nullable=False)
    op.create_foreign_key("fk_chunk_course_id", "chunk", "course", ["course_id"], ["id"])
    op.create_index(op.f("ix_chunk_course_id"), "chunk", ["course_id"], unique=False)
    # Drop the temporary server default; the app sets chunk_index explicitly.
    op.alter_column("chunk", "chunk_index", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_chunk_course_id"), table_name="chunk")
    op.drop_constraint("fk_chunk_course_id", "chunk", type_="foreignkey")
    op.drop_column("chunk", "chunk_index")
    op.drop_column("chunk", "course_id")
    op.drop_column("document", "error")
    op.drop_column("document", "storage_key")
    # Note: Postgres cannot easily drop a single enum value; 'failed' is left in place.
