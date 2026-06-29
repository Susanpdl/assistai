# Announcements & Notifications — Test Log

One entry per test run. See [`../features/announcements.md`](../features/announcements.md).

---

### Announcements & notifications — test run 2026-06-24

Automated suite: `cd backend && uv run pytest` (49 passed total; 6 new for this feature),
integration tests against the docker-compose Postgres + Redis. Emails go through the capturing
fake sender (also used by magic-link login), so we clear it before asserting on announcement
emails. Background email sending runs as a FastAPI background task and is exercised by the test
client.

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-M1, FR-M2 | Integration | Instructor posts an announcement (2 approved students) | 201; one email per enrolled student (correct recipients + subject) | ✅ |
| T-2 | FR-M3 | Integration | Non-enrolled user reads / comments | 403 both | ✅ |
| T-3 | FR-M4 | Integration | Student comments; reload the feed | comment appears under the right announcement | ✅ |
| T-4 | Open-q (edit/delete) | Integration | Owner edits then deletes the announcement | text updated; 204; feed empty | ✅ |
| T-5 | Open-q (moderation) | Integration | Another student deletes someone else's comment; owner moderates | 403 for the student, 204 for the owner | ✅ |
| T-6 | Guardrails | Integration | A transient email failure on the first attempt | retried; the email is delivered (not dropped) | ✅ |
| T-7 | — | Lint | `ruff check app tests` | clean | ✅ |

**Notes / design:**
- **Models already existed** (`Announcement`, `Comment` from Phase 0) — no migration this phase.
- **Email reuse:** the Phase 1 `EmailSender` serves both magic-link login and announcements; a new
  `send_announcement` template adds course branding + an unsubscribe note.
- **Out-of-band send:** posting returns immediately; emails go via a FastAPI background task
  (`announcements/notify.py`) that retries each recipient once on a transient failure and logs a
  final failure rather than dropping the rest of the class.
- **Permissions:** only the course owner posts/edits/deletes an announcement; only enrolled students
  (or the owner) read and comment; a comment can be deleted by its author or moderated by the owner.
- **Limits:** announcement text ≤ 5000 chars, comments ≤ 2000 (Pydantic), empty rejected (422).
- Browser click-through of the announcements feed is covered by the frontend build; the API,
  email fan-out, access control, and retry are verified here.

**Regression (earlier tests re-run and still pass?):** ✅ — full suite green (49/49); Phase
0–6 tests unaffected.
