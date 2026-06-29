"""Enumerated values used across the data model.

Using Python enums (stored as Postgres enum types) keeps the allowed values in one
place and lets the database reject anything outside the set.
"""

import enum


class Role(str, enum.Enum):
    student = "student"
    instructor = "instructor"


class EnrollmentStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class MessageRole(str, enum.Enum):
    user = "user"
    ai = "ai"


class DocumentStatus(str, enum.Enum):
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class ActivityType(str, enum.Enum):
    poll = "poll"
    quiz = "quiz"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"


class EscalationStatus(str, enum.Enum):
    needs = "needs"  # escalated to the instructor, awaiting a human answer
    answered = "answered"  # the instructor has responded


class SessionStatus(str, enum.Enum):
    live = "live"  # class is in session; students may join the room
    ended = "ended"  # the session is over; the room is closed
