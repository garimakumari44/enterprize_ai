
"""
app/workers/document_worker.py

Background worker for document-processing jobs.

Architecture:

    Queue / Background Task
            |
            v
    DocumentWorker
            |
            v
    ProcessingJobRunner
            |
            v
    DocumentProcessor
            |
            v
    StageRegistry
            |
            v
    Processing Pipeline
            |
            +--> classification
            +--> layout_analysis
            +--> text_extraction
            +--> ocr
            +--> structure_detection
            +--> cleaning
            +--> chunking
            +--> metadata_enrichment
            +--> embedding
            +--> indexing

Responsibilities
----------------

DocumentWorker is intentionally a thin execution adapter.

It is responsible for:

    - Receiving a ProcessingJob ID
    - Creating an independent database session
    - Providing StorageService
    - Delegating execution to ProcessingJobRunner
    - Returning a normalized WorkerResult
    - Logging worker-level failures

It does NOT:

    - Implement processing stages
    - Build the processing pipeline
    - Construct PipelineContext
    - Directly call DocumentProcessingPipeline
    - Manage individual ProcessingStep records
    - Duplicate ProcessingJob state transitions

Those responsibilities belong to:

    ProcessingJobRunner
        |
        +--> DocumentProcessor
        |
        +--> StageRegistry
        |
        +--> Processing Pipeline
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.constants import ProcessingStatus
from app.processing.job_runner import ProcessingJobRunner
from app.processing.stage_registry import StageRegistry
from app.storage.service import StorageService


logger = logging.getLogger(__name__)


# ============================================================================
# Worker Result
# ============================================================================


@dataclass(slots=True)
class WorkerResult:
    """
    Result returned by DocumentWorker after executing a processing job.

    The worker returns a lightweight result object instead of exposing
    SQLAlchemy session/model state to the caller.
    """

    job_id: UUID
    status: str
    document_version_id: UUID | None = None
    error: str | None = None
    result: dict[str, Any] | None = None


# ============================================================================
# Document Worker
# ============================================================================


class DocumentWorker:
    """
    Background worker for document-processing jobs.

    The worker owns the database-session boundary for background execution.

    Actual processing is delegated to ProcessingJobRunner.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        stage_registry: StageRegistry,
        storage_service: StorageService,
    ) -> None:
        self.session_factory = session_factory
        self.stage_registry = stage_registry
        self.storage_service = storage_service

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def run(
        self,
        job_id: UUID,
    ) -> WorkerResult:
        """
        Execute one processing job.

        Parameters
        ----------
        job_id:
            ID of the ProcessingJob to execute.

        Returns
        -------
        WorkerResult
            Normalized result describing the execution outcome.

        Notes
        -----
        A fresh database session is created for every worker execution.

        This is important because background workers should not reuse
        request-scoped AsyncSession instances.
        """

        logger.info(
            "Starting document worker",
            extra={
                "processing_job_id": str(job_id),
            },
        )

        async with self.session_factory() as session:

            runner = ProcessingJobRunner(
                db=session,
                stage_registry=self.stage_registry,
                storage_service=self.storage_service,
            )

            try:
                job = await runner.run(
                    job_id=job_id,
                )

            except Exception as exc:
                logger.exception(
                    "Document worker failed",
                    extra={
                        "processing_job_id": str(job_id),
                    },
                )

                return WorkerResult(
                    job_id=job_id,
                    status=ProcessingStatus.FAILED,
                    error=str(exc),
                )

            result = self._normalize_result(
                getattr(job, "result", None),
            )

            logger.info(
                "Document worker finished",
                extra={
                    "processing_job_id": str(job.id),
                    "status": str(job.status),
                    "document_version_id": str(
                        job.document_version_id,
                    ),
                },
            )

            return WorkerResult(
                job_id=job.id,
                status=str(job.status),
                document_version_id=job.document_version_id,
                result=result,
                error=getattr(
                    job,
                    "error_message",
                    None,
                ),
            )

    # ========================================================================
    # RUN QUEUED JOBS
    # ========================================================================

    async def run_pending_jobs(
        self,
    ) -> list[WorkerResult]:
        """
        Execute all currently queued processing jobs.

        This is useful for:

            - development workers
            - simple polling workers
            - scheduled jobs
            - local background processing

        For production queue infrastructure, the queue consumer should
        normally call `run(job_id)` for each dequeued job rather than
        repeatedly polling the database.
        """

        logger.info(
            "Starting pending document-job worker",
        )

        async with self.session_factory() as session:

            runner = ProcessingJobRunner(
                db=session,
                stage_registry=self.stage_registry,
                storage_service=self.storage_service,
            )

            try:
                jobs = await runner.run_pending_jobs()

            except Exception as exc:
                logger.exception(
                    "Pending document-job worker failed",
                    extra={
                        "error": str(exc),
                    },
                )

                return []

        results: list[WorkerResult] = []

        for job in jobs:

            results.append(
                WorkerResult(
                    job_id=job.id,
                    status=str(job.status),
                    document_version_id=job.document_version_id,
                    result=self._normalize_result(
                        getattr(
                            job,
                            "result",
                            None,
                        ),
                    ),
                    error=getattr(
                        job,
                        "error_message",
                        None,
                    ),
                )
            )

        logger.info(
            "Finished pending document jobs",
            extra={
                "processed_count": len(results),
            },
        )

        return results

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> dict[str, Any] | None:
        """
        Normalize a ProcessingJob result into a dictionary.

        ProcessingJob.result is currently JSONB-backed, so normally this
        should already be a dictionary. The additional handling keeps the
        worker defensive if a different result object is returned later.
        """

        if result is None:
            return None

        if isinstance(result, dict):
            return dict(result)

        if hasattr(result, "model_dump"):
            value = result.model_dump(
                mode="json",
            )

            if isinstance(value, dict):
                return value

        if hasattr(result, "dict"):
            value = result.dict()

            if isinstance(value, dict):
                return value

        if hasattr(result, "__dict__"):
            return {
                key: value
                for key, value in vars(result).items()
                if not key.startswith("_")
            }

        return {
            "result": result,
        }


__all__ = [
    "DocumentWorker",
    "WorkerResult",
]

