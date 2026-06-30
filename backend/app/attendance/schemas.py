"""Request/response shapes for attendance endpoints."""

import uuid
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
    name: str
    student: str  # email
    status: AttendanceStatus
    proofs: list[str]
    checked_in: bool
    checked_in_at: datetime | None = None


class AttendanceListOut(BaseModel):
    present: int
    total: int
    rows: list[AttendanceRowOut]


class AttendanceStudentOut(BaseModel):
    name: str
    email: str
    status: AttendanceStatus


class SessionAttendanceOut(BaseModel):
    session_id: uuid.UUID
    date: datetime | None  # the session's start time
    status: str  # live | ended
    present: int
    total: int
    students: list[AttendanceStudentOut]


class CourseAttendanceSummaryOut(BaseModel):
    # Newest first, limited to the last ~4 months.
    sessions: list[SessionAttendanceOut]
