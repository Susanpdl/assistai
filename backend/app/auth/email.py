"""Email sending, behind a small interface so the provider is swappable.

Phase 1 ships two backends:
- `ConsoleEmailSender` (dev): logs the magic link to stdout — no API key, fully testable.
- `ResendEmailSender` (prod): posts to the Resend API when EMAIL_BACKEND=resend.

The router depends on `get_email_sender`, so tests can override it with a capturing fake.
"""

import logging
from typing import Protocol

import httpx

from app.config import settings

logger = logging.getLogger("assistai.email")


class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender:
    """Logs the email instead of sending it. Used in local dev and tests."""

    def send(self, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL (console) -> %s | %s\n%s", to, subject, body)
        print(f"\n--- EMAIL to {to} ---\n{subject}\n{body}\n--- end email ---\n")


class ResendEmailSender:
    """Sends real email via the Resend HTTP API."""

    def send(self, to: str, subject: str, body: str) -> None:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.email_from, "to": [to], "subject": subject, "text": body},
            timeout=10,
        )
        resp.raise_for_status()


def get_email_sender() -> EmailSender:
    if settings.email_backend == "resend":
        return ResendEmailSender()
    return ConsoleEmailSender()


def send_magic_link(sender: EmailSender, to: str, link: str) -> None:
    body = (
        "Click the link below to sign in to AssistAI. It expires in "
        f"{settings.token_ttl_minutes} minutes and can be used once:\n\n{link}\n\n"
        "If you didn't request this, you can ignore this email."
    )
    sender.send(to=to, subject="Your AssistAI sign-in link", body=body)


def send_announcement(sender: EmailSender, to: str, course_name: str, text: str) -> None:
    subject = f"[{course_name}] New announcement"
    body = (
        f"Your instructor posted an announcement in {course_name}:\n\n"
        f"{text}\n\n"
        "— AssistAI\n\n"
        f"You're receiving this because you're enrolled in {course_name}. "
        "To stop these emails, ask your instructor to remove you from the course."
    )
    sender.send(to=to, subject=subject, body=body)


def send_enrollment_decision(sender: EmailSender, to: str, course_name: str, approved: bool) -> None:
    if approved:
        subject = f"You're enrolled in {course_name}"
        body = f"Your request to join {course_name} was approved. You now have access in AssistAI."
    else:
        subject = f"Update on your {course_name} enrollment request"
        body = (
            f"Your request to join {course_name} was not approved. "
            "You can request again if you think this was a mistake."
        )
    sender.send(to=to, subject=subject, body=body)
