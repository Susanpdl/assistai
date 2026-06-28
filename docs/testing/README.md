# Test Logs

One log per feature. Every test run gets recorded here using the template in
[`TEMPLATE.md`](TEMPLATE.md). See [`../05-testing-strategy.md`](../05-testing-strategy.md) for the
overall approach.

## Index

| Feature | Log | Status |
|---------|-----|--------|
| UI prototype (current) | this file (below) | ✅ Build + manual verification passing |
| Auth (magic link) | `auth-magic-link.md` | ✅ 9/9 passing (2026-06-28) |
| Enrollment & approval | `enrollment-approval.md` | ✅ 8/8 passing (2026-06-28) |
| Content & ingestion | `content-ingestion.md` | ⏳ not started |
| AI tutor | `ai-tutor.md` | ⏳ not started |
| Live sessions & polls | `live-sessions-polls.md` | ⏳ not started |
| Attendance | `attendance.md` | ⏳ not started |
| Announcements | `announcements.md` | ⏳ not started |
| Instructor dashboard | `instructor-console.md` | ⏳ not started |

---

### UI prototype — test run 2026-06-24

| ID | Requirement | Type | What we did | Expected | Result |
|----|-------------|------|-------------|----------|--------|
| T-1 | NFR-1 | Build | `vite build` | Compiles, 0 errors | ✅ Pass (40 modules) |
| T-2 | — | Manual | Loaded app, switched all 3 views | Each view renders | ✅ Pass |
| T-3 | FR-T1 (mock) | Manual | Typed a question in study view | AI reply + citation appears | ✅ Pass (mocked) |
| T-4 | FR-L4 (mock) | Manual | Answered the live poll | Result bar updates | ✅ Pass (mocked) |
| T-5 | FR-D1 (mock) | Manual | Opened instructor tabs | Dashboard/roster/upload render | ✅ Pass (mocked) |

**Notes:** All behavior is currently mock data (no backend). These confirm the UI/UX, not real logic.
**Regression:** n/a (first run).
