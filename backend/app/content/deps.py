"""Authorization helper for document-level actions (delete, reindex).

Course-level actions (upload, list) reuse `get_owned_course` from the courses package; this
adds the document-id variant: load the document, then require the caller owns its course.
"""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db import get_db
from app.models.content import Document
from app.models.courses import Course
from app.models.identity import User


def get_owned_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    course = db.get(Course, doc.course_id)
    if course is None or course.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the course owner")
    return doc
