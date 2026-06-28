"""Phase 0 smoke test: the app boots and the liveness endpoint responds.

Liveness is dependency-free on purpose, so this test runs without Postgres or Redis.
The readiness endpoint (`/health/ready`) is exercised manually / in integration once
the docker-compose stack is up.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_liveness():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
