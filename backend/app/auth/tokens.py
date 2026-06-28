"""Magic-link token creation and verification.

A token is a long random string we email to the user. We persist only its SHA-256 hash
(see `LoginToken`). Verification re-hashes the incoming token and looks the hash up.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth import LoginToken


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_login_token(db: Session, email: str) -> str:
    """Create and store a token for `email`, returning the RAW token (to email out)."""
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.token_ttl_minutes)
    db.add(LoginToken(token_hash=_hash(raw_token), email=email.lower(), expires_at=expires_at))
    db.commit()
    return raw_token


def consume_login_token(db: Session, raw_token: str) -> str | None:
    """Validate and single-use-consume a token. Returns the email on success, else None.

    Fails (returns None) if the token is unknown, already used, or expired.
    """
    row = db.execute(
        select(LoginToken).where(LoginToken.token_hash == _hash(raw_token))
    ).scalar_one_or_none()
    if row is None or row.used_at is not None:
        return None
    # `expires_at` comes back timezone-aware from Postgres; compare in UTC.
    if row.expires_at <= datetime.now(timezone.utc):
        return None
    row.used_at = datetime.now(timezone.utc)
    db.commit()
    return row.email
