"""Instructor dashboard endpoints (Phase 8).

The dashboard mostly reads and summarizes data the earlier features produce (enrollments,
questions, escalations). "Mark answered" closes an escalation and delivers the instructor's
answer back into the student's tutor chat so they actually see it.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.auth.deps import get_current_user
from app.courses.deps import get_owned_course
from app.dashboard.schemas import AnswerRequest, DashboardOut
from app.db import get_db
from app.models.courses import Course, Enrollment
from app.models.enums import EnrollmentStatus, EscalationStatus, MessageRole
from app.models.identity import User
from app.models.sessions import Message

router = APIRouter(tags=["dashboard"])


def _count(db: DbSession, stmt) -> int:
    return int(db.execute(stmt).scalar_one())


@router.get("/courses/{course_id}/dashboard", response_model=DashboardOut)
def dashboard(
    course: Course = Depends(get_owned_course),
    db: DbSession = Depends(get_db),
) -> DashboardOut:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    enroll_base = select(func.count()).select_from(Enrollment).where(
        Enrollment.course_id == course.id
    )
    q_base = select(func.count()).select_from(Message).where(
        Message.course_id == course.id, Message.role == MessageRole.user
    )

    return DashboardOut(
        students_enrolled=_count(
            db, enroll_base.where(Enrollment.status == EnrollmentStatus.approved)
        ),
        pending_requests=_count(
            db, enroll_base.where(Enrollment.status == EnrollmentStatus.pending)
        ),
        questions_today=_count(db, q_base.where(Message.created_at >= today_start)),
        questions_total=_count(db, q_base),
        escalated_open=_count(
            db, q_base.where(Message.escalation_status == EscalationStatus.needs)
        ),
        escalated_answered=_count(
            db, q_base.where(Message.escalation_status == EscalationStatus.answered)
        ),
    )


@router.post("/escalations/{escalation_id}/answer", status_code=status.HTTP_204_NO_CONTENT)
def answer_escalation(
    escalation_id: uuid.UUID,
    payload: AnswerRequest,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> None:
    """Close an escalation and deliver the instructor's answer into the student's chat."""
    msg = db.get(Message, escalation_id)
    if msg is None or msg.escalation_status is None:
        raise HTTPException(status_code=404, detail="Escalation not found")
    course = db.get(Course, msg.course_id)
    if course is None or course.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not the course owner")

    msg.escalation_status = EscalationStatus.answered
    # Deliver the answer back into the student's tutor history (author = the student's email).
    db.add(
        Message(
            course_id=msg.course_id,
            author=msg.author,
            role=MessageRole.ai,
            text=payload.answer,
            citation="Answered by your instructor",
        )
    )
    db.commit()
