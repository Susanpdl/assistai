"""Attendance business logic: the present-rule, check-in, the roster view, and finalize.

The rule (v1): a student is **present** if they entered a valid current code, AND — when a poll
was pushed this session — also answered a poll. If no poll was pushed, a valid code alone counts.
Two proofs at different moments (code + poll) is what makes a forwarded one-off code insufficient.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.attendance import codes
from app.models.courses import Enrollment
from app.models.enums import AttendanceStatus, EnrollmentStatus, SessionStatus
from app.models.identity import User
from app.models.sessions import Activity, ActivityResponse, Attendance, DeviceBinding, Session


@dataclass
class CheckinResult:
    ok: bool
    error: str | None = None  # "not_live" | "bad_code" | "device_taken"
    status: AttendanceStatus | None = None
    proofs: list[str] | None = None
    needs_poll: bool = False


@dataclass
class AttendanceRow:
    student: str  # email
    status: AttendanceStatus
    proofs: list[str]
    checked_in: bool
    checked_in_at: object | None  # datetime | None


def session_has_poll(db: DbSession, session_id: uuid.UUID) -> bool:
    return db.execute(
        select(Activity.id).where(Activity.session_id == session_id).limit(1)
    ).first() is not None


def student_answered(db: DbSession, session_id: uuid.UUID, student_id: uuid.UUID) -> bool:
    return db.execute(
        select(ActivityResponse.id)
        .join(Activity, Activity.id == ActivityResponse.activity_id)
        .where(Activity.session_id == session_id, ActivityResponse.student_id == student_id)
        .limit(1)
    ).first() is not None


def _status(has_poll: bool, answered: bool) -> AttendanceStatus:
    if not has_poll:
        return AttendanceStatus.present  # code alone counts when no poll was pushed
    return AttendanceStatus.present if answered else AttendanceStatus.absent


def _proofs(answered: bool) -> list[str]:
    return ["code", "poll"] if answered else ["code"]


def checkin(
    db: DbSession, session: Session, student_id: uuid.UUID, code: str, device_id: str
) -> CheckinResult:
    if session.status != SessionStatus.live:
        return CheckinResult(ok=False, error="not_live")
    if not device_id or not codes.is_valid(str(session.id), code):
        return CheckinResult(ok=False, error="bad_code")

    # Device binding: one account per device per session.
    binding = db.execute(
        select(DeviceBinding).where(
            DeviceBinding.session_id == session.id, DeviceBinding.device_id == device_id
        )
    ).scalar_one_or_none()
    if binding is not None and binding.student_id != student_id:
        return CheckinResult(ok=False, error="device_taken")
    if binding is None:
        db.add(DeviceBinding(session_id=session.id, device_id=device_id, student_id=student_id))

    answered = student_answered(db, session.id, student_id)
    has_poll = session_has_poll(db, session.id)
    proofs = _proofs(answered)
    status = _status(has_poll, answered)

    att = db.execute(
        select(Attendance).where(
            Attendance.session_id == session.id, Attendance.student_id == student_id
        )
    ).scalar_one_or_none()
    if att is None:
        db.add(Attendance(session_id=session.id, student_id=student_id, status=status, proofs=proofs))
    else:
        att.proofs = proofs
        att.status = status

    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # a concurrent check-in claimed the device first
        return CheckinResult(ok=False, error="device_taken")

    return CheckinResult(
        ok=True, status=status, proofs=proofs, needs_poll=has_poll and not answered
    )


def roster(db: DbSession, session: Session) -> list[AttendanceRow]:
    """Every approved student with their live attendance status for this session."""
    students = db.execute(
        select(User)
        .join(Enrollment, Enrollment.student_id == User.id)
        .where(
            Enrollment.course_id == session.course_id,
            Enrollment.status == EnrollmentStatus.approved,
        )
    ).scalars().all()
    att_by_student = {
        a.student_id: a
        for a in db.execute(
            select(Attendance).where(Attendance.session_id == session.id)
        ).scalars()
    }
    has_poll = session_has_poll(db, session.id)

    rows: list[AttendanceRow] = []
    for student in students:
        a = att_by_student.get(student.id)
        if a is None:
            rows.append(AttendanceRow(student.email, AttendanceStatus.absent, [], False, None))
            continue
        answered = student_answered(db, session.id, student.id)
        rows.append(
            AttendanceRow(
                student.email,
                _status(has_poll, answered),
                _proofs(answered),
                True,
                a.created_at,
            )
        )
    return rows


def finalize(db: DbSession, session: Session) -> None:
    """Persist the final computed status onto each checked-in record (called on session end)."""
    has_poll = session_has_poll(db, session.id)
    rows = db.execute(
        select(Attendance).where(Attendance.session_id == session.id)
    ).scalars().all()
    for a in rows:
        answered = student_answered(db, session.id, a.student_id)
        a.status = _status(has_poll, answered)
        a.proofs = _proofs(answered)
    db.commit()
