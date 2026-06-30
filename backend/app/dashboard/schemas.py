"""Request/response shapes for the instructor dashboard."""

from pydantic import BaseModel, Field


class DashboardOut(BaseModel):
    students_enrolled: int
    pending_requests: int
    questions_today: int
    questions_total: int
    escalated_open: int
    escalated_answered: int


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=5000)
