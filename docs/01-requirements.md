# 01 · Requirements

This is *what* the system must do (functional requirements, "FR") and *how well* it must do it
(non-functional requirements, "NFR"). Each requirement has an ID so feature docs and tests can refer
to it.

*(Writing requirements down before coding means we can later check "did we actually build what we
said?" — that check is what testing verifies.)*

## Functional requirements

### Identity & access (`FR-A`)
- **FR-A1** A person can sign in with only their email via a magic link.
- **FR-A2** Every account has exactly one role: `student` or `instructor`.
- **FR-A3** The role determines what the person can see and do (authorization).
- **FR-A4** A signed-in session persists until logout or expiry.

### Courses & enrollment (`FR-E`)
- **FR-E1** An instructor can create a course they own.
- **FR-E2** A student can request to enroll in a course.
- **FR-E3** An instructor can approve or reject enrollment requests.
- **FR-E4** A student can only access a course's content once approved.
- **FR-E5** A student sees only the courses they're enrolled in; an instructor sees only courses
  they own.

### Course content & ingestion (`FR-C`)
- **FR-C1** An instructor can upload course files (PDF, DOCX, PPTX).
- **FR-C2** Uploaded files are processed in the background (chunked + embedded) without blocking the
  instructor.
- **FR-C3** Once processed, content is searchable for grounding AI answers.
- **FR-C4** The instructor can see the processing status of each file (processing / indexed).

### AI tutor (`FR-T`)
- **FR-T1** A student can ask a free-text question about an enrolled course.
- **FR-T2** The answer is grounded in that course's uploaded material (RAG).
- **FR-T3** Every grounded answer shows a citation (which document/section it used).
- **FR-T4** The tutor follows guardrails: it guides and gives worked examples but refuses to produce
  a student's graded assignment verbatim.
- **FR-T5** When the AI can't answer confidently (or policy requires a human), it can **escalate**
  the question to the instructor.

### Live sessions & polls (`FR-L`)
- **FR-L1** An instructor can start and end a live session for a course.
- **FR-L2** Students in the course see when a session is live and how many peers are connected.
- **FR-L3** An instructor can push a poll to all connected students.
- **FR-L4** Students answer the poll and results aggregate in real time.
- **FR-L5** The instructor sees live poll results.

### Attendance (`FR-N`)
- **FR-N1** During a live session, the system shows a rotating code (regenerates every few seconds).
- **FR-N2** A student checks in by entering the current code from their own device.
- **FR-N3** If a poll is pushed during the session, the student must also have answered a poll to be
  marked present (two-proof confirmation).
- **FR-N4** If no poll is pushed, a valid code check-in alone marks the student present.
- **FR-N5** Each device can check in only one account per session (device binding).
- **FR-N6** The instructor can view the attendance list for each session.

### Announcements (`FR-M`)
- **FR-M1** An instructor can post a text announcement to a course.
- **FR-M2** Posting an announcement emails every enrolled student in that course.
- **FR-M3** Students can read announcements and post text comments on them.
- **FR-M4** Students see announcements only for courses they're enrolled in.

### Instructor dashboard (`FR-D`)
- **FR-D1** The instructor sees counts: students enrolled, questions asked today, questions
  escalated.
- **FR-D2** The instructor sees the list of escalated questions and can mark them answered.

## Non-functional requirements

- **NFR-1 · Consistency** Every screen follows the minimal design system in `04-ui-guidelines.md`.
- **NFR-2 · Real-time** Live poll results and the connected-count update within ~1 second.
- **NFR-3 · Anti-cheat** Attendance must make forwarded-code sharing hard (rotating code +
  poll-match + device binding). It need not be perfect — it must raise the effort to cheat.
- **NFR-4 · Privacy** Collect the minimum personal data; attendance/location signals require user
  permission. *(Important because student data is sensitive and often legally protected.)*
- **NFR-5 · Groundedness** The tutor must not present an answer as sourced unless it came from
  retrieved course material.
- **NFR-6 · Scale (v1)** Support one class of ~30 concurrent students in a live session smoothly.
- **NFR-7 · Testability** Each phase ships with documented tests (see `05-testing-strategy.md`).
- **NFR-8 · Portability for mobile** Keep business logic in the backend/API so a future React Native
  app can reuse it without rewrites.

## Traceability

Each feature doc in `features/` lists the FR/NFR IDs it implements, and each test in `testing/`
references the requirement it verifies. *(This chain — requirement → feature → test — is how we
prove the product does what we promised.)*
