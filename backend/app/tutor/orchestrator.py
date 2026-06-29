"""The tutor orchestrator: classify → route → (retrieve → generate → cite) / refuse / escalate.

This is a small explicit state machine. It mirrors the LangGraph node design described in
ai-tutor.md (classify, retrieve, generate, cite, plus refuse/escalate branches) without
pulling in the LangGraph dependency for v1 — the structure stays swappable if we adopt it.

A question enters; one of three paths runs:
- escalate  — student asked for a human, or no material was relevant enough to answer.
- assignment — looked like "do my homework": guide with hints, flag for the instructor.
- question  — retrieve course chunks, generate a grounded answer, attach a citation.

The exchange (question + answer) is persisted as two Messages owned by the student.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import EscalationStatus, MessageRole
from app.models.identity import User
from app.models.sessions import Message
from app.tutor import guardrails
from app.tutor.generation import get_generator
from app.tutor.retrieval import retrieve


@dataclass
class TutorReply:
    answer: str
    citation: str | None
    escalated: bool
    flagged: bool


def answer_question(db: Session, course_id: uuid.UUID, student: User, question: str) -> TutorReply:
    intent = guardrails.classify_intent(question)

    if intent is guardrails.Intent.escalate:
        reply = TutorReply(guardrails.ESCALATE_MESSAGE, citation=None, escalated=True, flagged=False)
        _persist(db, course_id, student, question, reply)
        return reply

    # Retrieve course-scoped material for both the question and assignment paths.
    passages = retrieve(db, course_id, question)
    best = passages[0].similarity if passages else 0.0
    grounded = bool(passages) and best >= settings.tutor_min_similarity

    if intent is guardrails.Intent.assignment:
        # Don't complete graded work — guide instead, and flag for the instructor to review.
        reply = TutorReply(
            guardrails.ASSIGNMENT_GUIDANCE,
            citation=passages[0].citation if grounded else None,
            escalated=False,
            flagged=True,
        )
        _persist(db, course_id, student, question, reply)
        return reply

    if not grounded:
        # Nothing relevant enough — never invent an answer or a citation. Escalate.
        reply = TutorReply(guardrails.NOT_SURE_MESSAGE, citation=None, escalated=True, flagged=False)
        _persist(db, course_id, student, question, reply)
        return reply

    # Normal path: generate a grounded answer and cite the top passage.
    answer = get_generator().answer(question, passages)
    reply = TutorReply(answer, citation=passages[0].citation, escalated=False, flagged=False)
    _persist(db, course_id, student, question, reply)
    return reply


def _persist(db: Session, course_id: uuid.UUID, student: User, question: str, reply: TutorReply) -> None:
    """Store the question and the AI answer as two Messages owned by the student."""
    esc = EscalationStatus.needs if reply.escalated else None
    db.add(
        Message(
            course_id=course_id,
            author=student.email,
            role=MessageRole.user,
            text=question,
            flagged=reply.flagged,
            escalation_status=esc,
        )
    )
    db.add(
        Message(
            course_id=course_id,
            author=student.email,
            role=MessageRole.ai,
            text=reply.answer,
            citation=reply.citation,
        )
    )
    db.commit()
