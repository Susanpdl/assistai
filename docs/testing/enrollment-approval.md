# Enrollment & Approval — Test Log

One entry per test run. See [`../features/enrollment-approval.md`](../features/enrollment-approval.md).

---

### Enrollment & approval — test run 2026-06-28

Automated suite: `cd backend && uv run pytest` (17 passed total; 8 new for this feature),
integration tests against the docker-compose Postgres + Redis. Plus a live curl smoke of the
full flow.

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-E1 | Integration | Instructor `POST /courses` | 201, returns a 6-char join code | ✅ |
| T-2 | FR-E1 | Integration | Student `POST /courses` | 403 (instructors only) | ✅ |
| T-3 | FR-E2 | Integration | Student `POST /courses/enroll` with a valid code | `pending` enrollment created | ✅ |
| T-4 | FR-E2 | Integration | Student enrolls again (same course) | idempotent — still one `pending` row | ✅ |
| T-5 | FR-E2 | Integration | Enroll with an unknown code | 404 | ✅ |
| T-6 | FR-E3 | Integration | Owner `POST /enrollments/{id}/decision` approved | status `approved` | ✅ |
| T-7 | FR-E4 | Integration | Approved student `GET /courses/{id}` | 200 (access granted) | ✅ |
| T-8 | FR-E4 | Integration | Pending/rejected student `GET /courses/{id}` | 403 (access denied) | ✅ |
| T-9 | FR-E3 | Integration | Non-owner instructor decides another's request | 403 | ✅ |
| T-10 | FR-E5 | Integration | Rejected student re-enrolls | row flips back to `pending` | ✅ |
| T-11 | FR-E2 | Integration | `GET /courses` for student vs instructor | role-aware (approved-only / owned; join code hidden from students) | ✅ |
| T-12 | FR-E3 | Integration | Decision sends email to student | capturing sender records "You're enrolled…" | ✅ |
| T-13 | FR-E1–E4 | Manual (curl) | Full live flow: create → enroll (pending) → 403 → approve (email printed) → 200 → course listed | each step as expected | ✅ |
| T-14 | — | Build | `npm run build` (frontend incl. Courses UI) | builds, 46 modules | ✅ |

**Notes / bugs found:** none. Smoke-test data was cleaned from the dev DB afterward.
Browser click-through of the new Courses screens not run in this environment (no browser driver);
API flow, role-aware data, and build all verified independently.

**Regression (earlier tests re-run and still pass?):** ✅ — full suite green (17/17), Phase 0 +
Phase 1 tests still pass.
