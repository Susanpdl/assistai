"""Request/response shapes for course and enrollment endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import EnrollmentStatus


class CourseCreate(BaseModel):
    code: str
    name: str


class CourseOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    # Only populated for the owner (students don't need to see other students' join code).
    join_code: str | None = None
    is_owner: bool = False


class EnrollRequest(BaseModel):
    join_code: str


class StudentOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str

    model_config = {"from_attributes": True}


class EnrollmentOut(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    status: EnrollmentStatus
    requested_at: datetime
    decided_at: datetime | None = None
    # Present when an instructor lists requests; omitted on a student's own view.
    student: StudentOut | None = None


class DecisionRequest(BaseModel):
    # Only these two are valid decisions; pending is not a decision.
    decision: EnrollmentStatus
