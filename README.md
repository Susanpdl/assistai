# AssistAI — AI Classroom Interaction Platform

A polished **frontend UI/UX prototype** for an AI-assisted classroom platform. It gives every
student a personal teaching assistant grounded in their actual course material, and gives
professors a live window into how the whole room is doing.

> **Status:** Frontend prototype only. All data is mocked (`src/data/mock.js`) so the three
> experiences can be demoed end to end. The backend (FastAPI · Postgres/pgvector · Redis ·
> LangGraph · Claude API) is intentionally not built yet.

---

## Run it

```bash
npm install
npm run dev
```

Then open the URL Vite prints (e.g. `http://localhost:5173`). A **floating "Demo" switcher** at
the bottom of the screen lets you jump between the three views — perfect for a walkthrough.

Build a static version to host/share:

```bash
npm run build      # outputs to dist/
npm run preview    # serve the production build locally
```

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

## Architecture diagram (editable)

The full system architecture is in [`docs/architecture.mmd`](docs/architecture.mmd) (Mermaid).

- **Editable link (no account needed):** open `docs/architecture-link.txt` and paste the
  `mermaid.live/edit#...` URL into your browser. The entire diagram is encoded in the link, so you
  (or your professor) can edit it live and re-share.
- **Want editable Excalidraw shapes?** Go to <https://excalidraw.com>, open the command menu, choose
  **"Mermaid to Excalidraw"**, and paste the contents of `docs/architecture.mmd`. It converts the
  diagram into fully editable shapes on the canvas.

The diagram maps the five logical layers — Client (React) → API Gateway (FastAPI) → Realtime
(WebSockets + Redis pub/sub) → AI Subsystem (LangGraph + RAG + Claude) → Persistence
(Postgres/pgvector, Redis, object storage) — plus the async ingestion worker.

---

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
