# Course Content & Ingestion — Test Log

One entry per test run. See [`../features/content-ingestion.md`](../features/content-ingestion.md).

---

### Content & ingestion — test run 2026-06-24

Automated suite: `cd backend && uv run pytest` (26 passed total; 9 new for this feature),
integration tests against the docker-compose Postgres + Redis. The pipeline is exercised
end to end: upload via the API → real Redis queue → `process_document` (extract → chunk →
embed → store) → pgvector. The dev/test embedder is the deterministic offline `LocalEmbedder`
(no API key); the real model is a Phase-4 decision.

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-C1 | Integration | Instructor uploads `.txt` | 201, status `processing`, `chunk_count` 0, returns immediately | ✅ |
| T-2 | FR-C1 | Integration | Upload pushes the document id to the Redis queue | id popped off queue matches | ✅ |
| T-3 | FR-C2 | Integration | Worker runs on a long file | status → `indexed`, `chunk_count` > 1, embeddings dim = 1024 | ✅ |
| T-4 | FR-C2 | Integration | `.pptx` with 2 slides | chunk `location`s include "slide 1" / "slide 2" (→ citations) | ✅ |
| T-5 | NFR-5 | Integration | Every chunk carries its `course_id`; scoped similarity search | only same-course chunks returned; other course has its own | ✅ |
| T-6 | FR-C1 | Integration | Upload a disallowed extension (`.exe`) | 422 rejected | ✅ |
| T-7 | NFR-5 | Integration | Non-owner (student) uploads / lists documents | 403 both | ✅ |
| T-8 | FR-C2 | Integration | Corrupt `.pdf` through the worker | status → `failed`, `error` surfaced in the list | ✅ |
| T-9 | FR-C3 | Integration | `DELETE /documents/{id}` | 204; document and its chunks gone; file removed from storage | ✅ |
| T-10 | FR-C4 | Integration | `POST /documents/{id}/reindex` on a failed doc | status → `processing`, re-enqueued, error cleared | ✅ |
| T-11 | — | Lint | `ruff check app tests` | clean | ✅ |
| T-12 | — | Migration | `alembic upgrade head` (failed status, chunk.course_id/index, document.storage_key/error) | applies cleanly | ✅ |
| T-13 | FR-C1–C2 | Manual (live) | Real API + worker: login → create course → upload `.txt`, `.pptx`, corrupt `.pdf` → poll | txt→indexed(3), pptx→indexed(2, per-slide), pdf→failed | ✅ |
| T-14 | — | Build | `npm run build` (frontend incl. upload panel) | builds, 47 modules | ✅ |

**Notes / design:**
- **Object storage** is a `Storage` seam (`app/storage.py`); the local-disk backend is used in
  dev/test, an S3/GCS backend can drop in without touching callers.
- **Queue + worker** use a Redis list (`app/ingestion/queue.py`) drained by a standalone process
  (`python -m app.ingestion.worker`). Tests stand in for the worker by popping the queue and calling
  `process_document` directly — same code path.
- **Embeddings** go through an `Embedder` seam; `LocalEmbedder` is a deterministic hashing embedder
  so cosine similarity still tracks word overlap, making retrieval testable offline.
- A bug found & fixed during the live smoke: the worker's blocking `BRPOP` raced with redis-py's
  socket read deadline and crashed the loop. Switched to non-blocking RPOP polling + a guard so the
  worker never dies on a transient error. Added an autouse fixture that clears the ingest queue per
  test so a stray live job can't leak in.
- Browser click-through of the instructor upload screen not run here (no browser driver); the API,
  pipeline, scoping, the live worker run, and the frontend build are verified independently.

**Regression (earlier tests re-run and still pass?):** ✅ — full suite green (26/26); Phase 0/1/2
tests unaffected.
