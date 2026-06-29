"""The async ingestion worker.

A standalone process that pulls document ids off the Redis queue and runs the pipeline,
so uploads return immediately while heavy work (parse/embed) happens out of band.

Run it alongside the API:

    python -m app.ingestion.worker
"""

from __future__ import annotations

import logging
import signal
import sys
import time

from app.db import SessionLocal
from app.ingestion.pipeline import process_document
from app.ingestion.queue import dequeue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("ingest.worker")

_running = True


def _stop(signum, _frame) -> None:
    global _running
    logger.info("Received signal %s, finishing current job then exiting", signum)
    _running = False


def run() -> None:
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    logger.info("Ingestion worker started; waiting for jobs…")

    while _running:
        try:
            document_id = dequeue(timeout=5)  # waits up to 5s, then loops (lets us check _running)
            if document_id is None:
                continue
            logger.info("Processing document %s", document_id)
            db = SessionLocal()
            try:
                process_document(db, document_id)
            finally:
                db.close()
        except Exception:  # noqa: BLE001 — a transient error must not kill the worker
            logger.exception("Worker loop error; continuing")
            time.sleep(1)

    logger.info("Ingestion worker stopped")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(0)
