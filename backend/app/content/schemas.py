"""Request/response shapes for course content endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DocumentStatus


class DocumentOut(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    filename: str
    type: str
    status: DocumentStatus
    # How many searchable chunks were produced (0 while processing / on failure).
    chunk_count: int = 0
    # Populated only when status == failed.
    error: str | None = None
    uploaded_at: datetime
