"""Live sessions and everything anchored to them: chat messages, polls/quizzes,
their responses, and attendance.

The architecture note: attendance reuses Session + Activity + ActivityResponse rather
than inventing new infrastructure — the "present" rule is "did this student produce a
valid code check-in AND (if a poll ran) an ActivityResponse in this Session?".
"""

import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk
from app.models.enums import ActivityType, AttendanceStatus, MessageRole


class Session(Base):
    __tablename__ = "session"

    id: Mapped[uuid.UUID] = uuid_pk()
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)


class Message(Base, TimestampMixin):
    __tablename__ = "message"

    id: Mapped[uuid.UUID] = uuid_pk()
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course.id"), nullable=False, index=True
    )
    # Null session_id means async study; otherwise the message belongs to a live session.
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("session.id"), nullable=True, index=True
    )
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole, name="message_role"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Citation is set only on grounded AI answers (e.g. "Week 4, p.12").
    citation: Mapped[str | None] = mapped_column(String(200), nullable=True)


class Activity(Base, TimestampMixin):
    __tablename__ = "activity"

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("session.id"), nullable=False, index=True
    )
    type: Mapped[ActivityType] = mapped_column(SAEnum(ActivityType, name="activity_type"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    # The answer choices, stored as a JSON array of strings.
    options: Mapped[list] = mapped_column(JSONB, nullable=False)


class ActivityResponse(Base, TimestampMixin):
    __tablename__ = "activity_response"

    id: Mapped[uuid.UUID] = uuid_pk()
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activity.id"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    choice: Mapped[str] = mapped_column(String(500), nullable=False)


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("session.id"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, name="attendance_status"), nullable=False
    )
    # Which checks passed, e.g. {"code": true, "poll": true}.
    proofs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
