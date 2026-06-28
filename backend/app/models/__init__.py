"""Import every model so `Base.metadata` knows about all tables.

Alembic's autogenerate and `Base.metadata.create_all` both rely on the models being
imported somewhere; importing them here (and re-exporting) is that single place.
"""

from app.models.announcements import Announcement, Comment
from app.models.auth import LoginToken
from app.models.base import Base
from app.models.content import Chunk, Document
from app.models.courses import Course, Enrollment
from app.models.identity import User
from app.models.sessions import (
    Activity,
    ActivityResponse,
    Attendance,
    Message,
    Session,
)

__all__ = [
    "Base",
    "User",
    "LoginToken",
    "Course",
    "Enrollment",
    "Session",
    "Message",
    "Document",
    "Chunk",
    "Activity",
    "ActivityResponse",
    "Attendance",
    "Announcement",
    "Comment",
]
