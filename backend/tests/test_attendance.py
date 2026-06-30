"""Phase 6 — attendance tests (see docs/features/attendance.md).

Covers: a valid current code marks present when no poll ran; an expired code is rejected
(replay); with a poll pushed, code-only is not present until the student also answers; one
account per device per session (device binding); the instructor roster and access control.

Polls are answered by inserting an ActivityResponse directly (the WS answer path itself is
covered in test_live); attendance only reads that the response exists.
"""

import uuid

from fastapi.testclient import TestClient

from app.attendance import codes
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models.sessions import ActivityResponse
from app.models.identity import User
from tests.conftest import TEST_DOMAIN


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@{TEST_DOMAIN}"


def _login(sender, email: str) -> TestClient:
    client = TestClient(app, follow_redirects=False)
    client.post("/auth/request", json={"email": email})
    client.get(f"/auth/verify?token={sender.last_token()}")
    return client


def _instructor(monkeypatch, sender) -> TestClient:
    email = _email()
    monkeypatch.setattr(settings, "instructor_emails", email)
    return _login(sender, email)


def _make_course(client: TestClient) -> dict:
    return client.post("/courses", json={"code": "CS 310", "name": "OS"}).json()


def _approved_student(instr: TestClient, sender, course) -> tuple[TestClient, str]:
    email = _email()
    student = _login(sender, email)
    enr = student.post("/courses/enroll", json={"join_code": course["join_code"]}).json()
    instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "approved"})
    return student, email


def _start(instr: TestClient, course) -> str:
    return instr.post(f"/courses/{course['id']}/sessions").json()["id"]


def _code(instr: TestClient, sid: str) -> str:
    return instr.get(f"/sessions/{sid}/attendance/code").json()["code"]


def _student_id(email: str) -> uuid.UUID:
    db = SessionLocal()
    try:
        return db.execute(
            User.__table__.select().where(User.email == email)
        ).first()[0]
    finally:
        db.close()


def _answer_poll(activity_id: str, email: str) -> None:
    db = SessionLocal()
    try:
        db.add(ActivityResponse(activity_id=uuid.UUID(activity_id), student_id=_student_id(email), choice="A"))
        db.commit()
    finally:
        db.close()


# --- tests -----------------------------------------------------------------

def test_valid_code_no_poll_is_present(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student, _ = _approved_student(instr, sender, course)
    sid = _start(instr, course)

    resp = student.post(
        f"/sessions/{sid}/attendance/checkin",
        json={"code": _code(instr, sid), "device_id": "dev-1"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["present"] is True
    assert body["proofs"] == ["code"]
    assert body["needs_poll"] is False


def test_expired_code_rejected(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student, _ = _approved_student(instr, sender, course)
    sid = _start(instr, course)

    # A code from a window well outside the grace window.
    old = codes._code_for(sid, codes._window() - 5)
    resp = student.post(
        f"/sessions/{sid}/attendance/checkin", json={"code": old, "device_id": "dev-1"}
    )
    assert resp.status_code == 422


def test_code_then_poll_required(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student, email = _approved_student(instr, sender, course)
    sid = _start(instr, course)

    poll = instr.post(
        f"/sessions/{sid}/activities", json={"question": "q", "options": ["A", "B"]}
    ).json()

    # Code only, but a poll was pushed → not present yet, needs the poll answer.
    first = student.post(
        f"/sessions/{sid}/attendance/checkin",
        json={"code": _code(instr, sid), "device_id": "dev-1"},
    ).json()
    assert first["present"] is False
    assert first["needs_poll"] is True

    # Answer the poll, then check in again → now present with both proofs.
    _answer_poll(poll["id"], email)
    second = student.post(
        f"/sessions/{sid}/attendance/checkin",
        json={"code": _code(instr, sid), "device_id": "dev-1"},
    ).json()
    assert second["present"] is True
    assert second["proofs"] == ["code", "poll"]


def test_device_binding_blocks_second_account(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    s1, _ = _approved_student(instr, sender, course)
    s2, _ = _approved_student(instr, sender, course)
    sid = _start(instr, course)

    assert s1.post(
        f"/sessions/{sid}/attendance/checkin",
        json={"code": _code(instr, sid), "device_id": "shared-phone"},
    ).status_code == 200

    blocked = s2.post(
        f"/sessions/{sid}/attendance/checkin",
        json={"code": _code(instr, sid), "device_id": "shared-phone"},
    )
    assert blocked.status_code == 409  # one account per device per session


def test_roster_and_access(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    present_student, _ = _approved_student(instr, sender, course)
    _absent_student, _ = _approved_student(instr, sender, course)
    sid = _start(instr, course)

    present_student.post(
        f"/sessions/{sid}/attendance/checkin",
        json={"code": _code(instr, sid), "device_id": "dev-a"},
    )

    roster = instr.get(f"/sessions/{sid}/attendance").json()
    assert roster["total"] == 2
    assert roster["present"] == 1
    statuses = {r["status"] for r in roster["rows"]}
    assert statuses == {"present", "absent"}

    # A student may not read the rotating code or the roster.
    assert present_student.get(f"/sessions/{sid}/attendance/code").status_code == 403
    assert present_student.get(f"/sessions/{sid}/attendance").status_code == 403


def test_course_attendance_summary(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student, _ = _approved_student(instr, sender, course)

    # Two sessions; the student checks in to both (no poll → code alone is present).
    sid1 = _start(instr, course)
    student.post(f"/sessions/{sid1}/attendance/checkin", json={"code": _code(instr, sid1), "device_id": "d1"})
    instr.post(f"/sessions/{sid1}/end")

    sid2 = _start(instr, course)
    student.post(f"/sessions/{sid2}/attendance/checkin", json={"code": _code(instr, sid2), "device_id": "d1"})

    summary = instr.get(f"/courses/{course['id']}/attendance/summary").json()
    assert len(summary["sessions"]) == 2  # both within the 4-month window, newest first
    for s in summary["sessions"]:
        assert s["present"] == 1 and s["total"] == 1
        assert s["date"] is not None
        present_students = [r for r in s["students"] if r["status"] == "present"]
        assert len(present_students) == 1
        assert "name" in present_students[0] and "email" in present_students[0]

    # A different instructor can't read it.
    other = _instructor(monkeypatch, sender)
    assert other.get(f"/courses/{course['id']}/attendance/summary").status_code == 403


def test_finalize_on_session_end(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student, email = _approved_student(instr, sender, course)
    sid = _start(instr, course)
    poll = instr.post(
        f"/sessions/{sid}/activities", json={"question": "q", "options": ["A", "B"]}
    ).json()
    student.post(
        f"/sessions/{sid}/attendance/checkin",
        json={"code": _code(instr, sid), "device_id": "dev-1"},
    )
    _answer_poll(poll["id"], email)

    # End the session → finalize; the roster reflects present (code + poll).
    assert instr.post(f"/sessions/{sid}/end").status_code == 200
    roster = instr.get(f"/sessions/{sid}/attendance").json()
    assert roster["present"] == 1
