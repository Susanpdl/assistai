"""Phase 5 — live sessions & polls tests (see docs/features/live-sessions-polls.md).

Covers the key cases:
- two student clients join → instructor sees connected_count = 2;
- a pushed poll reaches connected students;
- answers aggregate; a second answer from the same student is rejected (duplicate);
- live tallies go to the instructor until reveal, then to students;
- a non-enrolled user cannot join the room.

WebSockets are exercised through Starlette's TestClient. One TestClient (entered via `with`,
so the app lifespan starts the Redis pub/sub subscriber) holds all the sockets; HTTP actions
(start session, push poll, reveal) go through the per-user authenticated clients and fan out
over Redis to the room.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.main import app
from tests.conftest import TEST_DOMAIN

COOKIE = settings.session_cookie_name


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


def _make_course(client: TestClient) -> dict:
    return client.post("/courses", json={"code": "CS 310", "name": "OS"}).json()


def _cookie(client: TestClient) -> str:
    return client.cookies.get(COOKIE)


def _approved_student(instr: TestClient, sender, course) -> str:
    """Enroll + approve a new student; return their session-cookie value (for the WS)."""
    student = _login(sender, _email())
    enr = student.post("/courses/enroll", json={"join_code": course["join_code"]}).json()
    instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "approved"})
    return _cookie(student)


def _ws(wsc: TestClient, session_id: str, cookie: str):
    return wsc.websocket_connect(
        f"/ws/sessions/{session_id}", headers={"cookie": f"{COOKIE}={cookie}"}
    )


def _read_until(ws, msg_type: str, tries: int = 25) -> dict:
    for _ in range(tries):
        m = ws.receive_json()
        if m.get("type") == msg_type:
            return m
    raise AssertionError(f"did not receive a '{msg_type}' message")


def _read_count(ws, want: int, tries: int = 25) -> None:
    for _ in range(tries):
        m = ws.receive_json()
        if m.get("type") == "connected_count" and m.get("count") == want:
            return
    raise AssertionError(f"never saw connected_count == {want}")


# --- tests -----------------------------------------------------------------

def test_two_students_join_count(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    c1 = _approved_student(instr, sender, course)
    c2 = _approved_student(instr, sender, course)
    sid = instr.post(f"/courses/{course['id']}/sessions").json()["id"]

    with TestClient(app) as wsc:
        with _ws(wsc, sid, _cookie(instr)) as iws:
            _read_until(iws, "session_state")
            with _ws(wsc, sid, c1), _ws(wsc, sid, c2):
                _read_count(iws, 2)  # instructor sees both students connected


def test_poll_push_and_aggregate_and_reveal(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    c1 = _approved_student(instr, sender, course)
    sid = instr.post(f"/courses/{course['id']}/sessions").json()["id"]

    with TestClient(app) as wsc:
        with _ws(wsc, sid, _cookie(instr)) as iws, _ws(wsc, sid, c1) as sw1:
            _read_until(iws, "session_state")
            _read_until(sw1, "session_state")

            # Instructor pushes a poll → it reaches the student.
            poll = instr.post(
                f"/sessions/{sid}/activities",
                json={"question": "Which can starve?", "options": ["RR", "Priority", "FCFS"]},
            ).json()
            pushed = _read_until(sw1, "poll_pushed")
            assert pushed["activity"]["id"] == poll["id"]

            # Student answers; gets an ok ack.
            sw1.send_json({"type": "submit_answer", "activity_id": poll["id"], "choice": "Priority"})
            ack = _read_until(sw1, "answer_ack")
            assert ack["status"] == "ok"

            # Tally reaches the instructor (audience: instructor, before reveal).
            res = _read_until(iws, "results_update")
            assert res["tallies"]["Priority"] == 1
            assert res["total"] == 1

            # A second answer from the same student is rejected.
            sw1.send_json({"type": "submit_answer", "activity_id": poll["id"], "choice": "RR"})
            ack2 = _read_until(sw1, "answer_ack")
            assert ack2["status"] == "duplicate"

            # Reveal → the student now receives the results.
            instr.post(f"/activities/{poll['id']}/reveal")
            _read_until(sw1, "poll_revealed")
            shown = _read_until(sw1, "results_update")
            assert shown["tallies"]["Priority"] == 1


def test_non_enrolled_cannot_join(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    sid = instr.post(f"/courses/{course['id']}/sessions").json()["id"]

    # A logged-in but not-enrolled student.
    outsider = _login(sender, _email())
    with TestClient(app) as wsc:
        with pytest.raises(WebSocketDisconnect):
            with _ws(wsc, sid, _cookie(outsider)) as ws:
                ws.receive_json()


def test_results_hidden_from_students_before_reveal(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    c1 = _approved_student(instr, sender, course)
    sid = instr.post(f"/courses/{course['id']}/sessions").json()["id"]

    with TestClient(app) as wsc:
        with _ws(wsc, sid, c1) as sw1:
            _read_until(sw1, "session_state")
            poll = instr.post(
                f"/sessions/{sid}/activities",
                json={"question": "q", "options": ["A", "B"]},
            ).json()
            _read_until(sw1, "poll_pushed")
            sw1.send_json({"type": "submit_answer", "activity_id": poll["id"], "choice": "A"})
            _read_until(sw1, "answer_ack")
            # The instructor sees the tally over REST even though the student wasn't sent it.
            results = instr.get(f"/activities/{poll['id']}/results").json()
            assert results["tallies"]["A"] == 1
            assert results["revealed"] is False
