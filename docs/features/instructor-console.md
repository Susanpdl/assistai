# Feature: Instructor Dashboard

**Phase:** 8 · **Requirements:** FR-D1, FR-D2

## Summary
The instructor's home screen: at-a-glance stats (students enrolled, questions today, questions
escalated), the list of escalated questions to address, plus navigation to the other instructor
tools (content upload, live session, enrollment requests, announcements, students). Most of its
data comes from features built in earlier phases — this phase wires it to real numbers.

## How it works (technical)

The dashboard mostly **reads and summarizes** data other features produce:
- *Students enrolled* ← count of `approved` Enrollments (Phase 2).
- *Questions today* ← count of student Messages today (Phase 4).
- *Escalated to you* ← count of open escalations (Phase 4).
- *Escalated questions list* ← the escalation records, each markable as answered.

*(This is why it's late in the plan: a dashboard is only as real as the features feeding it. We build
the producers first, then the summary.)*

## Data
- Reads: Enrollment, Message, Escalation/flagged Messages, Session.
- Writes: escalation `status` (`needs` → `answered`).

## API surface
- `GET /courses/{id}/dashboard` *(instructor)* — returns the stat counts.
- `GET /courses/{id}/escalations` *(instructor)* — list.
- `POST /escalations/{id}/answer` *(instructor)* — mark answered (optionally send the answer to the
  student).

## UI
- The instructor console (dashboard, stat cards, escalated list, sidebar nav, roster, upload) already
  exists as a **prototype with mock data** — this phase replaces mock numbers with live API data.
- Keep the minimal styling already in place (`04-ui-guidelines.md`).

## Guardrails / anti-cheat
- All endpoints owner-scoped (an instructor sees only their course's data).

## Status
- ✅ **Done (Phase 8):** `GET /courses/{id}/dashboard` (real stat counts — enrolled, pending,
  questions today/total, escalated open/answered), `POST /escalations/{id}/answer` (close the
  escalation **and** deliver the instructor's answer into the student's tutor chat), and the real
  dashboard + escalation-answering UI in the instructor course card. Reuses the Phase 4 escalations
  list. No migration (reads existing tables; writes `Message.escalation_status`). Tests:
  `testing/instructor-console.md` (3 new, 52 total).
- ⏳ **Deferred:** richer pilot stats (live participation %, attendance rate) can be layered on the
  same endpoint later.

## Tests
Log: `testing/instructor-console.md`. Key cases:
- Stat counts match seeded data.
- Marking an escalation answered moves it out of "needs answer".
- One instructor can't read another course's dashboard (403).

## Open questions
- Does "mark answered" also send the answer to the student (chat/email), or just close the item? Answer: Also send the answer to the student via chat
- Which extra stats are useful for the pilot (participation %, attendance rate)? Answer: sure
