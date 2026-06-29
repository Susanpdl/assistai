"""A tiny Redis-list job queue for ingestion.

The upload endpoint pushes a document id; the worker pops ids to process. A Redis list is
enough here — one durable queue the web request doesn't have to wait on. (If we ever need
retries/visibility timeouts we'd reach for a real broker.)

We poll with non-blocking RPOP rather than a blocking BRPOP: blocking pops make the client
socket read deadline race with the command's own timeout (redis-py raises a socket
TimeoutError instead of returning nil), which is fiddly to get right. A short poll is simpler
and plenty responsive for ingestion.
"""

from __future__ import annotations

import time
import uuid

from app.config import settings
from app.redis_client import redis_client

_POLL_INTERVAL = 0.2  # seconds between RPOP attempts while the queue is empty


def enqueue(document_id: uuid.UUID) -> None:
    """Add a document to the ingestion queue (left push)."""
    redis_client.lpush(settings.ingest_queue_key, str(document_id))


def dequeue(timeout: float = 5) -> uuid.UUID | None:
    """Pop the next document id, waiting up to `timeout` seconds. None if none arrives."""
    deadline = time.monotonic() + timeout
    while True:
        item = redis_client.rpop(settings.ingest_queue_key)
        if item is not None:
            # decode_responses=True → item is already a str.
            return uuid.UUID(item)
        if time.monotonic() >= deadline:
            return None
        time.sleep(_POLL_INTERVAL)


def queue_length() -> int:
    return redis_client.llen(settings.ingest_queue_key)
