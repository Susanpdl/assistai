"""Course content endpoints (Phase 3).

Instructors upload course files; each upload is stored and queued for the ingestion worker,
returning immediately with status `processing`. The worker (out of band) extracts, chunks,
embeds, and flips the status to `indexed` (or `failed`).
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.auth.deps import require_role
from app.config import settings
from app.content.deps import get_owned_document
from app.content.schemas import DocumentOut
from app.courses.deps import get_owned_course
from app.db import get_db
from app.ingestion.queue import enqueue
from app.models.content import Chunk, Document
from app.models.courses import Course
from app.models.enums import DocumentStatus, Role
from app.models.identity import User
from app.storage import Storage, get_storage

router = APIRouter(tags=["content"])


def _document_out(db: Session, doc: Document) -> DocumentOut:
    count = db.execute(
        select(func.count()).select_from(Chunk).where(Chunk.document_id == doc.id)
    ).scalar_one()
    return DocumentOut(
        id=doc.id,
        course_id=doc.course_id,
        filename=doc.filename,
        type=doc.type,
        status=doc.status,
        chunk_count=count,
        error=doc.error,
        uploaded_at=doc.created_at,
    )


def _validate_upload(filename: str, data: bytes) -> str:
    """Return the normalized extension, or raise 4xx if the file isn't acceptable."""
    if "." not in filename:
        raise HTTPException(status_code=422, detail="File has no extension")
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in settings.allowed_extension_set:
        allowed = ", ".join(sorted(settings.allowed_extension_set))
        raise HTTPException(status_code=422, detail=f"Unsupported file type. Allowed: {allowed}")
    if len(data) == 0:
        raise HTTPException(status_code=422, detail="File is empty")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit"
        )
    return ext


@router.post(
    "/courses/{course_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    course: Course = Depends(get_owned_course),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: Storage = Depends(get_storage),
) -> DocumentOut:
    data = await file.read()
    ext = _validate_upload(file.filename or "", data)

    # Generate the id up front so the storage key is known before we commit.
    doc_id = uuid.uuid4()
    storage_key = storage.put(f"{course.id}/{doc_id}.{ext}", data)

    doc = Document(
        id=doc_id,
        course_id=course.id,
        filename=file.filename,
        type=ext,
        status=DocumentStatus.processing,
        storage_key=storage_key,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Hand off to the worker; the request returns immediately.
    enqueue(doc.id)
    return _document_out(db, doc)


@router.get("/courses/{course_id}/documents", response_model=list[DocumentOut])
def list_documents(
    course: Course = Depends(get_owned_course),
    db: Session = Depends(get_db),
) -> list[DocumentOut]:
    docs = db.execute(
        select(Document)
        .where(Document.course_id == course.id)
        .order_by(Document.created_at.desc())
    ).scalars().all()
    return [_document_out(db, d) for d in docs]


@router.post("/documents/{document_id}/reindex", response_model=DocumentOut)
def reindex_document(
    doc: Document = Depends(get_owned_document),
    _user: User = Depends(require_role(Role.instructor)),
    db: Session = Depends(get_db),
) -> DocumentOut:
    """Re-queue a document (e.g. retry after `failed`, or after the file was replaced)."""
    doc.status = DocumentStatus.processing
    doc.error = None
    db.commit()
    db.refresh(doc)
    enqueue(doc.id)
    return _document_out(db, doc)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
    storage: Storage = Depends(get_storage),
) -> None:
    if doc.storage_key:
        storage.delete(doc.storage_key)
    db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
    db.delete(doc)
    db.commit()
