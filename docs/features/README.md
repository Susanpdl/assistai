# Features

One document per feature. Each follows the same shape (see [`TEMPLATE.md`](TEMPLATE.md)):
**Summary · Requirements covered · How it works (technical, with plain-language notes) · Data ·
API · UI · Anti-cheat/Guardrails (if any) · Status (Done / In progress / Remaining) · Tests · Open
questions.**

The **Status** section in each doc is kept current — it's how we track what's built without digging
through code.

## Feature index

| # | Feature | Doc | Phase | Status |
|---|---------|-----|-------|--------|
| 1 | Auth — magic link | [`auth-magic-link.md`](auth-magic-link.md) | 1 | 🟡 Designed, not built |
| 2 | Enrollment & approval | [`enrollment-approval.md`](enrollment-approval.md) | 2 | 🟡 Designed, not built |
| 3 | Content & ingestion | [`content-ingestion.md`](content-ingestion.md) | 3 | 🟡 Designed, not built |
| 4 | AI tutor (RAG + guardrails) ⭐ | [`ai-tutor.md`](ai-tutor.md) | 4 | 🟡 Designed, not built |
| 5 | Live sessions & polls | [`live-sessions-polls.md`](live-sessions-polls.md) | 5 | 🟡 Designed, not built |
| 6 | Attendance (anti-cheat) | [`attendance.md`](attendance.md) | 6 | 🟡 Designed, not built |
| 7 | Announcements & email | [`announcements.md`](announcements.md) | 7 | 🟡 Designed, not built |
| 8 | Instructor dashboard | [`instructor-console.md`](instructor-console.md) | 8 | 🟡 UI prototype only |

**Legend:** 🟢 Done · 🟡 Designed / partial · ⏳ Not started

UI for views 1–3 exists as a **prototype with mock data** — the screens are built, but they aren't
wired to a real backend yet.
