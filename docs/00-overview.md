# 00 · Product Overview

## What we're building

**AssistAI** is an AI-assisted classroom platform: a website (and later a mobile app) that gives
every student a personal AI teaching assistant grounded in their *actual* course material, and
gives instructors a live window into how the class is doing.

In plain terms: a really good teaching assistant that lives inside a website, knows one specific
class inside-out, and is available any hour of the day. Students get a tutor grounded in their real
course content. Professors get attendance, announcements, live polls, and a view of what students
are struggling with.

## Who uses it (two roles)

- **Student** — enrolls in a course (with instructor approval), asks the AI questions grounded in
  course material, joins live class sessions, answers polls, checks in for attendance, reads
  announcements and comments on them.
- **Instructor** — owns a course, approves enrollment requests, uploads course material, runs live
  sessions and polls, takes attendance, posts announcements, and reviews escalated questions.

*(There are only two roles in v1 — no admins or TAs yet. Fewer roles = simpler permission rules to
get right.)*

## The three experiences (UI views)

1. **Student async study** — at home doing homework: pick a course, ask in plain language, get an
   answer with a **citation** (a small label showing exactly which slide/page the answer came from,
   so it's trustworthy rather than generic).
2. **Student in-class live** — during a live session: a green "live" banner, a poll the professor
   pushes to every screen, attendance check-in, and a private side-chat with the AI.
3. **Instructor console** — the control room: dashboard stats, escalated questions, content upload,
   live-session controls, attendance, enrollment approvals, and announcements.

## v1 scope (the pilot)

We are building for **one class at one school first**, to test with a real classroom before scaling.

| Area | v1 decision |
|------|-------------|
| Tenancy | Single school / one pilot class. (Multi-tenant later.) |
| Roles | Student + instructor only. |
| Login | Email-based, **passwordless via magic link** (no password, no university SSO). |
| AI tutor | Socratic tutor grounded in uploaded materials; **worked examples allowed**; refuses to do graded assignments verbatim. |
| Enrollment | Student requests → instructor approves. No self-enroll. |
| Attendance | Rotating code shown in class; **code alone counts**, and if a poll is pushed that session, answering it is also required. |
| Live sessions | Real-time polls with live results. |
| Announcements | Text only; students can comment; **email sent to all enrolled students on every post**. |
| Mobile | Deferred; likely React Native / Expo. |

## What is explicitly *out* of v1

Multi-tenant/multi-school, university SSO, passwords, admin/TA roles, scheduled or pinned
announcements, file attachments on announcements, the native mobile app, and grading/LMS
integration. We note these so we don't accidentally build them now.

## Glossary

- **RAG (Retrieval-Augmented Generation)** — instead of letting the AI answer from memory, we first
  *retrieve* the most relevant chunks of the professor's uploaded material, then ask the AI to
  answer *using only those chunks*. *(This is what makes answers grounded and citable.)*
- **Embedding** — a long list of numbers that represents the meaning of a piece of text. Texts with
  similar meaning have similar numbers, so we can find slides "close" to a student's question.
- **pgvector** — a Postgres extension that lets the database store embeddings and do similarity
  search. *(It means we don't need a separate "vector database" — Postgres does both jobs.)*
- **WebSocket** — a network connection that stays open so the server can push updates to the browser
  instantly *(needed for live polls and the "X students connected" counter)*.
- **Magic link** — passwordless login: you type your email, get a one-time sign-in link, click it,
  you're in.
- **Socratic tutoring** — teaching by guiding with questions and hints rather than handing over the
  finished answer.
