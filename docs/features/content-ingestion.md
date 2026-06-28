# Feature: Course Content & Ingestion

**Phase:** 3 · **Requirements:** FR-C1–FR-C4 · NFR-5

## Summary
Instructors upload course files (PDF, DOCX, PPTX). A background worker turns each file into
searchable pieces so the AI tutor can ground its answers in them. Uploading returns immediately —
the heavy processing happens out of sight.

## How it works (technical)

This is the **ingestion pipeline** *(the assembly line that turns a raw file into searchable
knowledge)*:

1. **Upload:** instructor uploads a file → it's stored in **object storage** *(a service for holding
   files, like a cloud folder)* and a **Document** row is created with `status = processing`. The API
   responds right away.
2. **Queue:** a job is placed on a queue for the background worker. *(A queue is a to-do list the
   worker pulls from, so the web request doesn't have to wait.)*
3. **Extract:** the worker reads the file and extracts its text (per page/slide).
4. **Chunk:** the text is split into overlapping **chunks** of a few hundred tokens. *(We split
   because an answer usually needs one relevant passage, not a whole 50-page PDF; overlap avoids
   cutting a sentence's meaning in half.)*
5. **Embed:** each chunk is sent to an embedding model, which returns an **embedding** (a vector of
   numbers representing meaning).
6. **Store:** chunk text + embedding + a **location label** (e.g., "Week 4, p.12") are saved to
   pgvector. The location is what later becomes the **citation**.
7. **Finish:** the Document's `status` flips to `indexed`; the instructor's UI updates.

## Data
- **Document**: `id`, `course_id`, `filename`, `type`, `status` (`processing` | `indexed` | `failed`),
  `uploaded_at`.
- **Chunk**: `id`, `document_id`, `course_id`, `text`, `embedding` (vector), `location`.

## API surface
- `POST /courses/{id}/documents` *(instructor)* — multipart upload; returns the Document (processing).
- `GET /courses/{id}/documents` *(instructor)* — list with statuses.
- `DELETE /documents/{id}` *(instructor)* — remove a file and its chunks.
- (Internal) worker consumes the queue; no public endpoint.

## UI
- The instructor "Upload content" screen already exists in the prototype: drag-and-drop box + a file
  list showing **Indexed** / **Processing…** states (with a spinner). Wire these to real statuses.

## Guardrails / anti-cheat
- Validate file type/size on upload.
- Scope chunks to a `course_id` so retrieval can never leak another course's material (NFR-5).
- Handle failures: mark `failed`, show it, allow retry.

## Status
- ✅ Done: design; the upload UI exists in the prototype (mock statuses).
- ⏳ Remaining: storage wiring, the worker (extract/chunk/embed/store), real status updates, delete.

## Tests
Log: `testing/content-ingestion.md`. Key cases:
- Upload returns immediately with `processing`.
- Worker produces N chunks with embeddings; status → `indexed`.
- A query retrieves only same-course chunks.
- Corrupt file → `failed`, surfaced in UI.

## Open questions
- Chunk size / overlap defaults? Answer: start ~500 tokens / ~50 overlap, tune later.
- Which embedding model? (Decide alongside the Claude setup in Phase 4.)
- Re-index when a file is replaced? Yeah
