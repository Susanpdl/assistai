"""Phase 7 — announcements & email notification tests (see docs/features/announcements.md).

Covers: posting emails every approved student (background task); non-enrolled users can't
read/comment; comments appear under the right announcement; the owner can edit/delete and
moderate comments; a transient email failure is retried (not dropped).

The `sender` fixture is the capturing fake email sender (also used by magic-link login), so we
clear it before asserting on announcement emails.
"""

import uuid

from fastapi.testclient import TestClient

from app.auth.email import get_email_sender
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
    return client.post("/courses", json={"code": "CS 310", "name": "OS"}).json()


def _approved_student(instr: TestClient, sender, course) -> tuple[TestClient, str]:
    email = _email()
    student = _login(sender, email)
    enr = student.post("/courses/enroll", json={"join_code": course["join_code"]}).json()
    instr.post(f"/enrollments/{enr['id']}/decision", json={"decision": "approved"})
    return student, email


# --- tests -----------------------------------------------------------------

def test_post_emails_each_enrolled_student(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    _, e1 = _approved_student(instr, sender, course)
    _, e2 = _approved_student(instr, sender, course)

    sender.sent.clear()  # drop the magic-link / enrollment emails from setup
    resp = instr.post(
        f"/courses/{course['id']}/announcements", json={"text": "Midterm moved to Friday."}
    )
    assert resp.status_code == 201, resp.text
    # One announcement email per approved student (background task ran).
    recipients = {m["to"] for m in sender.sent}
    assert recipients == {e1, e2}
    assert all("announcement" in m["subject"].lower() for m in sender.sent)


def test_non_enrolled_cannot_read_or_comment(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    ann = instr.post(f"/courses/{course['id']}/announcements", json={"text": "Hi class"}).json()

    outsider = _login(sender, _email())
    assert outsider.get(f"/courses/{course['id']}/announcements").status_code == 403
    assert outsider.post(f"/announcements/{ann['id']}/comments", json={"text": "hey"}).status_code == 403


def test_comment_appears_under_announcement(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    student, _ = _approved_student(instr, sender, course)
    ann = instr.post(f"/courses/{course['id']}/announcements", json={"text": "Readings posted"}).json()

    c = student.post(f"/announcements/{ann['id']}/comments", json={"text": "Thanks!"})
    assert c.status_code == 201

    feed = student.get(f"/courses/{course['id']}/announcements").json()
    assert len(feed) == 1
    assert len(feed[0]["comments"]) == 1
    assert feed[0]["comments"][0]["text"] == "Thanks!"


def test_owner_can_edit_and_delete(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    ann = instr.post(f"/courses/{course['id']}/announcements", json={"text": "v1"}).json()

    edited = instr.patch(f"/announcements/{ann['id']}", json={"text": "v2 corrected"})
    assert edited.status_code == 200
    assert edited.json()["text"] == "v2 corrected"

    assert instr.delete(f"/announcements/{ann['id']}").status_code == 204
    assert instr.get(f"/courses/{course['id']}/announcements").json() == []


def test_comment_moderation(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    s1, _ = _approved_student(instr, sender, course)
    s2, _ = _approved_student(instr, sender, course)
    ann = instr.post(f"/courses/{course['id']}/announcements", json={"text": "post"}).json()
    comment = s1.post(f"/announcements/{ann['id']}/comments", json={"text": "mine"}).json()

    # Another student can't delete someone else's comment.
    assert s2.delete(f"/comments/{comment['id']}").status_code == 403
    # The instructor (course owner) can moderate it.
    assert instr.delete(f"/comments/{comment['id']}").status_code == 204


def test_email_retried_on_transient_failure(monkeypatch, sender):
    instr = _instructor(monkeypatch, sender)
    course = _make_course(instr)
    _approved_student(instr, sender, course)

    class FlakySender:
        def __init__(self):
            self.calls = 0
            self.sent = []

        def send(self, to, subject, body):
            self.calls += 1
            if self.calls == 1:  # first attempt fails transiently
                raise RuntimeError("transient")
            self.sent.append({"to": to})

    flaky = FlakySender()
    app.dependency_overrides[get_email_sender] = lambda: flaky
    try:
        resp = instr.post(f"/courses/{course['id']}/announcements", json={"text": "retry me"})
        assert resp.status_code == 201
        # One recipient; first send raised, the retry succeeded.
        assert flaky.calls == 2
        assert len(flaky.sent) == 1
    finally:
        app.dependency_overrides[get_email_sender] = lambda: sender
