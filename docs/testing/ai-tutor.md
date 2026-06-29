# AI Tutor — Test Log

One entry per test run. See [`../features/ai-tutor.md`](../features/ai-tutor.md).

---

### AI tutor — test run 2026-06-24

Automated suite: `cd backend && uv run pytest` (33 passed total; 7 new for this feature),
integration tests against the docker-compose Postgres + Redis. Retrieval runs against real
pgvector; generation uses the deterministic offline `LocalGenerator` (no API key), so answers
are reproducible. The full path is exercised: upload → index → ask → classify → retrieve →
generate → cite / refuse / escalate → persist.

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-T1, FR-T2, FR-T3 | Integration | Approved student asks a factual question about indexed material | answer returned **with a citation** to the real document | ✅ |
| T-2 | FR-T4 | Integration | "Just do my homework… give me the answer to question 3" | guided/refused (`flagged=true`), not completed verbatim | ✅ |
| T-3 | FR-T5, NFR-5 | Integration | Ask in a course with no relevant material | `escalated=true`, **citation null** (no hallucinated source) | ✅ |
| T-4 | NFR-5 | Integration | Student approved in course A asks in course B | 403 (course-scoped access) | ✅ |
| T-5 | FR-T1 | Integration | Pending (unapproved) student asks | 403 | ✅ |
| T-6 | FR-T1 | Integration | `GET /courses/{id}/messages` after asking | history round-trips: user question + AI answer | ✅ |
| T-7 | FR-T5 | Integration | Instructor `GET /courses/{id}/escalations` | the escalated question surfaces with `status=needs` + student | ✅ |
| T-8 | — | Lint | `ruff check app tests` | clean | ✅ |
| T-9 | — | Migration | `alembic upgrade head` (message.flagged, message.escalation_status + enum) | applies cleanly | ✅ |

**Notes / design:**
- **Orchestration** is a small explicit state machine (`app/tutor/orchestrator.py`) mirroring the
  documented LangGraph node design — classify → retrieve → generate → cite, plus refuse and
  escalate branches — without taking on the LangGraph dependency for v1. Swappable later.
- **Guardrails** are two layers: a deterministic intent classifier (`guardrails.py`) that routes
  obvious "do my homework" / "talk to a human" requests *before* generation, plus the tutor
  **system prompt** for the model. "Do my homework" requests are recorded with `flagged=true` for
  the instructor (integrity log).
- **Generation** is a seam (`Generator`): default `LocalGenerator` (offline, free, extractive) for
  dev/tests; `ClaudeGenerator` (Anthropic API, `claude-sonnet-4-6`) switches on via
  `GENERATION_BACKEND=claude` + `ANTHROPIC_API_KEY`. Keeps v1 cost-free.
- **Groundedness (NFR-5):** retrieval is always filtered by `course_id`; if the best chunk's
  similarity is below `TUTOR_MIN_SIMILARITY` we escalate instead of inventing an answer/citation.
- Browser click-through of the student chat screen wired to `/ask` is covered by the frontend build;
  the API, RAG path, guardrails, and scoping are verified independently here.

**Regression (earlier tests re-run and still pass?):** ✅ — full suite green (33/33); Phase
0/1/2/3 tests unaffected.
