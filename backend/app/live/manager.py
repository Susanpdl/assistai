"""The realtime connection manager + Redis pub/sub relay.

Every WebSocket joins a **room** named by its session id. Messages are not sent to sockets
directly — they're **published to a Redis channel** for the room, and a single subscriber
loop (running on every server instance) delivers them to that instance's local sockets. That
indirection is what makes it scale-safe: a poll pushed on server A reaches students connected
to server B, because both instances subscribe to the same channel.

`connected_count` (the "X students connected" number) is the size of a Redis set of student
connection ids — shared across instances, so the count is correct no matter where students
land. Instructor connections aren't counted (the number means *students*).

Delivery is role-aware: a message may target `audience: "instructor"` (e.g. live tallies
before the instructor reveals them) or `"all"`. The filtering happens against each instance's
local sockets, so it works across instances without shipping roles through Redis.
"""

from __future__ import annotations

import asyncio
import json
import logging

from app.config import settings

logger = logging.getLogger("live.manager")

_CHANNEL_PREFIX = "assistai:rt:session:"
_CHANNEL_PATTERN = "assistai:rt:session:*"
_CONN_PREFIX = "assistai:rt:conn:"


def channel(session_id: str) -> str:
    return f"{_CHANNEL_PREFIX}{session_id}"


def conn_key(session_id: str) -> str:
    return f"{_CONN_PREFIX}{session_id}"


class ConnectionManager:
    def __init__(self) -> None:
        # session_id -> {websocket: role}
        self._rooms: dict[str, dict] = {}
        self._aredis = None
        self._task: asyncio.Task | None = None
        self._ready: asyncio.Event = asyncio.Event()

    async def _redis(self):
        if self._aredis is None:
            import redis.asyncio as aioredis

            self._aredis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._aredis

    # --- room membership ---------------------------------------------------

    async def join(self, session_id: str, ws, role: str, conn_id: str) -> None:
        self._rooms.setdefault(session_id, {})[ws] = role
        if role == "student":
            r = await self._redis()
            await r.sadd(conn_key(session_id), conn_id)

    async def leave(self, session_id: str, ws, role: str, conn_id: str) -> None:
        room = self._rooms.get(session_id)
        if room is not None:
            room.pop(ws, None)
            if not room:
                self._rooms.pop(session_id, None)
        if role == "student":
            r = await self._redis()
            await r.srem(conn_key(session_id), conn_id)

    async def connected_count(self, session_id: str) -> int:
        r = await self._redis()
        return int(await r.scard(conn_key(session_id)))

    async def clear_room(self, session_id: str) -> None:
        r = await self._redis()
        await r.delete(conn_key(session_id))

    # --- publish / deliver -------------------------------------------------

    async def publish(self, session_id: str, message: dict) -> None:
        r = await self._redis()
        await r.publish(channel(session_id), json.dumps(message))

    async def _deliver_local(self, session_id: str, message: dict) -> None:
        room = self._rooms.get(session_id)
        if not room:
            return
        audience = message.get("audience", "all")
        dead = []
        for ws, role in list(room.items()):
            if audience != "all" and role != audience:
                continue
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001 — a dead socket shouldn't block the room
                dead.append(ws)
        for ws in dead:
            room.pop(ws, None)

    # --- subscriber loop (one per process) ---------------------------------

    def start(self) -> None:
        if self._task is None:
            self._ready = asyncio.Event()
            self._task = asyncio.create_task(self._run_subscriber())

    async def wait_ready(self, timeout: float = 5.0) -> None:
        """Block until the subscriber has psubscribed (so no early publish is missed)."""
        await asyncio.wait_for(self._ready.wait(), timeout=timeout)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._ready.clear()
        if self._aredis is not None:
            await self._aredis.aclose()
            self._aredis = None

    async def _run_subscriber(self) -> None:
        r = await self._redis()
        pubsub = r.pubsub()
        await pubsub.psubscribe(_CHANNEL_PATTERN)
        self._ready.set()
        logger.info("Realtime subscriber listening on %s", _CHANNEL_PATTERN)
        try:
            async for msg in pubsub.listen():
                if msg.get("type") != "pmessage":
                    continue
                ch = msg["channel"]
                session_id = ch.rsplit(":", 1)[-1]
                try:
                    payload = json.loads(msg["data"])
                except (ValueError, TypeError):
                    continue
                await self._deliver_local(session_id, payload)
        except asyncio.CancelledError:
            await pubsub.aclose()
            raise


# One manager per process.
manager = ConnectionManager()


def publish_sync(session_id: str, message: dict) -> None:
    """Publish from synchronous code (HTTP handlers) using the sync Redis client.

    The async subscriber on every instance picks it up and delivers — so REST actions like
    'push poll' / 'reveal' / 'end session' fan out to the WebSocket rooms.
    """
    from app.redis_client import redis_client

    redis_client.publish(channel(session_id), json.dumps(message))
