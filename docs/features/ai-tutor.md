# Feature: AI Tutor (RAG + Guardrails) ⭐

**Phase:** 4 · **Requirements:** FR-T1–FR-T5 · NFR-5 · This is the core value of the product.

## Summary
A student asks a question in plain language; the AI answers **grounded in that course's uploaded
material**, shows a **citation**, and behaves like a Socratic tutor — it explains, gives worked
examples, but refuses to hand over a graded assignment verbatim. When it can't answer confidently or
policy requires a human, it **escalates** to the instructor.

## How it works (technical)

We use **RAG (Retrieval-Augmented Generation)** so the model answers from the professor's material,
not its own memory:

1. **Receive** the question (must be for a course the student is approved in).
2. **Classify intent** (LangGraph node): is this a normal question, a request to *do* an assignment,
   a tool request (quiz/progress), or something to escalate? *(LangGraph is a state machine — it lets
   the flow branch instead of running one fixed sequence.)*
3. **Retrieve** (normal path): embed the question, similarity-search pgvector for the top chunks in
   this course.
4. **Generate:** send Claude the question + retrieved chunks + the **tutor system prompt** (the
   guardrails). Claude answers using only the provided chunks.
5. **Cite:** attach the `location` of the chunks used (e.g., "Week 5, slide 17").
6. **Store** the exchange as Messages.

### The guardrails (tutor behavior)
The system prompt instructs the model to:
- Act as a tutor for *this* course; ground answers in the provided material and cite it.
- **Allow** explanations, hints, and worked examples (illustrative problems, not the student's
  actual graded one).
- **Refuse** to produce a student's graded assignment verbatim; instead guide them with steps/hints.
- Say "I'm not sure / let me flag your instructor" rather than invent an answer.

*(Important honesty note: a system prompt is a strong nudge but can be **jailbroken** — a determined
student may phrase things to slip past it. That's why we don't rely on the prompt alone:)*

- The **intent classifier** routes obvious "do my homework" requests to a hint/refusal path **before**
  generation.
- Optional **integrity logging** records flagged requests for the instructor to review.
- Strictness is **instructor-configurable** (e.g., "worked examples allowed" — our v1 default).

### Escalation
If confidence is low, the question is policy-flagged, or the student asks for a human, the
**escalate path** sends the question to the instructor via the realtime layer (and it appears in the
instructor's "escalated questions" list).

## Data
- **Message**: `id`, `course_id`, `session_id?`, `author`, `role` (user/ai), `text`, `citation?`,
  `flagged?`.
- Reads **Chunk** (embeddings) for retrieval.
- **Escalation** (or a flag on Message): `question`, `student_id`, `status` (needs/answered).

## API surface
- `POST /courses/{id}/ask` *(student, approved)* — body `{ question }` → `{ answer, citation, escalated }`.
- `GET /courses/{id}/messages` — chat history.
- (Internal) LangGraph orchestrator with nodes: classify → retrieve → generate → cite; plus tool and
  escalate branches.

## UI
- The student study + in-class chat already exist (mock). Wire to `/ask`; render the `source-pill`
  citation; show a "sent to your instructor" state on escalation.

## Guardrails / anti-cheat
See "The guardrails" above: system prompt + intent classifier + optional logging + configurable
strictness. Retrieval is course-scoped so answers can't leak other courses' material.

## Status
- ✅ Done: design; chat UI exists in prototype (canned replies).
- ⏳ Remaining: LangGraph graph, retrieval against pgvector, Claude integration, guardrail prompt +
  classifier, citation wiring, escalation path.

## Tests
Log: `testing/ai-tutor.md`. Key cases:
- A factual course question returns an answer **with a citation** to a real chunk.
- "Write my assignment for me" → guided/refused, not completed verbatim.
- A question with no relevant material → graceful "not sure" / escalate, no hallucinated citation.
- Retrieval never returns another course's chunks.

## Open questions
- Which Claude model (opus vs sonnet) for cost/quality balance, and which embedding model? Answer: Sonnet is good for now or any free model. I want to make it as cost free as possible since it is our first version. Embedding model of your choice as per my need.
- Confidence threshold for auto-escalation? Answer: whatever you like
- Exact set of instructor strictness presets? Answer: whatever you like
