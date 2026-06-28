# AssistAI — Documentation

This folder is the **source of truth** for what we are building and how. We write the docs first,
then build to match them, and we keep them updated as we go.

> **How to read these docs:** They're written technically, but wherever a concept might be
> unfamiliar you'll find a plain-language note in parentheses *(like this)*. The goal is for the
> docs to teach the software-development reasoning, not just record decisions.

## Map of the docs

| File | What it covers |
|------|----------------|
| [`00-overview.md`](00-overview.md) | The product vision, who uses it, the v1 scope, and a glossary of terms. |
| [`01-requirements.md`](01-requirements.md) | Exactly what the system must do (functional requirements) and qualities it must have (non-functional). |
| [`02-architecture.md`](02-architecture.md) | The technical shape: layers, tech stack, data model, and the architecture diagram. |
| [`03-development-plan.md`](03-development-plan.md) | The phases we build in, our working method, and the "definition of done." |
| [`04-ui-guidelines.md`](04-ui-guidelines.md) | The minimal design system every screen must follow, so the UI stays consistent. |
| [`05-testing-strategy.md`](05-testing-strategy.md) | How we test each phase and where we record test results. |
| [`06-challenges.md`](06-challenges.md) | A running log of problems we hit during development and how we solved them. |
| [`features/`](features/) | One document per feature: what it is, what's done, what's left, and how it works. |
| [`testing/`](testing/) | A test log per feature — every test we run gets written down here. |
| [`architecture.mmd`](architecture.mmd) | The editable system diagram (Mermaid). See `architecture-link.txt` for an editable link. |

## Our working method (short version)

1. **Document first.** A feature isn't started until its doc in `features/` describes it.
2. **One phase at a time.** We finish a phase, test it, write down the test results, *then* move on.
3. **Keep the UI minimal and consistent.** Every screen follows `04-ui-guidelines.md`.
4. **Status lives in the docs.** Each feature doc has a Status section we keep current.

See [`03-development-plan.md`](03-development-plan.md) for the full method and the phase list.
