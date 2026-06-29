"""Request/response shapes for announcements and comments."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class AnnouncementUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: uuid.UUID
    author: str  # display name
    author_role: str
    text: str
    created_at: datetime


class AnnouncementOut(BaseModel):
    id: uuid.UUID
    author: str
    text: str
    created_at: datetime
    comments: list[CommentOut] = []
