"""Phase 2 — courses & enrollment tests (see docs/features/enrollment-approval.md).

Covers: instructor creates a course (student can't); enroll-by-code creates pending and is
idempotent; bad code 404; approve grants access, reject denies; non-owner can't decide (403);
unapproved student blocked from course content (403); rejected student can re-request; role-
aware course listing; decision emails the student.
"""

import uuid

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

from tests.conftest import TEST_DOMAIN


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@{TEST_DOMAIN}"


def _login(sender, email: str) -> TestClient:
    """Return an authenticated client for `email` (role depends on the allowlist at this point)."""
    client = TestClient(app, follow_redirects=False)
    client.post("/auth/request", json={"email": email})
    client.get(f"/auth/verify?token={sender.last_token()}")
    return client


def _make_course(instr: TestClient, code="CS 101", name="Intro") -> dict:
    resp = instr.post("/courses", json={"code": code, "name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_instructor_creates_course_student_cannot(monkeypatch, sender):
    instr_email = _email()
    monkeypatch.setattr(settings, "instructor_emails", instr_email)

    instr = _login(sender, instr_email)
    course = _make_course(instr)
    assert course["is_owner"] is True
    assert course["join_code"] and len(course["join_code"]) == 6

    student = _login(sender, _email())
    assert student.post("/courses", json={"code": "X", "name": "Y"}).status_code == 403


def test_enroll_creates_pending_and_is_idempotent(monkeypatch, sender):
    instr_email = _email()
    monkeypatch.setattr(settings, "instructor_emails", instr_email)
    instr = _login(sender, instr_email)
    course = _make_course(instr)

    student = _login(sender, _email())
    first = student.post("/courses/enroll", json={"join_code": course["join_code"]})
    assert first.status_code == 200
    assert first.json()["status"] == "pending"

    # Requesting again is a no-op, not a duplicate.
    again = student.post("/courses/enroll", json={"join_code": course["join_code"]})
    assert again.json()["status"] == "pending"

    pending = instr.get(f"/courses/{course['id']}/enrollments?status_filter=pending").json()
    assert len(pending) == 1


def test_enroll_bad_join_code_404(monkeypatch, sender):
    monkeypatch.setattr(settings, "instructor_emails", "")
    student = _login(sender, _email())
    assert student.post("/courses/enroll", json={"join_code": "ZZZZZZ"}).status_code == 404


def test_approve_grants_access_and_emails_student(monkeypatch, sender):
    instr_email = _email()
    monkeypatch.setattr(settings, "instructor_emails", instr_email)
    instr = _login(sender, instr_email)
    course = _make_course(instr, name="Algorithms")

    student_email = _email()
    student = _login(sender, student_email)
    student.post("/courses/enroll", json={"join_code": course["join_code"]})

    # Blocked while pending.
    assert student.get(f"/courses/{course['id']}").status_code == 403

    enr = instr.get(f"/courses/{course['id']}/enrollments").json()[0]
    decision = instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "approved"})
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"

    # Access granted now.
    assert student.get(f"/courses/{course['id']}").status_code == 200

    # The student was emailed about the decision.
    decision_mail = [m for m in sender.sent if m["to"] == student_email and "Algorithms" in m["subject"]]
    assert decision_mail, "no enrollment-decision email sent to student"


def test_reject_denies_access(monkeypatch, sender):
    instr_email = _email()
    monkeypatch.setattr(settings, "instructor_emails", instr_email)
    instr = _login(sender, instr_email)
    course = _make_course(instr)

    student = _login(sender, _email())
    student.post("/courses/enroll", json={"join_code": course["join_code"]})
    enr = instr.get(f"/courses/{course['id']}/enrollments").json()[0]
    instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "rejected"})

    assert student.get(f"/courses/{course['id']}").status_code == 403


def test_non_owner_instructor_cannot_decide(monkeypatch, sender):
    owner_email, other_email = _email(), _email()
    monkeypatch.setattr(settings, "instructor_emails", f"{owner_email},{other_email}")

    owner = _login(sender, owner_email)
    other = _login(sender, other_email)
    course = _make_course(owner)

    student = _login(sender, _email())
    student.post("/courses/enroll", json={"join_code": course["join_code"]})
    enr = owner.get(f"/courses/{course['id']}/enrollments").json()[0]

    # A different instructor (not the owner) must not be able to decide.
    assert other.post(f"/enrollments/{enr['id']}/decision", json={"decision": "approved"}).status_code == 403


def test_rejected_student_can_rerequest(monkeypatch, sender):
    instr_email = _email()
    monkeypatch.setattr(settings, "instructor_emails", instr_email)
    instr = _login(sender, instr_email)
    course = _make_course(instr)

    student = _login(sender, _email())
    student.post("/courses/enroll", json={"join_code": course["join_code"]})
    enr = instr.get(f"/courses/{course['id']}/enrollments").json()[0]
    instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "rejected"})

    # Re-request flips the rejected row back to pending.
    re = student.post("/courses/enroll", json={"join_code": course["join_code"]})
    assert re.json()["status"] == "pending"
    pending = instr.get(f"/courses/{course['id']}/enrollments?status_filter=pending").json()
    assert len(pending) == 1


def test_list_courses_is_role_aware(monkeypatch, sender):
    instr_email = _email()
    monkeypatch.setattr(settings, "instructor_emails", instr_email)
    instr = _login(sender, instr_email)
    course = _make_course(instr)

    student = _login(sender, _email())
    # Not approved yet -> student sees nothing.
    assert student.get("/courses").json() == []

    student.post("/courses/enroll", json={"join_code": course["join_code"]})
    enr = instr.get(f"/courses/{course['id']}/enrollments").json()[0]
    instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "approved"})

    student_courses = student.get("/courses").json()
    assert len(student_courses) == 1
    assert student_courses[0]["id"] == course["id"]
    assert student_courses[0]["join_code"] is None  # students don't see the join code
    assert student_courses[0]["is_owner"] is False

    instr_courses = instr.get("/courses").json()
    assert any(c["id"] == course["id"] and c["join_code"] for c in instr_courses)
