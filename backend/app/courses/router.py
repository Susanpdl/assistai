"""Course and enrollment endpoints.

Instructors create courses (and get a join code); students request to join by that code;
instructors approve/reject (which emails the student). An approved enrollment is the gate
for all course-scoped access.
"""

import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_role
from app.auth.email import EmailSender, get_email_sender, send_enrollment_decision
from app.courses.deps import get_owned_course, require_course_access
from app.courses.schemas import (
    CourseCreate,
    CourseOut,
    DecisionRequest,
    EnrollmentOut,
    EnrollRequest,
)
from app.db import get_db
from app.models.courses import Course, Enrollment
from app.models.enums import EnrollmentStatus, Role
from app.models.identity import User

router = APIRouter(tags=["courses"])

# Unambiguous alphabet (no 0/O/1/I) for human-typed join codes.
_JOIN_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_join_code(db: Session) -> str:
    for _ in range(10):
        code = "".join(secrets.choice(_JOIN_ALPHABET) for _ in range(6))
        if db.execute(select(Course).where(Course.join_code == code)).scalar_one_or_none() is None:
            return code
    raise HTTPException(status_code=500, detail="Could not allocate a join code")


def _course_out(course: Course, *, is_owner: bool) -> CourseOut:
    return CourseOut(
        id=course.id,
        code=course.code,
        name=course.name,
        join_code=course.join_code if is_owner else None,
        is_owner=is_owner,
    )


def _enrollment_out(enr: Enrollment, *, with_student: User | None = None) -> EnrollmentOut:
    return EnrollmentOut(
        id=enr.id,
        course_id=enr.course_id,
        status=enr.status,
        requested_at=enr.created_at,
        decided_at=enr.decided_at,
        student=with_student,
    )


@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    user: User = Depends(require_role(Role.instructor)),
    db: Session = Depends(get_db),
) -> CourseOut:
    course = Course(
        code=payload.code,
        name=payload.name,
        join_code=_generate_join_code(db),
        owner_id=user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return _course_out(course, is_owner=True)


@router.get("/courses", response_model=list[CourseOut])
def list_courses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CourseOut]:
    if user.role == Role.instructor:
        owned = db.execute(select(Course).where(Course.owner_id == user.id)).scalars().all()
        return [_course_out(c, is_owner=True) for c in owned]
    # Student: only courses they're approved for.
    rows = db.execute(
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(
            Enrollment.student_id == user.id,
            Enrollment.status == EnrollmentStatus.approved,
        )
    ).scalars().all()
    return [_course_out(c, is_owner=False) for c in rows]


@router.post("/courses/enroll", response_model=EnrollmentOut)
def enroll(
    payload: EnrollRequest,
    user: User = Depends(require_role(Role.student)),
    db: Session = Depends(get_db),
) -> EnrollmentOut:
    course = db.execute(
        select(Course).where(Course.join_code == payload.join_code.strip().upper())
    ).scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No course for that code")

    existing = db.execute(
        select(Enrollment).where(
            Enrollment.course_id == course.id, Enrollment.student_id == user.id
        )
    ).scalar_one_or_none()

    if existing is not None:
        if existing.status == EnrollmentStatus.rejected:
            # Re-request: flip the rejected row back to pending instead of inserting a dup.
            existing.status = EnrollmentStatus.pending
            existing.decided_at = None
            db.commit()
            db.refresh(existing)
        return _enrollment_out(existing)

    enr = Enrollment(course_id=course.id, student_id=user.id, status=EnrollmentStatus.pending)
    db.add(enr)
    db.commit()
    db.refresh(enr)
    return _enrollment_out(enr)


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(
    course: Course = Depends(require_course_access),
    user: User = Depends(get_current_user),
) -> CourseOut:
    return _course_out(course, is_owner=course.owner_id == user.id)


@router.get("/courses/{course_id}/enrollments", response_model=list[EnrollmentOut])
def list_enrollments(
    status_filter: EnrollmentStatus | None = None,
    course: Course = Depends(get_owned_course),
    db: Session = Depends(get_db),
) -> list[EnrollmentOut]:
    stmt = select(Enrollment, User).join(User, User.id == Enrollment.student_id).where(
        Enrollment.course_id == course.id
    )
    if status_filter is not None:
        stmt = stmt.where(Enrollment.status == status_filter)
    return [_enrollment_out(enr, with_student=student) for enr, student in db.execute(stmt).all()]


@router.post("/enrollments/{enrollment_id}/decision", response_model=EnrollmentOut)
def decide_enrollment(
    enrollment_id: uuid.UUID,
    payload: DecisionRequest,
    user: User = Depends(require_role(Role.instructor)),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
) -> EnrollmentOut:
    if payload.decision not in (EnrollmentStatus.approved, EnrollmentStatus.rejected):
        raise HTTPException(status_code=422, detail="Decision must be approved or rejected")

    enr = db.get(Enrollment, enrollment_id)
    if enr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    course = db.get(Course, enr.course_id)
    if course is None or course.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the course owner")

    enr.status = payload.decision
    enr.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(enr)

    student = db.get(User, enr.student_id)
    if student is not None:
        send_enrollment_decision(
            sender, to=student.email, course_name=course.name,
            approved=payload.decision == EnrollmentStatus.approved,
        )
    return _enrollment_out(enr, with_student=student)
