"""A single shared Redis client.

Redis backs two things in Phase 1: the session store and the rate limiter. One client
(connection pool) is reused across the app. `decode_responses=True` means we get back
`str` instead of `bytes`, which is what we want for ids and counters.
"""

import redis

from app.config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
