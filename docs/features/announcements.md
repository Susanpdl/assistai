# Feature: Announcements & Email Notifications

**Phase:** 7 · **Requirements:** FR-M1–FR-M4 · Reuses the email infra from Phase 1.

## Summary
An instructor posts a text announcement to a course (like Canvas announcements). Every enrolled
student gets an **email**, and students can read announcements and **comment** on them. Text only —
no attachments, scheduling, or pinning in v1.

## How it works (technical)

1. **Post:** instructor submits text → an **Announcement** row is created for the course.
2. **Notify:** the backend looks up all `approved` enrollments for that course and sends each student
   an email via the email provider. *(Sending is done as a background job so posting returns
   immediately even for a big class — the same out-of-band pattern as ingestion.)*
3. **Read:** enrolled students see the course's announcements newest-first.
4. **Comment:** a student posts a text **Comment** on an announcement; comments are shown under it.

*(We reuse the Phase 1 email provider — one integration serves both magic-link login and these
notifications. Fewer moving parts.)*

## Data
- **Announcement**: `id`, `course_id`, `author_id`, `text`, `created_at`.
- **Comment**: `id`, `announcement_id`, `author_id`, `text`, `created_at`.

## API surface
- `POST /courses/{id}/announcements` *(instructor)* — create + trigger emails.
- `GET /courses/{id}/announcements` *(enrolled)* — list with comments.
- `POST /announcements/{id}/comments` *(enrolled)* — add a comment.

## UI
- **Instructor:** a simple composer (text + Post). 
- **Student:** an announcements feed with a comment box under each post.
- New screen, built from existing minimal patterns (cards, `--ink` primary button, comment rows).

## Guardrails / anti-cheat
- Only the course owner may post; only enrolled students may read/comment.
- Basic abuse handling on comments (length limits; instructor can delete — open question).
- Email send failures are retried/logged, not silently dropped.

## Status
- ✅ Done: design.
- ⏳ Remaining: everything — models, post/list/comment endpoints, batched email send, both UIs. **No
  UI exists yet.**

## Tests
Log: `testing/announcements.md`. Key cases:
- Posting creates the announcement and queues one email per enrolled student.
- Non-enrolled user can't read/comment (403).
- Comment appears under the right announcement.
- Email send is retried on transient failure (mock provider).

## Open questions
- Can the instructor edit/delete an announcement or moderate comments? Answer: delete yes, edit
  as well.
- Email format/branding and an unsubscribe consideration. Answer: Yeah do it.
