"""attendance: unique (session_id, student_id) + device_binding table

Revision ID: e5b6c7d8f9a0
Revises: d4a5b6c7e8f9
Create Date: 2026-06-24 14:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5b6c7d8f9a0"
down_revision: str | None = "d4a5b6c7e8f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_attendance_student", "attendance", ["session_id", "student_id"]
    )
    op.create_table(
        "device_binding",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.String(length=200), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["session_id"], ["session.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "device_id", name="uq_device_binding_session_device"),
    )
    op.create_index(
        op.f("ix_device_binding_session_id"), "device_binding", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_device_binding_student_id"), "device_binding", ["student_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_device_binding_student_id"), table_name="device_binding")
    op.drop_index(op.f("ix_device_binding_session_id"), table_name="device_binding")
    op.drop_table("device_binding")
    op.drop_constraint("uq_attendance_student", "attendance", type_="unique")
