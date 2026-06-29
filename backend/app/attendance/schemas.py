"""Request/response shapes for attendance endpoints."""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AttendanceStatus


class CodeOut(BaseModel):
    code: str
    expires_in_seconds: int


class CheckinRequest(BaseModel):
    code: str
    device_id: str


class CheckinResponse(BaseModel):
    status: AttendanceStatus
    proofs: list[str]
    present: bool
    needs_poll: bool


class AttendanceRowOut(BaseModel):
    student: str
    status: AttendanceStatus
    proofs: list[str]
    checked_in: bool
    checked_in_at: datetime | None = None


class AttendanceListOut(BaseModel):
    present: int
    total: int
    rows: list[AttendanceRowOut]
