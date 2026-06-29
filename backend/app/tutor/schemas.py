"""Request/response shapes for the AI tutor endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import EscalationStatus, MessageRole


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    citation: str | None = None
    escalated: bool = False
    flagged: bool = False


class MessageOut(BaseModel):
    id: uuid.UUID
    role: MessageRole
    text: str
    citation: str | None = None
    flagged: bool = False
    created_at: datetime


class EscalationOut(BaseModel):
    id: uuid.UUID
    question: str
    student: str  # the student's email
    status: EscalationStatus
    created_at: datetime
