"""Phase 1 — magic-link auth tests (see docs/features/auth-magic-link.md).

Covers: request → email sent; valid token logs in; invalid / used / expired tokens
rejected; logout invalidates the session; role guard blocks the wrong role (403).
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.deps import require_role
from app.auth.email import get_email_sender
from app.auth.router import router as auth_router
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models.auth import LoginToken
from app.models.enums import Role

from tests.conftest import TEST_DOMAIN, CapturingSender


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@{TEST_DOMAIN}"


def _login(client, sender, email: str):
    """Run the full request → verify flow; return the verify response."""
    resp = client.post("/auth/request", json={"email": email})
    assert resp.status_code == 200
    token = sender.last_token()
    assert token, "no magic-link token was emailed"
    return client.get(f"/auth/verify?token={token}")


def test_request_sends_magic_link(client, sender):
    email = _email()
    resp = client.post("/auth/request", json={"email": email})
    assert resp.status_code == 200
    assert resp.json() == {"status": "sent"}
    assert len(sender.sent) == 1
    assert sender.sent[0]["to"] == email
    assert "/auth/verify?token=" in sender.sent[0]["body"]


def test_request_unknown_email_still_200_and_no_leak(client, sender):
    # Always-200 so the endpoint can't be used to discover who has an account.
    resp = client.post("/auth/request", json={"email": _email()})
    assert resp.status_code == 200
    assert resp.json() == {"status": "sent"}


def test_valid_token_logs_in(client, sender):
    email = _email()
    verify = _login(client, sender, email)
    assert verify.status_code == 303
    assert verify.headers["location"] == settings.frontend_url

    me = client.get("/auth/me")
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == email
    assert body["role"] == "student"  # default role for non-allowlisted emails


def test_invalid_token_rejected(client):
    verify = client.get("/auth/verify?token=this-is-not-a-real-token")
    assert verify.status_code == 303
    assert "auth=invalid" in verify.headers["location"]
    assert client.get("/auth/me").status_code == 401


def test_used_token_is_single_use(client, sender):
    email = _email()
    resp = client.post("/auth/request", json={"email": email})
    assert resp.status_code == 200
    token = sender.last_token()

    first = client.get(f"/auth/verify?token={token}")
    assert first.status_code == 303
    assert first.headers["location"] == settings.frontend_url

    # A fresh client (no session) reusing the same token must be rejected.
    second = TestClient(app, follow_redirects=False)
    reused = second.get(f"/auth/verify?token={token}")
    assert "auth=invalid" in reused.headers["location"]


def test_expired_token_rejected(client, sender):
    email = _email()
    client.post("/auth/request", json={"email": email})
    token = sender.last_token()

    # Backdate the token's expiry directly in the DB.
    db = SessionLocal()
    try:
        row = db.query(LoginToken).filter(LoginToken.email == email).one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    verify = client.get(f"/auth/verify?token={token}")
    assert "auth=invalid" in verify.headers["location"]


def test_logout_invalidates_session(client, sender):
    _login(client, sender, _email())
    assert client.get("/auth/me").status_code == 200

    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_role_guard_blocks_student_allows_instructor(monkeypatch, sender):
    # A throwaway app that mounts the auth router plus one instructor-only route.
    guarded = FastAPI()
    guarded.include_router(auth_router)
    guarded.dependency_overrides[get_email_sender] = lambda: sender

    @guarded.get("/instructor-only")
    def _instructor_only(user=Depends(require_role(Role.instructor))):
        return {"ok": True}

    instructor_email = _email()
    monkeypatch.setattr(settings, "instructor_emails", instructor_email)

    gclient = TestClient(guarded, follow_redirects=False)

    # Student is blocked.
    student_token = _request_token(gclient, sender, _email())
    gclient.get(f"/auth/verify?token={student_token}")
    assert gclient.get("/instructor-only").status_code == 403

    # Instructor is allowed (new client = fresh session).
    iclient = TestClient(guarded, follow_redirects=False)
    instructor_token = _request_token(iclient, sender, instructor_email)
    iclient.get(f"/auth/verify?token={instructor_token}")
    assert iclient.get("/instructor-only").status_code == 200


def _request_token(client, sender: CapturingSender, email: str) -> str:
    client.post("/auth/request", json={"email": email})
    return sender.last_token()
