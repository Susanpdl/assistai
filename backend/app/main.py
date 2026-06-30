"""FastAPI application entry point.

This is the Phase 0 skeleton: it wires CORS, exposes a liveness check (`/health`) and a
readiness check (`/health/ready`, which actually talks to Postgres and Redis). Feature
routers (auth, courses, tutor, ...) get mounted here in later phases.
"""

from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.announcements.router import router as announcements_router
from app.attendance.router import router as attendance_router
from app.auth.router import router as auth_router
from app.config import settings
from app.content.router import router as content_router
from app.courses.router import router as courses_router
from app.dashboard.router import router as dashboard_router
from app.db import engine
from app.live.manager import manager
from app.live.router import router as live_router
from app.live.ws import router as live_ws_router
from app.tutor.router import router as tutor_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Start the realtime pub/sub subscriber so WebSocket rooms receive published messages.
    manager.start()
    await manager.wait_ready()
    yield
    await manager.stop()


app = FastAPI(title="AssistAI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(content_router)
app.include_router(tutor_router)
app.include_router(live_router)
app.include_router(live_ws_router)
app.include_router(attendance_router)
app.include_router(announcements_router)
app.include_router(dashboard_router)


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
