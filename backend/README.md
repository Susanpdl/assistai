# AssistAI — Backend

FastAPI API gateway, Postgres + pgvector persistence, and Redis for cache/realtime.
This is the **Phase 0** foundation (see [`../docs/03-development-plan.md`](../docs/03-development-plan.md)):
a runnable app skeleton with the full data model and migrations in place. Feature logic
(auth, courses, tutor, ...) lands in later phases.

## Stack

| Concern | Choice |
|---------|--------|
| API | FastAPI (async) |
| ORM / migrations | SQLAlchemy 2.0 + Alembic |
| Database | Postgres 16 + pgvector |
| Cache / realtime | Redis 7 |
| Tooling | uv (packaging), ruff (lint), pytest |

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker + Docker Compose (for Postgres and Redis)

## Quick start

```bash
cd backend

# 1. Install dependencies into a local .venv
uv sync

# 2. Configure environment (defaults match docker-compose)
cp .env.example .env

# 3. Start Postgres (pgvector) + Redis
docker compose up -d

# 4. Create the schema
uv run alembic upgrade head

# 5. Run the API (http://localhost:8000, docs at /docs)
# `--host ::` binds IPv6 localhost — the Vite dev server and browser use IPv6 for
# `localhost`, so the API must listen there too or the frontend's calls never arrive.
uv run uvicorn app.main:app --reload --host ::

# 6. (Phase 3+) Run the ingestion worker in a second terminal so uploaded course
# files get extracted, chunked, embedded, and indexed into pgvector.
uv run python -m app.ingestion.worker
```

Check it's alive:

```bash
curl localhost:8000/health        # {"status":"ok"}
curl localhost:8000/health/ready  # {"status":"ready","checks":{"database":true,"redis":true}}
```

## Project layout

```
backend/
  app/
    main.py            FastAPI app + health endpoints
    config.py          settings (env-driven)
    db.py              engine + session dependency
    storage.py         object-storage seam (local-disk backend; S3 later)
    models/            SQLAlchemy models (one file per domain area)
    auth/ courses/ content/ tutor/ live/   feature routers (router + schemas + deps)
    ingestion/         extract → chunk → embed → store pipeline + Redis queue + worker
    tutor/             RAG: retrieval + generation seam + guardrails + orchestrator
    live/              WebSocket rooms + Redis pub/sub manager + poll push/aggregate
  migrations/          Alembic (env.py + versions/)
  tests/               pytest
  storage/             uploaded course files (local backend; gitignored)
  docker-compose.yml   Postgres (pgvector) + Redis
```

## Common commands

```bash
uv run pytest                                   # tests
uv run ruff check .                             # lint
uv run alembic revision --autogenerate -m "..." # new migration after model changes
uv run alembic upgrade head                     # apply migrations
docker compose down                             # stop infra (add -v to wipe data)
```
