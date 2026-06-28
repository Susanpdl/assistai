"""Server-side sessions, stored in Redis.

A session is just an opaque random id (the cookie value) mapped to a user id, with a
TTL. Because the server holds the mapping, logout is a real delete — unlike a stateless
JWT, there's nothing still-valid floating around after we remove the key.
"""

import secrets

from app.config import settings
from app.redis_client import redis_client

_SESSION_PREFIX = "session:"


def _key(session_id: str) -> str:
    return f"{_SESSION_PREFIX}{session_id}"


def create_session(user_id: str) -> str:
    """Create a session for `user_id`, returning the session id (cookie value)."""
    session_id = secrets.token_urlsafe(32)
    ttl = settings.session_ttl_days * 24 * 60 * 60
    redis_client.set(_key(session_id), user_id, ex=ttl)
    return session_id


def get_session_user_id(session_id: str) -> str | None:
    """Return the user id for a session id, or None if missing/expired."""
    if not session_id:
        return None
    return redis_client.get(_key(session_id))


def delete_session(session_id: str) -> None:
    if session_id:
        redis_client.delete(_key(session_id))
