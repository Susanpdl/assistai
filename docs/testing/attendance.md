# Attendance — Test Log

One entry per test run. See [`../features/attendance.md`](../features/attendance.md).

---

### Attendance — test run 2026-06-24

Automated suite: `cd backend && uv run pytest` (43 passed total; 6 new for this feature),
integration tests against the docker-compose Postgres + Redis. Polls are answered by inserting
an `ActivityResponse` directly (the WebSocket answer path is covered in `test_live`); attendance
only reads that a response exists.

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-N1, FR-N2 | Integration | Valid current code, no poll pushed | `present`, proofs `["code"]` | ✅ |
| T-2 | NFR-3 | Integration | A code from an out-of-grace window (replay) | rejected (422) | ✅ |
| T-3 | FR-N3 | Integration | Poll pushed; code only | not present, `needs_poll=true` | ✅ |
| T-4 | FR-N3 | Integration | Then student answers + checks in again | `present`, proofs `["code","poll"]` | ✅ |
| T-5 | FR-N4 | Integration | Second account checks in on the same device | blocked (409, device binding) | ✅ |
| T-6 | FR-N5 | Integration | Instructor roster after one check-in | `total=2`, `present=1`, statuses {present, absent} | ✅ |
| T-7 | NFR-5 | Integration | Student requests the rotating code / roster | 403 (instructor-only) | ✅ |
| T-8 | FR-N6 | Integration | End session → finalize; roster after end | `present` locked in for code+poll student | ✅ |
| T-9 | — | Lint | `ruff check app tests` | clean | ✅ |
| T-10 | — | Migration | `alembic upgrade head` (attendance unique + device_binding table) | applies cleanly | ✅ |

**Notes / design:**
- **Rotating code** (`attendance/codes.py`) is derived by HMAC of `(session_id, time_window)` —
  stateless, so any instance computes the same code; a screenshot goes stale within one window. A
  one-window grace covers typing time. Default interval 15s.
- **The present rule** (`attendance/service.py`): a valid code marks present **unless** a poll was
  pushed this session, in which case the student must also have answered a poll (two proofs at
  different moments). Status is computed live (a student who answers after checking in flips to
  present); `finalize()` on session-end persists the final status.
- **Device binding** — one account per `device_id` per session (a per-browser id from the client);
  a second account on the same device is rejected. Sturdier in the future native app.
- **GPS/Bluetooth deliberately deferred** to the native app (imprecise/unsupported on web); the rule
  is shaped so a proximity proof can be added later as another check without model changes.
- Browser click-through of the check-in / instructor code screens is covered by the frontend build;
  code rotation, the present rule, replay rejection, and device binding are verified here.

**Regression (earlier tests re-run and still pass?):** ✅ — full suite green (43/43); Phase
0–5 tests unaffected.
