"""Batched announcement email send.

Runs out of band (FastAPI background task) so posting an announcement returns immediately even
for a big class. Each recipient is retried once on a transient failure, and a final failure is
logged rather than dropped silently or allowed to block the rest of the class.
"""

from __future__ import annotations

import logging

from app.auth.email import EmailSender, send_announcement

logger = logging.getLogger("assistai.announcements")


def _send_one(sender: EmailSender, to: str, course_name: str, text: str, attempts: int = 2) -> bool:
    for i in range(attempts):
        try:
            send_announcement(sender, to=to, course_name=course_name, text=text)
            return True
        except Exception as exc:  # noqa: BLE001 — keep going; one bad address shouldn't stop the class
            if i == attempts - 1:
                logger.error("Announcement email to %s failed after %d attempts: %s", to, attempts, exc)
    return False


def send_announcement_batch(
    sender: EmailSender, recipients: list[str], course_name: str, text: str
) -> int:
    """Email every recipient; returns how many sent successfully."""
    sent = sum(_send_one(sender, to, course_name, text) for to in recipients)
    logger.info("Announcement emailed to %d/%d recipients in %s", sent, len(recipients), course_name)
    return sent
