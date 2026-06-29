"""The session WebSocket endpoint.

A browser opens `/ws/sessions/{id}`; we authenticate from the session cookie, check the user
has access to the session's course, then join them to the room. Students send `submit_answer`;
the server records it and broadcasts updated tallies (to the instructor until they reveal).
Poll pushes, reveals, and session-end are published by the HTTP endpoints and delivered here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.sessions import get_session_user_id
from app.config import settings
from app.db import SessionLocal
from app.live import service
from app.live.manager import manager
from app.models.enums import SessionStatus
from app.models.identity import User
from app.models.sessions import Activity, Session

router = APIRouter(tags=["live-ws"])


@dataclass
class WsContext:
    user_id: uuid.UUID
    session_id: uuid.UUID
    role: str  # "instructor" | "student"
    status: SessionStatus


def _authenticate(websocket: WebSocket, session_id: str) -> WsContext | None:
    cookie = websocket.cookies.get(settings.session_cookie_name)
    user_id = get_session_user_id(cookie) if cookie else None
    if not user_id:
        return None
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return None
    db = SessionLocal()
    try:
        user = db.get(User, uuid.UUID(user_id))
        session = db.get(Session, sid)
        if user is None or session is None:
            return None
        role = service.resolve_role(db, session, user)
        if role is None:
            return None
        return WsContext(user_id=user.id, session_id=sid, role=role, status=session.status)
    finally:
        db.close()


@router.websocket("/ws/sessions/{session_id}")
async def session_ws(websocket: WebSocket, session_id: str) -> None:
    ctx = _authenticate(websocket, session_id)
    if ctx is None:
        await websocket.close(code=4403)  # policy violation: no access
        return

    conn_id = uuid.uuid4().hex
    await websocket.accept()
    await manager.join(session_id, websocket, ctx.role, conn_id)
    try:
        count = await manager.connected_count(session_id)
        await websocket.send_json(service.session_state_msg(ctx.status.value, count))
        await manager.publish(session_id, service.connected_count_msg(count))

        while True:
            data = await websocket.receive_json()
            if data.get("type") == "submit_answer" and ctx.role == "student":
                await _handle_answer(websocket, session_id, ctx, data)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.leave(session_id, websocket, ctx.role, conn_id)
        count = await manager.connected_count(session_id)
        await manager.publish(session_id, service.connected_count_msg(count))


async def _handle_answer(websocket: WebSocket, session_id: str, ctx: WsContext, data: dict) -> None:
    activity_id = data.get("activity_id")
    choice = data.get("choice")
    if not activity_id or choice is None:
        return
    db = SessionLocal()
    try:
        activity = db.get(Activity, uuid.UUID(str(activity_id)))
        if activity is None or activity.session_id != ctx.session_id:
            return
        result = service.record_answer(db, activity, ctx.user_id, choice)
        # Ack only the student who submitted (direct send, not a room broadcast).
        await websocket.send_json(
            {"type": "answer_ack", "activity_id": str(activity.id), "status": result}
        )
        if result != "ok":
            return
        tallies, total = service.tally(db, activity)
        # Tallies go to the instructor until they reveal them to the class.
        audience = "all" if activity.revealed else "instructor"
        await manager.publish(
            session_id, service.results_update_msg(activity.id, tallies, total, audience=audience)
        )
    finally:
        db.close()
