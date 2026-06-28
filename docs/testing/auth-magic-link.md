# Auth (Magic Link) — Test Log

One entry per test run. See [`../features/auth-magic-link.md`](../features/auth-magic-link.md)
for the feature spec.

---

### Auth (magic link) — test run 2026-06-28

Automated suite: `cd backend && uv run pytest` (9 passed). Backend integration tests run
against the docker-compose Postgres + Redis. Plus a live end-to-end curl smoke and a CORS check.

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-A1 | Integration | `POST /auth/request` with a valid email | 200 `{status:sent}`, magic link emailed | ✅ |
| T-2 | FR-A1 · NFR-4 | Integration | `POST /auth/request` with an unknown email | 200 (no account-existence leak) | ✅ |
| T-3 | FR-A2 | Integration | `GET /auth/verify` with a valid token | 303 → frontend, session cookie set | ✅ |
| T-4 | FR-A2 | Integration | `/auth/me` after verify | 200, returns the user | ✅ |
| T-5 | FR-A2 | Integration | `GET /auth/verify` with a bogus token | 303 → `?auth=invalid`, no session | ✅ |
| T-6 | FR-A2 | Integration | Re-use an already-consumed token | rejected (`?auth=invalid`) | ✅ |
| T-7 | FR-A2 | Integration | Verify a token past its expiry | rejected (`?auth=invalid`) | ✅ |
| T-8 | FR-A3 | Integration | `POST /auth/logout` then `/auth/me` | session invalidated → 401 | ✅ |
| T-9 | FR-A4 | Integration | Student hits an instructor-only route | 403 Forbidden | ✅ |
| T-10 | FR-A4 | Integration | Instructor (allowlisted email) hits same route | 200 OK | ✅ |
| T-11 | FR-A1·A2·A3 | Manual (curl) | Full live flow on a running server: request → console link → verify → `/auth/me` (role `instructor`) → logout → 401 | each step as expected | ✅ |
| T-12 | NFR (cross-origin) | Manual (curl) | CORS preflight + credentialed `/auth/me` from `Origin: localhost:5173` | `allow-origin: localhost:5173`, `allow-credentials: true` | ✅ |
| T-13 | — | Build | `npm run build` (frontend incl. login UI) | builds, 44 modules | ✅ |

**Notes / bugs found:**
- `EmailStr` rejects `.local` test addresses (special-use domain) — switched test data to a
  normal domain. App behaviour was correct; only the fixtures were wrong. Logged as C7 in
  `06-challenges.md`.
- Not done in this environment: a visual click-through in a real browser (no browser-driver
  available here). Every layer was verified independently (API flow, CORS, build); the
  click-through is the one remaining manual check to run locally.

**Regression (earlier tests re-run and still pass?):** ✅ — `test_health` still passes; full
suite green (9/9).
