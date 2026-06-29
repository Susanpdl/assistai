"""Announcement & comment endpoints (Phase 7).

Instructors post text announcements (which email every enrolled student in the background);
enrolled students read them newest-first and comment. The course owner can edit/delete an
announcement and moderate comments.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.announcements.notify import send_announcement_batch
from app.announcements.schemas import (
    AnnouncementCreate,
    AnnouncementOut,
    AnnouncementUpdate,
    CommentCreate,
    CommentOut,
)
from app.auth.deps import get_current_user
from app.auth.email import EmailSender, get_email_sender
from app.courses.deps import get_owned_course, require_course_access
from app.db import get_db
from app.models.announcements import Announcement, Comment
from app.models.courses import Course, Enrollment
from app.models.enums import EnrollmentStatus, Role
from app.models.identity import User

router = APIRouter(tags=["announcements"])


def _display(db: DbSession, user_id: uuid.UUID) -> tuple[str, str]:
    u = db.get(User, user_id)
    if u is None:
        return ("Unknown", "student")
    return (u.name or u.email, u.role.value)


def _comment_out(db: DbSession, c: Comment) -> CommentOut:
    name, role = _display(db, c.author_id)
    return CommentOut(id=c.id, author=name, author_role=role, text=c.text, created_at=c.created_at)


def _announcement_out(db: DbSession, a: Announcement, comments: list[Comment]) -> AnnouncementOut:
    name, _ = _display(db, a.author_id)
    return AnnouncementOut(
        id=a.id, author=name, text=a.text, created_at=a.created_at,
        comments=[_comment_out(db, c) for c in comments],
    )


def _course_has_access(db: DbSession, course: Course, user: User) -> bool:
    if course.owner_id == user.id:
        return True
    return db.execute(
        select(Enrollment).where(
            Enrollment.course_id == course.id,
            Enrollment.student_id == user.id,
            Enrollment.status == EnrollmentStatus.approved,
        )
    ).scalar_one_or_none() is not None


def _announcement_for_access(
    announcement_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> Announcement:
    a = db.get(Announcement, announcement_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    course = db.get(Course, a.course_id)
    if course is None or not _course_has_access(db, course, user):
        raise HTTPException(status_code=403, detail="No access to this course")
    return a


def _owned_announcement(
    announcement_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> Announcement:
    a = db.get(Announcement, announcement_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    course = db.get(Course, a.course_id)
    if course is None or course.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not the course owner")
    return a


@router.post(
    "/courses/{course_id}/announcements", response_model=AnnouncementOut, status_code=201
)
def post_announcement(
    payload: AnnouncementCreate,
    background_tasks: BackgroundTasks,
    course: Course = Depends(get_owned_course),
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
) -> AnnouncementOut:
    a = Announcement(course_id=course.id, author_id=user.id, text=payload.text)
    db.add(a)
    db.commit()
    db.refresh(a)

    # Email every approved student, out of band.
    recipients = list(
        db.execute(
            select(User.email)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(
                Enrollment.course_id == course.id,
                Enrollment.status == EnrollmentStatus.approved,
            )
        ).scalars().all()
    )
    background_tasks.add_task(send_announcement_batch, sender, recipients, course.name, payload.text)
    return _announcement_out(db, a, [])


@router.get("/courses/{course_id}/announcements", response_model=list[AnnouncementOut])
def list_announcements(
    course: Course = Depends(require_course_access),
    db: DbSession = Depends(get_db),
) -> list[AnnouncementOut]:
    anns = db.execute(
        select(Announcement)
        .where(Announcement.course_id == course.id)
        .order_by(Announcement.created_at.desc())
    ).scalars().all()
    out = []
    for a in anns:
        comments = db.execute(
            select(Comment)
            .where(Comment.announcement_id == a.id)
            .order_by(Comment.created_at)
        ).scalars().all()
        out.append(_announcement_out(db, a, comments))
    return out


@router.patch("/announcements/{announcement_id}", response_model=AnnouncementOut)
def edit_announcement(
    payload: AnnouncementUpdate,
    a: Announcement = Depends(_owned_announcement),
    db: DbSession = Depends(get_db),
) -> AnnouncementOut:
    a.text = payload.text
    db.commit()
    db.refresh(a)
    comments = db.execute(
        select(Comment).where(Comment.announcement_id == a.id).order_by(Comment.created_at)
    ).scalars().all()
    return _announcement_out(db, a, comments)


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    a: Announcement = Depends(_owned_announcement),
    db: DbSession = Depends(get_db),
) -> None:
    db.query(Comment).filter(Comment.announcement_id == a.id).delete(synchronize_session=False)
    db.delete(a)
    db.commit()


@router.post("/announcements/{announcement_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    payload: CommentCreate,
    a: Announcement = Depends(_announcement_for_access),
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> CommentOut:
    c = Comment(announcement_id=a.id, author_id=user.id, text=payload.text)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _comment_out(db, c)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> None:
    c = db.get(Comment, comment_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    a = db.get(Announcement, c.announcement_id)
    course = db.get(Course, a.course_id) if a else None
    is_owner = course is not None and course.owner_id == user.id
    # The comment's author may delete their own; the course owner may moderate any.
    if c.author_id != user.id and not (is_owner and user.role == Role.instructor):
        raise HTTPException(status_code=403, detail="Cannot delete this comment")
    db.delete(c)
    db.commit()
