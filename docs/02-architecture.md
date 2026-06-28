# 02 · Architecture

This describes the technical shape of the system: the layers, the technology in each, and the data
model. The visual version is in [`architecture.mmd`](architecture.mmd) (open the editable link in
[`architecture-link.txt`](architecture-link.txt)).

## The five layers

*(We split the system into layers so each part has one job. A change in one layer shouldn't force
changes in the others — that separation is what keeps a codebase maintainable.)*

1. **Client layer — React single-page app.** The three views (student study, student in-class,
   instructor console). Talks to the backend over HTTP and WebSockets.
2. **API gateway — FastAPI.** Handles login, REST endpoints (request/response actions), and the
   WebSocket connection. Enforces authentication and role-based authorization on every request.
3. **Realtime layer.** A connection manager that tracks who's connected to which "room" (a live
   session) and broadcasts messages (polls, results, connected-count). Redis pub/sub sits underneath
   so it still works if we run more than one server copy.
4. **AI subsystem.** A LangGraph orchestrator that classifies the student's intent and routes it:
   retrieve-and-answer (RAG), call a tool, or escalate to the instructor. Generation goes through
   the Claude API.
5. **Persistence layer.** Postgres (with the pgvector extension) for both normal data and
   embeddings, Redis for cache + pub/sub, and object storage for uploaded files.

Plus a **background ingestion worker** that processes uploaded files (chunk → embed → store) so
uploads don't block the instructor.

## Tech stack

| Concern | Choice | Why |
|---------|--------|-----|
| Frontend | React + Vite | Fast dev, component reuse, and the same components can inform a future React Native app. |
| Styling | Hand-built CSS design system | Full control of the minimal look; no framework to fight. See `04-ui-guidelines.md`. |
| API | FastAPI (Python) | Async, native WebSocket support, great for AI/Python ecosystem. |
| Database | Postgres + pgvector | One database for relational data *and* vector search (no separate vector DB). |
| Cache / realtime | Redis | Doubles as a cache and a pub/sub backbone for broadcasting. |
| AI orchestration | LangGraph | Classroom flows branch (answer / tool / escalate); a state machine fits better than a linear chain. |
| AI generation | Claude API (claude-opus / sonnet) | Grounded generation from retrieved material. |
| File storage | Object storage (e.g., S3-compatible) | Cheap, durable storage for raw uploads. |
| Email | Transactional email provider (e.g., Resend) | Needed for magic-link login *and* announcement notifications. |
| Background jobs | Async worker (queue-driven) | Ingestion runs out-of-band so uploads return immediately. |

*(We will pin exact versions and the email provider when Phase 1 starts; this table is the
direction, not the lockfile.)*

## Data model (entities)

These are the core "tables" *(a table is just a structured list of one kind of thing — e.g., all
users)*. Relationships are noted with → (one-to-many) and ↔ (many-to-many).

- **User** — `id`, `email`, `name`, `role` (`student` | `instructor`). The `role` gates all
  permissions.
- **Course** — `id`, `code`, `name`, `owner_id` → User(instructor). One instructor owns many courses.
- **Enrollment** — links Student ↔ Course with a `status` (`pending` | `approved` | `rejected`).
  This is how the request-and-approve flow is stored.
- **Session** — `id`, `course_id`, `started_at`, `ended_at`. One live class meeting.
- **Message** — `id`, `course_id`, `session_id?`, `author`, `role` (user/ai), `text`, `citation?`.
  Stores the chat (tied to a live session, or to async study when `session_id` is null).
- **Document** — `id`, `course_id`, `filename`, `type`, `status` (`processing` | `indexed`).
  Metadata for an uploaded file.
- **Chunk** — `id`, `document_id`, `text`, `embedding` (vector), `location` (e.g., "Week 4, p.12").
  The searchable pieces; `location` is what becomes the citation.
- **Activity** — `id`, `session_id`, `type` (`poll` | `quiz`), `question`, `options`.
- **ActivityResponse** — `id`, `activity_id`, `student_id`, `choice`. One student's answer.
- **Attendance** — `id`, `session_id`, `student_id`, `status` (`present` | `absent`), `proofs`
  (which checks passed: code, poll). Built from check-ins.
- **Announcement** — `id`, `course_id`, `author_id`, `text`, `created_at`.
- **Comment** — `id`, `announcement_id`, `author_id`, `text`, `created_at`.

*(Notice attendance reuses Session, Activity, and ActivityResponse — the anti-cheat rule is "did this
student produce both a valid code check-in and an ActivityResponse in this Session?" We're not
inventing new infrastructure, just combining what's already there.)*

## How a student question flows (example)

1. Student types a question → API gateway (FastAPI) authenticates and forwards it.
2. LangGraph classifies intent. Most questions → **retrieve path**.
3. Retrieve path embeds the question, runs a similarity search in pgvector, gets the top chunks.
4. Those chunks + the question + the tutor guardrail prompt go to Claude.
5. Claude returns a grounded answer; we attach the chunk's `location` as the citation.
6. If intent is "do my assignment," guardrails route to a Socratic/hint response instead.
7. If confidence is low or policy requires, the **escalate path** notifies the instructor via the
   realtime layer.

## How real-time works (example)

1. Instructor pushes a poll → WebSocket → connection manager.
2. Connection manager broadcasts the poll to every student in that session's room.
3. Students answer → responses flow back → results aggregate → broadcast to the instructor.
4. Redis pub/sub mirrors these messages so multiple server copies stay in sync.

See per-feature docs in [`features/`](features/) for the detailed design of each piece.
