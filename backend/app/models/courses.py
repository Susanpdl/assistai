"""Course and Enrollment — who owns a class and who is allowed into it."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk
from app.models.enums import EnrollmentStatus


class Course(Base, TimestampMixin):
    __tablename__ = "course"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Short, shareable code students type to request enrollment (distinct from `code`,
    # which is the human course code like "CS 310").
    join_code: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    # One instructor owns many courses.
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )


class Enrollment(Base, TimestampMixin):
    __tablename__ = "enrollment"
    # A student can only have one enrollment row per course.
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course.id"), nullable=False, index=True
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        SAEnum(EnrollmentStatus, name="enrollment_status"),
        default=EnrollmentStatus.pending,
        nullable=False,
    )
    # When the instructor approved/rejected (null while still pending).
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
