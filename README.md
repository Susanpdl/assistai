# AssistAI: AI Classroom Interaction Platform

> **Status:** Frontend prototype only. All data is mocked (`src/data/mock.js`) so the three
> experiences can be demoed end to end. The backend (FastAPI · Postgres/pgvector · Redis ·
> LangGraph · Claude API) is intentionally not built yet.

---


## The three views

| View | What it shows |
|------|---------------|
| **Student · Study** | At-home homework mode. Pick a course, ask in plain language, get an answer **with a citation pill** showing the exact slide/page it came from. Try the suggestion chips or type your own — the AI replies with a simulated grounded answer. |
| **Student · In-Class** | Live session. Green live banner, a **poll card** pushed by the professor (tap to answer — results update live in the right panel), plus a private side-chat to ask the AI quietly during class. |
| **Instructor Console** | The professor's control room: dashboard stat cards, **escalated questions** with status badges, a **drag-and-drop upload box** with indexed-file list, a live-session poll pusher, and a student roster. |

Everything is interactive: send messages, answer the poll, push a poll as the instructor, switch
instructor tabs (Dashboard / Questions / Live session / Upload content / Students).

---

## Architecture diagram

The full system architecture is in [`docs/architecture.mmd`](docs/architecture.mmd) (Mermaid).


## Project structure

```
src/
  App.jsx                  # view switcher + shell
  styles.css               # design system (colors, components)
  data/mock.js             # all illustrative data
  components/
    TopNav.jsx             # nav bar + Avatar + Brand
    Chat.jsx               # message bubbles, typing dots, composer, auto-scroll thread
    PollCard.jsx           # live poll with selectable options
    ResultBars.jsx         # horizontal bar chart of poll results
    ViewSwitcher.jsx       # bottom demo control
  views/
    StudentStudyView.jsx
    StudentLiveView.jsx
    InstructorConsoleView.jsx
docs/
  architecture.mmd         # Mermaid source
  architecture-link.txt    # editable mermaid.live link
```

## Tech (frontend)

React 18 + Vite. No UI framework — a hand-built CSS design system so the look is fully owned and
easy to tweak.

## Planned backend (not yet built)

FastAPI · Postgres + pgvector · Redis (cache + pub/sub) · LangGraph orchestration · Claude API for
grounded generation · WebSockets for live sessions · async ingestion worker for document
chunking/embedding. Recommended build order: auth + data model → upload & ingestion → single
grounded RAG answer → WebSockets/live sessions → polls & quizzes.
