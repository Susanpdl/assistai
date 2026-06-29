# 03 · Development Plan

## How we work

- **Documentation-first.** A feature is "started" only after its doc in `features/` describes what
  we're building and why.
- **One phase at a time.** We finish a phase, test it, write the results in `testing/`, and only
  then start the next phase. *(This is incremental delivery — building in small, verified steps
  instead of one big risky push.)*
- **Vertical slices where possible.** A "vertical slice" means one feature working end-to-end
  (UI → API → database) rather than building all of one layer first. It proves the whole path works
  early.
- **No time estimates.** Phases are ordered by dependency, not deadline. A phase might take a day or
  a week — we move when it's done and tested.

## Definition of Done (every phase)

A phase is done when **all** of these are true:

1. The feature meets the requirements (FR/NFR IDs) listed in its feature doc.
2. The UI (if any) follows `04-ui-guidelines.md`.
3. Tests are written **and passing**, and recorded in `testing/<feature>.md`.
4. The feature doc's **Status** section is updated (Done / Remaining).
5. Nothing already-working broke (we re-run earlier tests — "regression" checking).

## The phases

Phases are ordered so each one builds on a solid layer below it. Dependencies are noted.

### Phase 0 — Foundations & Design System
Set up the repo structure, backend scaffold (FastAPI), database (Postgres + pgvector via
docker-compose), and lock the design system. The React UI prototype already exists and the minimal
design system is built — this phase makes the backend skeleton runnable and the data model defined.
**Done when:** the app + a stub API run locally, the schema is created, and `04-ui-guidelines.md` is
agreed.

### Phase 1 — Identity & Access  *(depends on: Phase 0)*
Magic-link login, the User model, roles, and session handling. Wire up the email provider here
(it's reused by announcements later).
**Why first:** almost everything else needs "who is this person and what may they do?"
**Feature doc:** `features/auth-magic-link.md`.

### Phase 2 — Courses & Enrollment  *(depends on: Phase 1)*
Instructors create courses; students request enrollment; instructors approve/reject; access is
gated by enrollment.
**Feature doc:** `features/enrollment-approval.md`.

### Phase 3 — Course Content & Ingestion  *(depends on: Phase 2)*
Upload files → object storage → background worker chunks + embeds → pgvector. Show processing status.
**Why before the tutor:** the tutor has nothing to ground answers in until content is indexed.
**Feature doc:** `features/content-ingestion.md`.

### Phase 4 — AI Tutor (RAG + guardrails)  *(depends on: Phase 3)* ⭐ core slice
The heart of the product: grounded Q&A with citations, Socratic guardrails (worked examples allowed,
no verbatim assignments), and escalation. This is the vertical slice that proves the hardest part
works.
**Feature doc:** `features/ai-tutor.md`.

### Phase 5 — Live Sessions & Polls  *(depends on: Phase 1, 2)*
WebSocket connection manager, start/end session, live "connected" count, push poll, live results.
**Feature doc:** `features/live-sessions-polls.md`.

### Phase 6 — Attendance  *(depends on: Phase 5)*
Rotating code + the code-alone/code-plus-poll rule + device binding + instructor attendance view.
**Why after live sessions:** attendance is built on sessions and reuses poll responses.
**Feature doc:** `features/attendance.md`.

### Phase 7 — Announcements & Notifications  *(depends on: Phase 1, 2)*
Post text announcements, email all enrolled students, student comments.
**Reuses:** the email infrastructure from Phase 1.
**Feature doc:** `features/announcements.md`.

### Phase 8 — Instructor Dashboard polish  *(depends on: Phase 4, 5, 7)*
Wire the dashboard stats and escalated-questions list to real data now that the features feeding
them exist.
**Feature doc:** `features/instructor-console.md`.

### Phase 9 — Hardening & Mobile Prep  *(depends on: all)*
Accessibility pass, performance, a security review, and planning the React Native/Expo app (which
reuses the same API). *(We design the API cleanly throughout so this phase is planning + thin client,
not a rewrite.)*

## Dependency summary

```
Phase 0 ─┬─ Phase 1 ─┬─ Phase 2 ─┬─ Phase 3 ── Phase 4 ⭐
         │           │           │
         │           │           └─ Phase 5 ── Phase 6
         │           │
         │           └─ Phase 7
         │
         └─ (design system)        Phase 8 ── Phase 9
```

## Current status

- ✅ React UI prototype with all three views (mock data).
- ✅ Minimal monochrome design system applied and documented.
- ✅ Architecture diagram + editable link.
- ✅ This documentation set.
- ✅ **Phase 0** — backend scaffold (FastAPI + Postgres/pgvector + Redis) + full schema + migrations.
- ✅ **Phase 1** — magic-link auth (Redis sessions, role guards, email sender) + login gate.
- ✅ **Phase 2** — courses & enrollment (join-code, approve/reject + emails, access gating) + Courses UI.
- ✅ **Phase 3** — Course Content & Ingestion: storage seam + Redis queue + worker; extract
  (PDF/DOCX/PPTX/TXT) → chunk → embed → pgvector; upload/list/delete/reindex API with status
  (`processing`/`indexed`/`failed`); course-scoped chunks (NFR-5); instructor upload UI wired live.
  *(Real embedding model + tutor retrieval deferred to Phase 4; deterministic `LocalEmbedder` for now.)*
- ✅ **Phase 4** ⭐ — AI Tutor (RAG + guardrails): course-scoped retrieval over pgvector, a
  classify→retrieve→generate→cite orchestrator (with refuse/escalate branches; lightweight state
  machine mirroring the LangGraph design), intent classifier + tutor guardrail prompt, citations,
  escalation + integrity flagging, and the `/ask` `/messages` `/escalations` API. Generation is a
  seam — free offline `LocalGenerator` by default, Claude (`claude-sonnet-4-6`) when configured.
- ✅ **Phase 5** — Live Sessions & Polls: WebSocket rooms (`/ws/sessions/{id}`), a connection
  manager with Redis pub/sub relay (scale-safe), connected-count via a shared Redis set, session
  start/end, poll push + live aggregation + instructor reveal, role-aware delivery, one-answer-per-
  student. HTTP: start/end session, push poll, reveal, results, active-session.
- ✅ **Phase 6** — Attendance: HMAC time-based rotating code (+grace), check-in with device binding
  (one account/device/session), the code+poll present rule reusing Phase 5 responses, finalize on
  end, instructor code display + live roster, student check-in UI. API: code / checkin / attendance.
- ✅ **Phase 7** — Announcements & Notifications: post/list/comment, owner edit + delete + comment
  moderation, out-of-band batched email (background task + per-recipient retry) reusing the Phase 1
  email provider, instructor composer + student feed UIs.
- ⏭️ **Next:** Phase 8 — Instructor Dashboard polish (wire the dashboard stats and escalated-questions
  list to real data now that the features feeding them exist).
