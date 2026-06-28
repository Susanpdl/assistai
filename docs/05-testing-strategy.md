# 05 · Testing Strategy

We test every phase before moving on, and we **write down every test** so there's a record that the
feature actually works. *(Testing is how we turn "I think it works" into "here's proof it works.")*

## The kinds of tests we use

*(Think of these as a pyramid: many small fast tests at the bottom, fewer big slow ones at the top.)*

1. **Unit tests** — test one small function in isolation (e.g., "does the rotating-code generator
   produce a fresh code each interval?"). Fast, run constantly.
2. **Integration tests** — test pieces working together (e.g., "upload a file → does the worker
   chunk and store embeddings?"). Touches the database.
3. **End-to-end (E2E) tests** — test a real user flow through the UI (e.g., "student logs in via
   magic link, asks a question, sees a cited answer"). Slow but closest to reality.
4. **Manual verification** — a human clicks through and confirms it looks/behaves right. Always
   recorded too, even if not automated.

## Tooling (to confirm at Phase 0/1)

| Layer | Likely tool | Notes |
|-------|-------------|-------|
| Backend (Python) | `pytest` | Standard for FastAPI; supports unit + integration. |
| API integration | `pytest` + `httpx` test client | Calls endpoints in-process against a test DB. |
| Frontend (React) | Vitest + React Testing Library | Component/unit tests; pairs with Vite. |
| E2E | Playwright | Drives a real browser through full flows. |
| Build check | `vite build` | A clean production build is our minimum gate (already passing). |

*(We pin exact tools when the relevant phase starts. Until the backend exists, "tests" are the build
check + manual verification of the UI prototype.)*

## What "tested" means per phase (Definition of Done, testing part)

- Each requirement (FR/NFR) the phase claims is covered by at least one test.
- Tests **pass**, and earlier phases' tests still pass (regression check).
- Results are written to `testing/<feature>.md` using the template below.

## Where test records live

`docs/testing/` holds one log per feature. Every time we run tests for a feature, we append an entry.
See [`testing/README.md`](testing/README.md) and [`testing/TEMPLATE.md`](testing/TEMPLATE.md).

## Test record template (copy for each run)

```markdown
### <Feature> — test run <YYYY-MM-DD>

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-A1 | E2E | Requested magic link, clicked it | Logged in as student | ✅ Pass |
| T-2 | FR-A3 | Integration | Student hit instructor-only endpoint | 403 Forbidden | ✅ Pass |

**Notes / bugs found:** …
**Regression:** earlier feature tests re-run? ✅ / ❌
```

## Current test status

- ✅ **Build check:** `vite build` passes (40 modules, 0 errors).
- ✅ **Manual verification:** all three UI views render and are interactive (chat send, poll answer,
  instructor tab switching) in the prototype.
- ⏭️ Automated tests begin with Phase 0/1 when the backend exists.
