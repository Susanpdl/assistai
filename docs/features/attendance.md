# Feature: Attendance (Anti-Cheat)

**Phase:** 6 · **Requirements:** FR-N1–FR-N6 · NFR-3 · Depends on Live Sessions (Phase 5).

## Summary
Take attendance in a way that's hard to fake. The classic trick — a student in class shares the QR
code to friends who mark themselves "present" from elsewhere — is defeated by combining a **rotating
code** (a forwarded screenshot goes stale in seconds) with a **second, time-separated proof** (the
live poll answer), plus **device binding** (one account per phone per session).

> **The goal isn't a perfect, unbeatable system** — that doesn't exist. The goal is to raise the
> effort of cheating above the effort of just attending. Layered checks do that.

## How it works (technical)

**The rule (v1):**
- A student is **present** if they enter a **valid current rotating code** during the session
  (`code alone counts`).
- **And** if the instructor pushes a poll that session, the student must **also** have answered a
  poll (the stronger two-proof confirmation).
- If no poll is pushed, the valid code check-in alone marks them present.

**The mechanisms:**

1. **Rotating code** *(like the 6-digit code in an authenticator app)*: the instructor's screen
   shows a code that regenerates every few seconds (e.g., every 10–15s). The backend knows the
   current valid code(s) for the session.
   - *Why rotating?* A student screenshots the code and sends it to a friend, but by the time the
     friend types it, it's expired. This kills casual screenshot-sharing.
2. **Check-in:** the student enters the code on their own device; the backend verifies it's the
   current code for *this* live session.
3. **Poll-match (second proof):** the system checks whether the same student also has an
   ActivityResponse in this session (reusing Phase 5 data). Two proofs at *different moments* mean a
   one-off forwarded code isn't enough — you had to be present long enough to also answer the poll.
4. **Device binding:** the device registers an id; only **one account may check in per device per
   session**. *(Stops one person in the room from checking in five friends on their own phone.)*
5. **Result:** an **Attendance** record is written with which proofs passed.

**Why not GPS/Bluetooth in v1?** GPS is imprecise indoors and spoofable; Web Bluetooth doesn't work
on iOS Safari. Those proximity methods become attractive in the **native mobile app** (future phase)
— we've deliberately kept v1 to rotating-code + poll-match + device-binding, which work on the web
today. The attendance rule is designed so a proximity proof can be *added* as another check later
without changing the model.

## Data
- **Attendance**: `id`, `session_id`, `student_id`, `status` (`present` | `absent`),
  `proofs` (e.g., `["code","poll"]`), `checked_in_at`. Unique on (`session_id`, `student_id`).
- **Reads** ActivityResponse (poll proof) and a per-session rotating-code state (server-side, time-based).
- **DeviceBinding** (helper): `session_id`, `device_id`, `student_id` — enforces one account/device/session.

## API surface
- `GET /sessions/{id}/attendance/code` *(instructor)* — current rotating code to display.
- `POST /sessions/{id}/attendance/checkin` *(student)* — body `{ code, device_id }` → validates code,
  checks device binding, records/updates Attendance with the `code` proof.
- (On session end) finalize: students with required proofs → `present`, others → `absent`.
- `GET /sessions/{id}/attendance` *(instructor)* — the attendance list.

## UI
- **Student (in-class):** a check-in field for the code, then a clear "✓ Checked in" / "needs poll
  answer" state.
- **Instructor:** the rotating code displayed large (for the projector) + a live attendance count and
  list. Minimal styling per `04-ui-guidelines.md` (the green `--live` accent fits here).

## Guardrails / anti-cheat (summary)
| Threat | Defense |
|--------|---------|
| Screenshot the code, send to a friend | Rotating code expires in seconds |
| Friend has the code AND wasn't in class | Poll-match needs a second proof at a different moment |
| One person marks many friends on one phone | Device binding (one account / device / session) |
| Replay an old code | Code validated against the session's *current* time window |

## Status
- ✅ Done: design (rule + mechanisms).
- ⏳ Remaining: rotating-code generator + validator, check-in endpoint, device binding, poll-match
  finalization, instructor code display + attendance view, student check-in UI. **No UI exists yet**
  (this is a new screen for both roles).

## Tests
Log: `testing/attendance.md`. Key cases:
- Current code accepted; expired/old code rejected (replay test).
- With a poll pushed: code only → not present until poll answered; code + poll → present.
- No poll pushed: valid code → present.
- Second account on same device/session → blocked.
- Forwarded-code simulation (code valid but no poll, poll required) → not present.

## Open questions
- Code rotation interval and validity window. Answer: start ~15s with a small grace window.
- How is `device_id` derived on web? Answer: A signed cookie/browser fingerprint; sturdier in the native
  app.
- Should a late student (joined after the poll) get a make-up proof? Answer: No, counts as Absent as well
