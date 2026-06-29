"""live: session.status, activity.revealed, unique (activity_id, student_id)

Revision ID: d4a5b6c7e8f9
Revises: c3f4a5b6d7e8
Create Date: 2026-06-24 13:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4a5b6c7e8f9"
down_revision: str | None = "c3f4a5b6d7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

session_status = sa.Enum("live", "ended", name="session_status")


def upgrade() -> None:
    session_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "session",
        sa.Column("status", session_status, nullable=False, server_default="live"),
    )
    op.alter_column("session", "status", server_default=None)

    op.add_column(
        "activity",
        sa.Column("revealed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("activity", "revealed", server_default=None)

    op.create_unique_constraint(
        "uq_activity_response_student", "activity_response", ["activity_id", "student_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_activity_response_student", "activity_response", type_="unique")
    op.drop_column("activity", "revealed")
    op.drop_column("session", "status")
    session_status.drop(op.get_bind(), checkfirst=True)
