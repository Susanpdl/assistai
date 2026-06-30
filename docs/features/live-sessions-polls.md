# Feature: Live Sessions & Polls

**Phase:** 5 · **Requirements:** FR-L1–FR-L5 · NFR-2, NFR-6

## Summary
An instructor starts a live class session; enrolled students see it's live and how many peers are
connected. The instructor pushes a poll to every student's screen, students answer, and results
update in real time. This also provides the foundation attendance is built on (Phase 6).

## How it works (technical)

Real-time means the server can *push* to browsers without them asking — we use **WebSockets** *(a
connection that stays open both ways, unlike a normal request that closes after one reply)*:

1. **Start session:** instructor creates a **Session** (`status = live`). Students in the course get
   notified it's live.
2. **Connect:** each student's browser opens a WebSocket and joins the session's **room** *(a named
   group of connections, like a chat room)*. The **connection manager** tracks room membership and
   updates the "X connected" count.
3. **Push poll:** instructor sends a poll → connection manager **broadcasts** it to everyone in the
   room. The poll card appears on each screen.
4. **Answer:** each answer is sent back, stored as an **ActivityResponse**, aggregated, and the new
   tallies are broadcast to the instructor (and optionally students) live.
5. **Scale-safe:** under the connection manager, **Redis pub/sub** relays messages between server
   copies, so if two servers are running, a poll pushed on server A still reaches students on server
   B. *(For the ~30-student pilot one server is plenty, but designing for pub/sub now avoids a
   rewrite later.)*
6. **End session:** instructor ends it (`status = ended`); the room closes.

## Data
- **Session**: `id`, `course_id`, `status` (`live` | `ended`), `started_at`, `ended_at`.
- **Activity**: `id`, `session_id`, `type` (`poll`), `question`, `options` (list).
- **ActivityResponse**: `id`, `activity_id`, `student_id`, `choice`, `answered_at`. Unique on
  (`activity_id`, `student_id`).

## API surface
- `POST /courses/{id}/sessions` *(instructor)* — start a session.
- `POST /sessions/{id}/end` *(instructor)* — end it.
- **WebSocket** `/ws/sessions/{id}` — messages:
  - server→client: `session_state`, `connected_count`, `poll_pushed`, `results_update`.
  - client→server: `join`, `submit_answer`.
- `POST /sessions/{id}/activities` *(instructor)* — push a poll.

## UI
- The student in-class view (poll card + live results aside) and the instructor live-control screen
  already exist as prototypes. Wire them to the WebSocket.

## Guardrails / anti-cheat
- Only enrolled, approved students may join a course's session room.
- One response per student per activity (enforced by the unique constraint).
- These responses double as an attendance proof in Phase 6.

## Status
- ✅ **Done (Phase 5):** WebSocket endpoint (`/ws/sessions/{id}`, cookie-authed + access-gated),
  connection manager with Redis pub/sub relay (scale-safe), connected-count via a shared Redis set,
  session lifecycle (start/end), poll push + answer aggregation + reveal, role-aware delivery
  (tallies to the instructor until reveal), one-answer-per-student enforcement, and the
  `/courses/{id}/sessions`, `/sessions/{id}/end`, `/sessions/{id}/activities`, `/activities/{id}/reveal`,
  `/activities/{id}/results` API. Tests: `testing/live-sessions-polls.md` (4 new, 37 total).
- ✅ **Correct answers (post-pilot fix):** a poll may carry an optional `correct_option`. The
  instructor marks it when composing the poll; it's **hidden from students** in `poll_pushed` and
  delivered only on `poll_revealed`, where the student sees which option was right (and whether they
  got it). Opinion polls (no correct answer) still work — `correct_option` is optional.
- ⏳ **Deferred:** a course-level "class is live" push to students who aren't yet in the room (they
  currently poll `GET /courses/{id}/sessions/active`); quizzes stay out of live mode by design — a
  student asks the AI tutor for a quiz from the course materials instead (per the open question).

## Tests
Log: `testing/live-sessions-polls.md`. Key cases:
- Two student clients join → connected count = 2 on instructor.
- Poll pushed → appears on all student clients within ~1s.
- Answers aggregate correctly; double-answer rejected.
- Non-enrolled user cannot join the room.

## Open questions
- Do students see live results too, or only the instructor (until the instructor reveals)? Answer: until the instructor reveals
- Quiz (multi-question) support now or later? Answer: Just the poll only for the live session. for the quiz, student can ask the AI to give them quiz based in the course materials.
