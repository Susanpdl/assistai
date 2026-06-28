# Feature: Enrollment & Approval

**Phase:** 2 · **Requirements:** FR-E1–FR-E5

## Summary
Instructors create courses. Students can't add themselves — they **request** to join a course, and
the instructor **approves or rejects** the request. Course content is locked until approval. This
keeps the class roster controlled by the teacher.

## How it works (technical)

1. Instructor creates a Course (they become its `owner`).
2. Student finds the course (by a class join-code or a list) and submits an enrollment request.
3. This creates an **Enrollment** row with `status = pending`.
4. Instructor sees pending requests and sets `status` to `approved` or `rejected`.
5. Authorization checks read this table: a student may access a course's content/AI/sessions **only**
   if an `approved` Enrollment exists linking them.

*(The Enrollment row is the single source of truth for "is this student in this class?" — every
other feature asks it before showing course data.)*

## Data
- **Course**: `id`, `code`, `name`, `owner_id`.
- **Enrollment**: `id`, `student_id`, `course_id`, `status` (`pending` | `approved` | `rejected`),
  `requested_at`, `decided_at`. Unique on (`student_id`, `course_id`) so a student can't double-request.

## API surface
- `POST /courses` *(instructor)* — create a course.
- `GET /courses` — instructor: courses they own; student: courses they're approved for.
- `POST /courses/{id}/enroll` *(student)* — create a pending request.
- `GET /courses/{id}/enrollments?status=pending` *(instructor)* — list requests.
- `POST /enrollments/{id}/decision` *(instructor)* — body `{ decision: approved|rejected }`.

## UI
- **Student:** a "request to enroll" action and a pending-state indicator until approved.
- **Instructor:** a requests list with Approve / Reject (reuse `.esc-item` / `.btn` patterns).
- Minimal styling per `04-ui-guidelines.md`.

## Guardrails / anti-cheat
- Only the course `owner` can decide requests (role + ownership check).
- A rejected student can re-request only if we allow it (open question).

## Status
- ✅ Done: design.
- 🚧 In progress: the instructor console UI prototype hints at this but isn't wired.
- ⏳ Remaining: course creation, request/decision endpoints, gating logic, both UIs.

## Tests
Log: `testing/enrollment-approval.md`. Key cases:
- Student request creates `pending`; duplicate request blocked.
- Approve → student gains access; reject → access denied.
- Non-owner instructor cannot decide another course's requests (403).
- Unapproved student blocked from course content (403).

## Open questions
- Discovery: a **join-code** per course, or a browsable course list? Answer: Join-code is best
- Can a rejected student re-request? Notify the student on decision (email)? yeah can re-request. Yeah notify the student on decision via email.
