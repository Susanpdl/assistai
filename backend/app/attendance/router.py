"""Attendance endpoints (Phase 6).

Instructor displays a rotating code and watches the live roster; students check in by entering
the current code from their own device. Present = valid code (+ a poll answer if a poll ran).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from app.attendance import codes, service
from app.attendance.schemas import (
    AttendanceListOut,
    AttendanceRowOut,
    CheckinRequest,
    CheckinResponse,
    CodeOut,
)
from app.auth.deps import get_current_user
from app.db import get_db
from app.live.service import resolve_role
from app.models.enums import AttendanceStatus
from app.models.identity import User
from app.models.sessions import Session

router = APIRouter(tags=["attendance"])

_ERROR_STATUS = {"not_live": 409, "bad_code": 422, "device_taken": 409}


def _require_instructor_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> Session:
    s = db.get(Session, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if resolve_role(db, s, user) != "instructor":
        raise HTTPException(status_code=403, detail="Not the course owner")
    return s


def _require_student_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> Session:
    s = db.get(Session, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if resolve_role(db, s, user) != "student":
        raise HTTPException(status_code=403, detail="No access to this session")
    return s


@router.get("/sessions/{session_id}/attendance/code", response_model=CodeOut)
def get_code(session: Session = Depends(_require_instructor_session)) -> CodeOut:
    return CodeOut(
        code=codes.current_code(str(session.id)),
        expires_in_seconds=codes.seconds_remaining(),
    )


@router.post("/sessions/{session_id}/attendance/checkin", response_model=CheckinResponse)
def checkin(
    payload: CheckinRequest,
    session: Session = Depends(_require_student_session),
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> CheckinResponse:
    result = service.checkin(db, session, user.id, payload.code.strip(), payload.device_id.strip())
    if not result.ok:
        detail = {
            "not_live": "Session is not live",
            "bad_code": "Invalid or expired code",
            "device_taken": "This device already checked in another account",
        }[result.error]
        raise HTTPException(status_code=_ERROR_STATUS[result.error], detail=detail)
    return CheckinResponse(
        status=result.status,
        proofs=result.proofs,
        present=result.status == AttendanceStatus.present,
        needs_poll=result.needs_poll,
    )


@router.get("/sessions/{session_id}/attendance", response_model=AttendanceListOut)
def list_attendance(
    session: Session = Depends(_require_instructor_session),
    db: DbSession = Depends(get_db),
) -> AttendanceListOut:
    rows = service.roster(db, session)
    out = [
        AttendanceRowOut(
            student=r.student,
            status=r.status,
            proofs=r.proofs,
            checked_in=r.checked_in,
            checked_in_at=r.checked_in_at,
        )
        for r in rows
    ]
    present = sum(1 for r in rows if r.status == AttendanceStatus.present)
    return AttendanceListOut(present=present, total=len(rows), rows=out)
