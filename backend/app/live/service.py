"""Shared live-session logic: access roles, answer recording, tallies, and message shapes.

Kept separate from the routers so both the HTTP endpoints and the WebSocket handler use the
same rules (one response per student, course-scoped access, identical message envelopes).
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.models.courses import Course, Enrollment
from app.models.enums import EnrollmentStatus
from app.models.identity import User
from app.models.sessions import Activity, ActivityResponse, Session


def resolve_role(db: DbSession, session: Session, user: User) -> str | None:
    """Return 'instructor' (course owner), 'student' (approved enrollee), or None (no access)."""
    course = db.get(Course, session.course_id)
    if course is None:
        return None
    if course.owner_id == user.id:
        return "instructor"
    approved = db.execute(
        select(Enrollment).where(
            Enrollment.course_id == course.id,
            Enrollment.student_id == user.id,
            Enrollment.status == EnrollmentStatus.approved,
        )
    ).scalar_one_or_none()
    return "student" if approved is not None else None


def record_answer(db: DbSession, activity: Activity, student_id: uuid.UUID, choice: str) -> str:
    """Store one answer. Returns 'ok', 'duplicate', or 'invalid' (choice not an option)."""
    if choice not in activity.options:
        return "invalid"
    db.add(ActivityResponse(activity_id=activity.id, student_id=student_id, choice=choice))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # unique (activity_id, student_id) → already answered
        return "duplicate"
    return "ok"


def tally(db: DbSession, activity: Activity) -> tuple[dict[str, int], int]:
    """Count responses per option (every option present, zero-filled)."""
    counts = {opt: 0 for opt in activity.options}
    rows = db.execute(
        select(ActivityResponse.choice, func.count())
        .where(ActivityResponse.activity_id == activity.id)
        .group_by(ActivityResponse.choice)
    ).all()
    total = 0
    for choice, n in rows:
        counts[choice] = int(n)
        total += int(n)
    return counts, total


# --- WebSocket message envelopes (server → client) -------------------------

def session_state_msg(status: str, count: int) -> dict:
    return {"type": "session_state", "status": status, "connected_count": count}


def connected_count_msg(count: int) -> dict:
    return {"type": "connected_count", "count": count, "audience": "all"}


def poll_pushed_msg(activity: Activity) -> dict:
    return {
        "type": "poll_pushed",
        "audience": "all",
        "activity": {
            "id": str(activity.id),
            "question": activity.question,
            "options": activity.options,
        },
    }


def results_update_msg(activity_id, tallies: dict, total: int, *, audience: str) -> dict:
    return {
        "type": "results_update",
        "audience": audience,
        "activity_id": str(activity_id),
        "tallies": tallies,
        "total": total,
    }


def poll_revealed_msg(activity_id) -> dict:
    return {"type": "poll_revealed", "audience": "all", "activity_id": str(activity_id)}


def session_ended_msg() -> dict:
    return {"type": "session_ended", "audience": "all"}
