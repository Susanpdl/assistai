# Feature: Authentication — Magic Link

**Phase:** 1 · **Requirements:** FR-A1, FR-A2, FR-A3, FR-A4 · NFR-4

## Summary
Passwordless login. A person types their email, receives a one-time sign-in link, clicks it, and is
logged in. No passwords to manage, no university SSO to integrate. Every account is either a
`student` or an `instructor`, and that role controls what they can do.

## How it works (technical)

1. **Request:** user submits their email on the login screen. Backend creates a short-lived,
   single-use **token** *(a random unguessable string)* and stores its hash with an expiry (e.g., 15
   minutes).
2. **Email:** backend emails a link like `https://app/auth/verify?token=…` via the email provider.
   *(The same email provider is reused for announcements in Phase 7.)*
3. **Verify:** user clicks the link. Backend looks up the token, checks it's unexpired and unused,
   marks it used, and finds-or-creates the User.
4. **Session:** backend issues a session — a signed **JWT** *(a tamper-proof token the browser sends
   on each request to prove who it is)* or a server-side session cookie. It carries the user id and
   role.
5. **Authorization:** every protected endpoint checks the session and the role *(e.g., only
   `instructor` may approve enrollments)*.

*(Why a hash of the token, not the token itself? So that even if the database leaked, an attacker
couldn't use stored tokens to log in — same reason we'd hash passwords.)*

### Role assignment
- For the pilot, an instructor account is created/seeded by us; students self-identify as students
  on first login. *(Open question below on how strictly to control who becomes an instructor.)*

## Data
- **User**: `id`, `email` (unique), `name`, `role`.
- **LoginToken** (new helper table): `token_hash`, `email`, `expires_at`, `used_at`.

## API surface
- `POST /auth/request` — body `{ email }` → sends magic link. *(Always returns 200 even if the email
  isn't registered, so it can't be used to discover who has an account.)*
- `GET /auth/verify?token=…` — validates token, starts a session, redirects into the app.
- `POST /auth/logout` — ends the session.
- `GET /auth/me` — returns the current user `{ id, email, name, role }`.

## UI
- A minimal login screen: email field + "Send me a link" button, then a "check your email" state.
- Follows `04-ui-guidelines.md` (single primary `--ink` button, lots of whitespace).

## Guardrails / anti-cheat
- Tokens: single-use, short expiry, hashed at rest.
- Rate-limit `POST /auth/request` per email/IP to prevent inbox spam.
- Sessions expire; logout invalidates them.
- Collect only email + name (NFR-4, data minimization).

## Status
- ✅ Done: design.
- ⏳ Remaining: everything (build) — email provider wiring, token flow, session middleware, login UI,
  role guards.

## Tests
Log: `testing/auth-magic-link.md`. Key cases:
- Request → email sent (mock provider in tests).
- Valid token logs in; expired/used/invalid token rejected.
- Student blocked from instructor-only endpoints (403).
- Logout invalidates session.

## Open questions
- How do we decide who becomes an **instructor**? Answer: Seed a fixed list of instructor emails
- Session lifetime / "remember me" duration? - Answer: do whatever you think is better. 
