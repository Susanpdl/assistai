"""The rotating check-in code.

The code shown on the instructor's screen regenerates every few seconds. It's derived
deterministically from `(session_id, time_window)` via HMAC — so any server instance computes
the same code with no shared state, and an old screenshot goes stale within one window. A small
grace (the previous window also validates) covers the seconds it takes a student to type it.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from app.config import settings


def _window(now: float | None = None) -> int:
    return int((now if now is not None else time.time()) // settings.attendance_code_interval_seconds)


def _code_for(session_id: str, window: int) -> str:
    msg = f"{session_id}:{window}".encode()
    digest = hmac.new(settings.attendance_code_secret.encode(), msg, hashlib.sha256).digest()
    return f"{int.from_bytes(digest[:4], 'big') % 1_000_000:06d}"


def current_code(session_id: str) -> str:
    return _code_for(session_id, _window())


def seconds_remaining(now: float | None = None) -> int:
    interval = settings.attendance_code_interval_seconds
    elapsed = int(now if now is not None else time.time()) % interval
    return interval - elapsed


def is_valid(session_id: str, code: str) -> bool:
    """True if `code` is the current code or within the grace window(s)."""
    w = _window()
    for i in range(settings.attendance_code_grace_windows + 1):
        if hmac.compare_digest(code, _code_for(session_id, w - i)):
            return True
    return False
