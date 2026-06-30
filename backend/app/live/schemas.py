"""Request/response shapes for live-session and poll endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import SessionStatus


class SessionOut(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    status: SessionStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None


class PollCreate(BaseModel):
    question: str
    options: list[str]
    # Optional: the correct option (must be one of `options`). Hidden from students until reveal.
    correct_option: str | None = None


class ActivityOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    question: str
    options: list[str]
    correct_option: str | None = None
    revealed: bool


class ResultsOut(BaseModel):
    activity_id: uuid.UUID
    tallies: dict[str, int]
    total: int
    revealed: bool
