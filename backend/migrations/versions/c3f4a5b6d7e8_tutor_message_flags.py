"""tutor: message.flagged + message.escalation_status (+ escalation_status enum)

Revision ID: c3f4a5b6d7e8
Revises: b7e2a1c9d4f0
Create Date: 2026-06-24 12:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3f4a5b6d7e8"
down_revision: str | None = "b7e2a1c9d4f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

escalation_status = sa.Enum("needs", "answered", name="escalation_status")


def upgrade() -> None:
    escalation_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "message",
        sa.Column("flagged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("message", sa.Column("escalation_status", escalation_status, nullable=True))
    # Drop the temporary default now that existing rows are backfilled.
    op.alter_column("message", "flagged", server_default=None)


def downgrade() -> None:
    op.drop_column("message", "escalation_status")
    op.drop_column("message", "flagged")
    escalation_status.drop(op.get_bind(), checkfirst=True)
