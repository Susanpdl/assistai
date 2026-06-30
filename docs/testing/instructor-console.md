# Instructor Dashboard — Test Log

One entry per test run. See [`../features/instructor-console.md`](../features/instructor-console.md).

---

### Instructor dashboard — test run 2026-06-30

Automated suite: `cd backend && uv run pytest` (52 passed total; 3 new for this feature),
integration tests against the docker-compose Postgres + Redis. Escalations are produced the real
way — a student asks in a course with no indexed material, so the tutor escalates (Phase 4).

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-D1 | Integration | Seed 2 approved + 1 pending student, 2 escalating questions; read dashboard | counts match: enrolled 2, pending 1, questions today/total 2, escalated_open 2, answered 0 | ✅ |
| T-2 | FR-D2 | Integration | `POST /escalations/{id}/answer` | escalation closes (open→0, answered→1) **and** the answer appears in the student's chat history | ✅ |
| T-3 | Guardrails | Integration | A different instructor reads this course's dashboard | 403 (owner-scoped) | ✅ |
| T-4 | — | Lint | `ruff check app tests` | clean | ✅ |

**Notes / design:**
- **No migration** — the dashboard reads existing tables (Enrollment, Message) and writes only an
  existing field (`Message.escalation_status`).
- **Stats** (`GET /courses/{id}/dashboard`): students enrolled (approved), pending requests,
  questions today + total (student messages), escalated open + answered. Owner-scoped.
- **Mark answered** (`POST /escalations/{id}/answer`): flips the escalation to `answered` and — per
  the feature's open question — **delivers the instructor's answer back into the student's tutor
  chat** as an AI-role message authored to that student (citation "Answered by your instructor"), so
  it shows up in their `/messages` history. Reuses the Message model; no new channel.
- Browser click-through of the dashboard cards / escalation answering is covered by the frontend
  build; the counts, the close+deliver flow, and owner-scoping are verified here.

**Regression (earlier tests re-run and still pass?):** ✅ — full suite green (52/52); Phase
0–7 tests unaffected.
