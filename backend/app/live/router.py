"""Live-session & poll HTTP endpoints (Phase 5).

Instructors start/end sessions and push/reveal polls over REST; each action publishes a
realtime message (via Redis) that the WebSocket rooms deliver. Students answer over the
WebSocket (see ws.py).
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.auth.deps import get_current_user
from app.courses.deps import get_owned_course, require_course_access
from app.db import get_db
from app.live import service
from app.live.manager import conn_key, publish_sync
from app.live.schemas import ActivityOut, PollCreate, ResultsOut, SessionOut
from app.models.courses import Course
from app.models.enums import ActivityType, SessionStatus
from app.models.identity import User
from app.models.sessions import Activity, Session
from app.redis_client import redis_client

router = APIRouter(tags=["live"])


def _session_out(s: Session) -> SessionOut:
    return SessionOut(
        id=s.id, course_id=s.course_id, status=s.status,
        started_at=s.started_at, ended_at=s.ended_at,
    )


def _activity_out(a: Activity) -> ActivityOut:
    return ActivityOut(
        id=a.id, session_id=a.session_id, question=a.question,
        options=list(a.options), correct_option=a.correct_option, revealed=a.revealed,
    )


def _owned_session(db: DbSession, session_id: uuid.UUID, user: User) -> Session:
    s = db.get(Session, session_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    course = db.get(Course, s.course_id)
    if course is None or course.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the course owner")
    return s


def _owned_activity(db: DbSession, activity_id: uuid.UUID, user: User) -> Activity:
    a = db.get(Activity, activity_id)
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    _owned_session(db, a.session_id, user)
    return a


@router.post("/courses/{course_id}/sessions", response_model=SessionOut, status_code=201)
def start_session(
    course: Course = Depends(get_owned_course),
    db: DbSession = Depends(get_db),
) -> SessionOut:
    s = Session(
        course_id=course.id,
        status=SessionStatus.live,
        started_at=datetime.now(timezone.utc),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _session_out(s)


@router.get("/courses/{course_id}/sessions/active", response_model=SessionOut | None)
def active_session(
    course: Course = Depends(require_course_access),
    db: DbSession = Depends(get_db),
) -> SessionOut | None:
    """The course's current live session (if any) — students poll this to know class is live."""
    s = db.execute(
        select(Session)
        .where(Session.course_id == course.id, Session.status == SessionStatus.live)
        .order_by(Session.started_at.desc())
    ).scalars().first()
    return _session_out(s) if s else None


@router.post("/sessions/{session_id}/end", response_model=SessionOut)
def end_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> SessionOut:
    s = _owned_session(db, session_id, user)
    s.status = SessionStatus.ended
    s.ended_at = datetime.now(timezone.utc)
    db.commit()
    # Lock in final attendance (present/absent) now that we know if a poll ran and who answered.
    from app.attendance.service import finalize

    finalize(db, s)
    db.refresh(s)
    publish_sync(str(session_id), service.session_ended_msg())
    redis_client.delete(conn_key(str(session_id)))
    return _session_out(s)


@router.post("/sessions/{session_id}/activities", response_model=ActivityOut, status_code=201)
def push_poll(
    session_id: uuid.UUID,
    payload: PollCreate,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> ActivityOut:
    s = _owned_session(db, session_id, user)
    if s.status != SessionStatus.live:
        raise HTTPException(status_code=409, detail="Session is not live")
    if len(payload.options) < 2:
        raise HTTPException(status_code=422, detail="A poll needs at least two options")
    if payload.correct_option is not None and payload.correct_option not in payload.options:
        raise HTTPException(status_code=422, detail="correct_option must be one of the options")
    activity = Activity(
        session_id=s.id, type=ActivityType.poll,
        question=payload.question, options=payload.options,
        correct_option=payload.correct_option, revealed=False,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    publish_sync(str(session_id), service.poll_pushed_msg(activity))
    return _activity_out(activity)


@router.post("/activities/{activity_id}/reveal", response_model=ActivityOut)
def reveal_poll(
    activity_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> ActivityOut:
    activity = _owned_activity(db, activity_id, user)
    activity.revealed = True
    db.commit()
    db.refresh(activity)
    tallies, total = service.tally(db, activity)
    publish_sync(
        str(activity.session_id),
        service.poll_revealed_msg(activity.id, activity.correct_option),
    )
    publish_sync(
        str(activity.session_id),
        service.results_update_msg(activity.id, tallies, total, audience="all"),
    )
    return _activity_out(activity)


@router.get("/activities/{activity_id}/results", response_model=ResultsOut)
def poll_results(
    activity_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> ResultsOut:
    activity = _owned_activity(db, activity_id, user)
    tallies, total = service.tally(db, activity)
    return ResultsOut(
        activity_id=activity.id, tallies=tallies, total=total, revealed=activity.revealed
    )
