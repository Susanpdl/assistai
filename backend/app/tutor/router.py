"""AI Tutor endpoints (Phase 4).

A student asks a free-text question about a course they're approved in; the tutor answers
grounded in that course's material with a citation, or guides/escalates per the guardrails.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.courses.deps import get_owned_course, require_course_access
from app.db import get_db
from app.models.courses import Course
from app.models.enums import MessageRole
from app.models.identity import User
from app.models.sessions import Message
from app.tutor.orchestrator import answer_question
from app.tutor.schemas import AskRequest, AskResponse, EscalationOut, MessageOut

router = APIRouter(tags=["tutor"])


@router.post("/courses/{course_id}/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    course: Course = Depends(require_course_access),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AskResponse:
    reply = answer_question(db, course.id, user, payload.question.strip())
    return AskResponse(
        answer=reply.answer,
        citation=reply.citation,
        escalated=reply.escalated,
        flagged=reply.flagged,
    )


@router.get("/courses/{course_id}/messages", response_model=list[MessageOut])
def list_messages(
    course: Course = Depends(require_course_access),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MessageOut]:
    """The caller's own async-study history for this course, oldest first."""
    rows = db.execute(
        select(Message)
        .where(Message.course_id == course.id, Message.author == user.email)
        .order_by(Message.created_at)
    ).scalars().all()
    return [
        MessageOut(
            id=m.id,
            role=m.role,
            text=m.text,
            citation=m.citation,
            flagged=m.flagged,
            created_at=m.created_at,
        )
        for m in rows
    ]


@router.get("/courses/{course_id}/escalations", response_model=list[EscalationOut])
def list_escalations(
    course: Course = Depends(get_owned_course),
    db: Session = Depends(get_db),
) -> list[EscalationOut]:
    """Questions escalated to the instructor for this course, newest first (owner only)."""
    rows = db.execute(
        select(Message)
        .where(
            Message.course_id == course.id,
            Message.role == MessageRole.user,
            Message.escalation_status.is_not(None),
        )
        .order_by(Message.created_at.desc())
    ).scalars().all()
    return [
        EscalationOut(
            id=m.id,
            question=m.text,
            student=m.author,
            status=m.escalation_status,
            created_at=m.created_at,
        )
        for m in rows
    ]
