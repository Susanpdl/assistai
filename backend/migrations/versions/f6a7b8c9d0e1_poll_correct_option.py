"""poll: activity.correct_option

Revision ID: f6a7b8c9d0e1
Revises: e5b6c7d8f9a0
Create Date: 2026-06-30 14:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5b6c7d8f9a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("activity", sa.Column("correct_option", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("activity", "correct_option")
