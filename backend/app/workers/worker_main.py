from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import redis

from app.core.dependencies import get_storage_service
from app.db.session import AsyncSessionLocal
from app.execution.queue.broker import Broker
from app.workers.document_worker import DocumentWorker
from app.workers.processing_runtime import create_stage_registry


logger = logging.getLogger(__name__)

QUEUE_NAME = "document_processing"


async def run_worker() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    logger.info("Initializing document-processing worker...")

    stage_registry = create_stage_registry()
    storage_service = get_storage_service()

    worker = DocumentWorker(
        session_factory=AsyncSessionLocal,
        stage_registry=stage_registry,
        storage_service=storage_service,
    )

    broker = Broker()

    logger.info(
        "Document-processing worker ready. Queue: %s",
        QUEUE_NAME,
    )

    try:
        while True:
            try:
                payload = await asyncio.to_thread(
                    broker.consume,
                    QUEUE_NAME,
                    2,
                )
            except redis.exceptions.TimeoutError:
                continue

            if payload is None:
                continue

            try:
                job_id = UUID(payload)
            except ValueError:
                logger.error(
                    "Invalid processing job ID received: %s",
                    payload,
                )
                continue

            logger.info(
                "Dequeued processing job: %s",
                job_id,
            )

            result = await worker.run(job_id)

            logger.info(
                "Processing job completed: job_id=%s status=%s",
                result.job_id,
                result.status,
            )

    except asyncio.CancelledError:
        logger.info("Document-processing worker cancelled.")
        raise

    finally:
        logger.info("Document-processing worker stopped.")


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
