"""FastAPI application entry point.

This is the Phase 0 skeleton: it wires CORS, exposes a liveness check (`/health`) and a
readiness check (`/health/ready`, which actually talks to Postgres and Redis). Feature
routers (auth, courses, tutor, ...) get mounted here in later phases.
"""

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth.router import router as auth_router
from app.config import settings
from app.db import engine

app = FastAPI(title="AssistAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
def health() -> dict:
    """Liveness: the process is up. No external dependencies touched."""
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> dict:
    """Readiness: can we actually reach Postgres and Redis? Reports each dependency."""
    checks = {"database": _check_database(), "redis": _check_redis()}
    ready = all(checks.values())
    return {"status": "ready" if ready else "degraded", "checks": checks}


def _check_database() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _check_redis() -> bool:
    try:
        client = redis.Redis.from_url(settings.redis_url)
        return bool(client.ping())
    except Exception:
        return False
