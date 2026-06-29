"""Shared pytest fixtures for the auth integration tests.

These tests run against the real docker-compose Postgres + Redis (they exercise the full
session/token path), so the stack must be up. We isolate by using a dedicated email
domain and cleaning up those rows after each test.
"""

import re

import pytest
from fastapi.testclient import TestClient

from sqlalchemy import or_

from app.auth.email import get_email_sender
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models.auth import LoginToken
from app.models.content import Chunk, Document
from app.models.courses import Course, Enrollment
from app.models.identity import User
from app.models.sessions import (
    Activity,
    ActivityResponse,
    Attendance,
    DeviceBinding,
    Message,
    Session,
)

# A normal (non special-use) domain so EmailStr validation passes; `.local` would be
# rejected by email-validator. No real mail is sent — the email backend is a fake.
TEST_DOMAIN = "assistai-test.com"


def _remove_storage(course_ids) -> None:
    """Delete any uploaded files for the given test courses from local storage."""
    import shutil
    from pathlib import Path

    base = Path(settings.storage_dir)
    for cid in course_ids:
        shutil.rmtree(base / str(cid), ignore_errors=True)


class CapturingSender:
    """Stand-in email sender that records what would have been sent."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})

    def last_token(self) -> str | None:
        if not self.sent:
            return None
        match = re.search(r"token=([A-Za-z0-9_\-]+)", self.sent[-1]["body"])
        return match.group(1) if match else None


@pytest.fixture(autouse=True)
def relax_rate_limits(monkeypatch):
    """Don't let the per-IP rate limiter (shared host in tests) trip across cases."""
    monkeypatch.setattr(settings, "auth_request_max_per_window", 10_000)


@pytest.fixture(autouse=True)
def cleanup_test_rows():
    yield
    db = SessionLocal()
    try:
        test_user_ids = [
            u.id for u in db.query(User).filter(User.email.like(f"%@{TEST_DOMAIN}")).all()
        ]
        if test_user_ids:
            course_ids = [
                c.id for c in db.query(Course).filter(Course.owner_id.in_(test_user_ids)).all()
            ]
            # Delete in FK order: responses/activities/sessions -> chunks/messages
            # -> documents -> enrollments -> courses ...
            if course_ids:
                session_ids = [
                    s.id
                    for s in db.query(Session).filter(Session.course_id.in_(course_ids)).all()
                ]
                if session_ids:
                    activity_ids = [
                        a.id
                        for a in db.query(Activity)
                        .filter(Activity.session_id.in_(session_ids))
                        .all()
                    ]
                    if activity_ids:
                        db.query(ActivityResponse).filter(
                            ActivityResponse.activity_id.in_(activity_ids)
                        ).delete(synchronize_session=False)
                        db.query(Activity).filter(Activity.id.in_(activity_ids)).delete(
                            synchronize_session=False
                        )
                    db.query(Attendance).filter(
                        Attendance.session_id.in_(session_ids)
                    ).delete(synchronize_session=False)
                    db.query(DeviceBinding).filter(
                        DeviceBinding.session_id.in_(session_ids)
                    ).delete(synchronize_session=False)
                    db.query(Session).filter(Session.id.in_(session_ids)).delete(
                        synchronize_session=False
                    )
                db.query(Chunk).filter(Chunk.course_id.in_(course_ids)).delete(
                    synchronize_session=False
                )
                db.query(Message).filter(Message.course_id.in_(course_ids)).delete(
                    synchronize_session=False
                )
                db.query(Document).filter(Document.course_id.in_(course_ids)).delete(
                    synchronize_session=False
                )
                _remove_storage(course_ids)
            db.query(Enrollment).filter(
                or_(
                    Enrollment.student_id.in_(test_user_ids),
                    Enrollment.course_id.in_(course_ids) if course_ids else False,
                )
            ).delete(synchronize_session=False)
            db.query(Course).filter(Course.owner_id.in_(test_user_ids)).delete(
                synchronize_session=False
            )
        db.query(LoginToken).filter(LoginToken.email.like(f"%@{TEST_DOMAIN}")).delete(
            synchronize_session=False
        )
        db.query(User).filter(User.email.like(f"%@{TEST_DOMAIN}")).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture
def sender():
    """Override the email dependency with a capturing sender for the duration of a test."""
    capturing = CapturingSender()
    app.dependency_overrides[get_email_sender] = lambda: capturing
    yield capturing
    app.dependency_overrides.pop(get_email_sender, None)


@pytest.fixture
def client():
    # Don't auto-follow the post-login redirect (it points at the frontend origin).
    return TestClient(app, follow_redirects=False)
