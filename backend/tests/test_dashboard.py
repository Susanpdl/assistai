"""Phase 8 — instructor dashboard tests (see docs/features/instructor-console.md).

Covers: stat counts match the data the earlier features produced; marking an escalation
answered moves it out of "needs" and delivers the answer into the student's chat; the
dashboard is owner-scoped.

Escalations are produced the real way: a student asks a question in a course with no indexed
material, so the tutor escalates (Phase 4).
"""

import uuid

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
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
    return client.post("/courses", json={"code": "CS 999", "name": "Empty"}).json()


def _approved_student(instr, sender, course) -> tuple[TestClient, str]:
    email = _email()
    student = _login(sender, email)
    enr = student.post("/courses/enroll", json={"join_code": course["join_code"]}).json()
    instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "approved"})
    return student, email


def test_dashboard_counts(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student, _ = _approved_student(instr, sender, course)
    _approved_student(instr, sender, course)  # a second approved student

    # A pending (not approved) student.
    pending = _login(sender, _email())
    pending.post("/courses/enroll", json={"join_code": course["join_code"]})

    # Two questions; both escalate (no material in the course).
    student.post(f"/courses/{course['id']}/ask", json={"question": "How does paging work?"})
    student.post(f"/courses/{course['id']}/ask", json={"question": "What is a semaphore?"})

    dash = instr.get(f"/courses/{course['id']}/dashboard").json()
    assert dash["students_enrolled"] == 2
    assert dash["pending_requests"] == 1
    assert dash["questions_today"] == 2
    assert dash["questions_total"] == 2
    assert dash["escalated_open"] == 2
    assert dash["escalated_answered"] == 0


def test_mark_answered_reaches_student_and_closes(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student, _ = _approved_student(instr, sender, course)
    student.post(f"/courses/{course['id']}/ask", json={"question": "Will this be on the exam?"})

    esc = instr.get(f"/courses/{course['id']}/escalations").json()
    assert len(esc) == 1 and esc[0]["status"] == "needs"

    answer = "Yes — focus on chapters 4 and 5."
    resp = instr.post(f"/escalations/{esc[0]['id']}/answer", json={"answer": answer})
    assert resp.status_code == 204

    # Escalation is closed.
    dash = instr.get(f"/courses/{course['id']}/dashboard").json()
    assert dash["escalated_open"] == 0
    assert dash["escalated_answered"] == 1

    # The student sees the instructor's answer in their chat history.
    history = student.get(f"/courses/{course['id']}/messages").json()
    ai_texts = [m["text"] for m in history if m["role"] == "ai"]
    assert answer in ai_texts


def test_dashboard_owner_scoped(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)

    other = _instructor(monkeypatch, sender)  # a different instructor
    assert other.get(f"/courses/{course['id']}/dashboard").status_code == 403
