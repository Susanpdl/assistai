# Live Sessions & Polls — Test Log

One entry per test run. See [`../features/live-sessions-polls.md`](../features/live-sessions-polls.md).

---

### Live sessions & polls — test run 2026-06-24

Automated suite: `cd backend && uv run pytest` (37 passed total; 4 new for this feature).
WebSockets are exercised through Starlette's TestClient: one client (entered via `with`, so the
app lifespan starts the Redis pub/sub subscriber) holds all the sockets, while HTTP actions
(start session, push poll, reveal) go through the per-user authenticated clients and fan out over
Redis to the room.

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | FR-L1, FR-L2 | Integration (WS) | Two student clients join a session; instructor watches | instructor receives `connected_count = 2` | ✅ |
| T-2 | FR-L3 | Integration (WS) | Instructor `POST /sessions/{id}/activities` | `poll_pushed` reaches the connected student | ✅ |
| T-3 | FR-L4 | Integration (WS) | Student submits an answer | `answer_ack=ok`; instructor gets `results_update` tally | ✅ |
| T-4 | NFR-6 | Integration (WS) | Same student answers again | second answer rejected (`answer_ack=duplicate`) | ✅ |
| T-5 | Open-q (reveal) | Integration (WS) | Instructor `POST /activities/{id}/reveal` | student now receives `poll_revealed` + the results | ✅ |
| T-6 | NFR-5 | Integration (WS) | A logged-in, non-enrolled user opens the room | connection refused (close 4403 → `WebSocketDisconnect`) | ✅ |
| T-7 | Open-q (reveal) | Integration | Before reveal, instructor reads tallies over REST; student was never sent them | results visible to owner, `revealed=false` | ✅ |
| T-8 | — | Lint | `ruff check app tests` | clean | ✅ |
| T-9 | — | Migration | `alembic upgrade head` (session.status, activity.revealed, unique constraint) | applies cleanly | ✅ |

**Notes / design:**
- **Connection manager** (`app/live/manager.py`): rooms are named by session id; messages are
  **published to a Redis channel** and a single per-process **subscriber** delivers them to that
  process's local sockets — so it's scale-safe (a poll pushed on one server reaches students on
  another). The subscriber signals readiness on startup so no early publish is missed.
- **Connected count** is the size of a Redis set of *student* connection ids (instructors aren't
  counted), so the "X connected" number is correct across instances.
- **Role-aware delivery:** messages may target `audience: "instructor"` (live tallies before
  reveal) or `"all"`; filtering happens against each instance's local sockets.
- **One answer per student** is enforced by a unique `(activity_id, student_id)` constraint; a
  duplicate submit is acked as `duplicate`. These responses double as the Phase 6 attendance proof.
- HTTP actions publish via the **sync** Redis client; the **async** subscriber delivers — cleanly
  decoupling the REST handlers from the WebSocket event loop.
- Per the feature's open question, students see results **only after the instructor reveals**.
- Browser click-through of the live screens wired to the WebSocket is covered by the frontend build;
  the realtime path, aggregation, gating, and access control are verified here.

**Regression (earlier tests re-run and still pass?):** ✅ — full suite green (37/37); Phase
0–4 tests unaffected.
