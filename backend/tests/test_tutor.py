"""Phase 4 — AI tutor tests (see docs/features/ai-tutor.md).

Covers the key cases from the feature doc:
- a factual course question returns an answer WITH a citation to a real chunk;
- "do my assignment" is guided/refused (flagged), not completed verbatim;
- a course with no relevant material → graceful "not sure" + escalate, no hallucinated citation;
- retrieval/access is course-scoped (a student can't ask in a course they're not approved in);
- chat history round-trips; unapproved students are blocked; escalations surface to the owner.

Run against the docker-compose Postgres + Redis. Generation uses the deterministic offline
LocalGenerator (no API key), so answers are reproducible.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import SessionLocal
from app.ingestion.pipeline import process_document
from app.main import app
from app.redis_client import redis_client
from app.tutor.guardrails import ASSIGNMENT_GUIDANCE
from tests.conftest import TEST_DOMAIN


@pytest.fixture(autouse=True)
def clear_ingest_queue():
    redis_client.delete(settings.ingest_queue_key)
    yield
    redis_client.delete(settings.ingest_queue_key)


# --- helpers ---------------------------------------------------------------

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


def _make_course(client: TestClient, code="CS 310", name="OS") -> dict:
    resp = client.post("/courses", json={"code": code, "name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _upload_and_index(instr, course_id, filename, text: bytes) -> None:
    resp = instr.post(
        f"/courses/{course_id}/documents",
        files={"file": (filename, text, "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    doc_id = uuid.UUID(resp.json()["id"])
    db = SessionLocal()
    try:
        process_document(db, doc_id)  # run the pipeline inline (stands in for the worker)
    finally:
        db.close()


def _approved_student(instr, sender, course) -> tuple[TestClient, str]:
    email = _email()
    student = _login(sender, email)
    enr = student.post("/courses/enroll", json={"join_code": course["join_code"]}).json()
    decision = instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "approved"})
    assert decision.status_code == 200, decision.text
    return student, email


OS_TEXT = (
    b"Paging maps a virtual address to a physical frame using a page table. "
    b"The page number indexes the page table to find the frame; the offset is added "
    b"to the frame base address. Virtual memory and paging are core operating system "
    b"concepts that let each process believe it has contiguous memory. " * 10
)


# --- tests -----------------------------------------------------------------

def test_grounded_answer_has_citation(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    _upload_and_index(instr, course["id"], "Week7-VirtualMemory.txt", OS_TEXT)
    student, _ = _approved_student(instr, sender, course)

    resp = student.post(
        f"/courses/{course['id']}/ask",
        json={"question": "How does paging translate a virtual address to a physical frame?"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["escalated"] is False
    assert body["flagged"] is False
    assert body["citation"] and "Week7-VirtualMemory.txt" in body["citation"]
    assert body["answer"]


def test_assignment_request_is_guided_not_completed(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    _upload_and_index(instr, course["id"], "notes.txt", OS_TEXT)
    student, _ = _approved_student(instr, sender, course)

    resp = student.post(
        f"/courses/{course['id']}/ask",
        json={"question": "Just do my homework for me and give me the answer to question 3."},
    )
    body = resp.json()
    assert body["flagged"] is True  # recorded for the instructor
    assert body["escalated"] is False
    assert body["answer"] == ASSIGNMENT_GUIDANCE  # guidance, not a completed answer


def test_no_relevant_material_escalates_without_citation(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr, code="CS 999", name="Empty")  # no documents uploaded
    student, _ = _approved_student(instr, sender, course)

    resp = student.post(
        f"/courses/{course['id']}/ask",
        json={"question": "How does paging work?"},
    )
    body = resp.json()
    assert body["escalated"] is True
    assert body["citation"] is None  # never invent a source


def test_student_cannot_ask_in_unapproved_course(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course1 = _make_course(instr, code="CS 310", name="OS")
    course2 = _make_course(instr, code="CS 240", name="DS")
    student, _ = _approved_student(instr, sender, course1)

    # Approved in course1, not enrolled in course2 → blocked (course-scoped access, NFR-5).
    blocked = student.post(f"/courses/{course2['id']}/ask", json={"question": "hi"})
    assert blocked.status_code == 403


def test_pending_student_blocked(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student_email = _email()
    student = _login(sender, student_email)
    student.post("/courses/enroll", json={"join_code": course["join_code"]})  # pending, not approved

    resp = student.post(f"/courses/{course['id']}/ask", json={"question": "hi"})
    assert resp.status_code == 403


def test_history_round_trips(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    _upload_and_index(instr, course["id"], "notes.txt", OS_TEXT)
    student, _ = _approved_student(instr, sender, course)

    student.post(f"/courses/{course['id']}/ask", json={"question": "What is paging?"})
    history = student.get(f"/courses/{course['id']}/messages").json()
    assert len(history) == 2  # the question + the AI answer
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "ai"


def test_escalations_surface_to_instructor(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr, code="CS 999", name="Empty")
    student, student_email = _approved_student(instr, sender, course)

    student.post(f"/courses/{course['id']}/ask", json={"question": "Totally unanswerable here?"})
    esc = instr.get(f"/courses/{course['id']}/escalations").json()
    assert len(esc) == 1
    assert esc[0]["student"] == student_email
    assert esc[0]["status"] == "needs"
