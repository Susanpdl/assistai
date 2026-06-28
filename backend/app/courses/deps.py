"""Authorization helpers for courses.

- `require_course_access` — the gate every course-scoped feature reuses: the owner, or a
  student with an *approved* enrollment, may proceed; anyone else gets 403/404.
- `get_owned_course` — for instructor-only actions on a course they must own.
"""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db import get_db
from app.models.courses import Course, Enrollment
from app.models.enums import EnrollmentStatus
from app.models.identity import User


def _get_course_or_404(db: Session, course_id: uuid.UUID) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def require_course_access(
    course_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Course:
    course = _get_course_or_404(db, course_id)
    if course.owner_id == user.id:
        return course
    approved = db.execute(
        select(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == user.id,
            Enrollment.status == EnrollmentStatus.approved,
        )
    ).scalar_one_or_none()
    if approved is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this course")
    return course


def get_owned_course(
    course_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Course:
    course = _get_course_or_404(db, course_id)
    if course.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the course owner")
    return course
