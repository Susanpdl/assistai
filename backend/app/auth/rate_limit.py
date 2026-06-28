"""A tiny fixed-window rate limiter backed by Redis.

We INCR a counter keyed by what we're limiting (e.g. an email or IP) and put a TTL on it
the first time. When the count exceeds the limit within the window, we reject. Fixed-window
is simple and good enough to stop magic-link inbox spam.
"""

from app.config import settings
from app.redis_client import redis_client


def too_many_requests(scope: str, identifier: str) -> bool:
    """Return True if `identifier` has exceeded the limit for `scope` this window."""
    key = f"ratelimit:{scope}:{identifier}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, settings.auth_request_window_minutes * 60)
    return count > settings.auth_request_max_per_window
