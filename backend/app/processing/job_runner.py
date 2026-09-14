"""
app/services/processing/processing_job_runner.py

Executes processing jobs and guarantees persistence of the canonical
DocumentIntelligenceResult.

Architecture
------------

New job:

    ProcessingJob
         |
         v
    StageRegistry
         |
         v
    ProcessingPipeline
         |
         v
    DocumentProcessor
         |
         v
    raw result
         |
         v
    canonical intelligence result
         |
         v
    IntelligenceResultService
         |
         v
    PostgreSQL


Completed legacy job:

    ProcessingJob.result
         |
         v
    legacy result mapper
         |
         v
    canonical intelligence result
         |
         v
    IntelligenceResultService
         |
         v
    PostgreSQL


Session lifecycle
-----------------

The runner owns the job-scoped AsyncSession.

The session is injected into DocumentProcessor and ultimately passed
to DB-dependent processing stages such as IndexingStage.

The ProcessingContext remains session-free.

The runner does NOT:

    - create another AsyncSession
    - store a global session
    - put AsyncSession into ProcessingContext
    - close the session

The caller that created the session remains responsible for its
overall lifecycle.
"""

from __future__ import annotations

import inspect
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.document_intelligence_result import (
    DocumentIntelligenceResult,
)
from app.db.models.processing_job import ProcessingJob
from app.services.processing.intelligence_result_service import (
    IntelligenceResultService,
)

logger = logging.getLogger(__name__)


class ProcessingJobRunner:
    """
    Runs processing jobs and persists canonical intelligence results.

    The runner is responsible for orchestration around DocumentProcessor.
    It does not implement individual processing stages itself.

    Processing architecture:

        StageRegistry
            |
            v
        ProcessingPipeline
            |
            v
        DocumentProcessor
            |
            v
        raw result
            |
            v
        canonical result
            |
            v
        IntelligenceResultService

    Database session architecture:

        ProcessingJobRunner
                |
                | job-scoped AsyncSession
                v
        DocumentProcessor
                |
                v
        ProcessingPipeline
                |
                v
        IndexingStage
                |
                v
        ProcessingIndexProvider
                |
                v
        VectorStoreManager
    """

    def __init__(
        self,
        db: AsyncSession,
        *,
        processor_factory: Any = None,
        stage_registry: Any = None,
        storage_service: Any = None,
    ) -> None:
        """
        Initialize the processing job runner.

        Args:
            db:
                Job-scoped Async SQLAlchemy session.

            processor_factory:
                Optional custom DocumentProcessor factory.

            stage_registry:
                StageRegistry responsible for constructing the canonical
                processing pipeline.

            storage_service:
                StorageService used by DocumentProcessor to download the
                source document.

        Important:
            The runner does not create or close the AsyncSession.
            The caller owns the session lifecycle.
        """

        self.db = db
        self.processor_factory = processor_factory
        self.stage_registry = stage_registry
        self.storage_service = storage_service

        self.intelligence_result_service = IntelligenceResultService(
            db
        )

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    async def run(
        self,
        job_id: UUID,
    ) -> ProcessingJob:
        """
        Execute a processing job.

        Already-completed jobs are not rerun.

        If a completed job is missing its canonical
        DocumentIntelligenceResult, the existing legacy
        ProcessingJob.result is backfilled.

        Returns:
            The current ProcessingJob after execution or recovery.
        """

        job = await self._load_job(job_id)

        if job is None:
            raise ValueError(
                f"Processing job {job_id} was not found."
            )

        status = self._status_value(job.status)

        logger.info(
            "Starting processing job | job_id=%s | status=%s",
            job.id,
            status,
        )

        # --------------------------------------------------------------
        # CANCELLED
        # --------------------------------------------------------------

        if status == "cancelled":
            logger.info(
                "Processing job already cancelled | job_id=%s",
                job.id,
            )

            return job

        # --------------------------------------------------------------
        # COMPLETED
        # --------------------------------------------------------------

        if status == "completed":
            existing = await self._get_intelligence_result(
                processing_id=job.id
            )

            if existing is not None:
                logger.info(
                    "Completed processing job already has intelligence "
                    "result | job_id=%s | result_id=%s",
                    job.id,
                    existing.id,
                )

                return job

            logger.warning(
                "Completed processing job is missing intelligence result; "
                "starting legacy-result backfill | job_id=%s",
                job.id,
            )

            await self._backfill_completed_job_intelligence(
                job=job
            )

            await self.db.refresh(job)

            return job

        # --------------------------------------------------------------
        # CLAIM JOB
        # --------------------------------------------------------------

        claimed = await self._claim_job(job)

        if not claimed:
            logger.info(
                "Processing job could not be claimed | job_id=%s",
                job.id,
            )

            await self.db.refresh(job)

            return job

        try:
            # ----------------------------------------------------------
            # BUILD PROCESSOR
            # ----------------------------------------------------------

            processor = await self._build_processor()

            # ----------------------------------------------------------
            # EXECUTE PIPELINE
            # ----------------------------------------------------------

            raw_result = await processor.process(
                job=job
            )

            logger.info(
                "Processing pipeline completed | job_id=%s",
                job.id,
            )

            # ----------------------------------------------------------
            # BUILD CANONICAL RESULT
            # ----------------------------------------------------------

            document_result = (
                self._build_document_intelligence_result(
                    job=job,
                    raw_result=raw_result,
                )
            )

            # ----------------------------------------------------------
            # VERIFY DOCUMENT VERSION
            # ----------------------------------------------------------

            document_version_id = getattr(
                job,
                "document_version_id",
                None,
            )

            if document_version_id is None:
                raise ValueError(
                    f"Processing job {job.id} has no "
                    "document_version_id."
                )

            # ----------------------------------------------------------
            # CHECK CANCELLATION
            # ----------------------------------------------------------

            await self.db.refresh(job)

            if self._status_value(job.status) == "cancelled":
                logger.info(
                    "Processing job was cancelled during execution | "
                    "job_id=%s",
                    job.id,
                )

                await self.db.rollback()

                return job

            # ----------------------------------------------------------
            # PERSIST CANONICAL RESULT
            # ----------------------------------------------------------

            persisted_result = (
                await self._persist_intelligence_result(
                    job=job,
                    document_result=document_result,
                )
            )

            logger.info(
                "Canonical intelligence result persisted | "
                "job_id=%s | result_id=%s",
                job.id,
                persisted_result.id,
            )

            # ----------------------------------------------------------
            # MARK JOB COMPLETED
            # ----------------------------------------------------------

            job.status = "completed"

            if hasattr(job, "progress"):
                job.progress = 100

            if hasattr(job, "completed_at"):
                job.completed_at = datetime.now(
                    timezone.utc
                )

            # Store the canonical result as the ProcessingJob result
            # if the model supports the result field.
            if hasattr(job, "result"):
                job.result = document_result

            # ----------------------------------------------------------
            # COMPLETE STEPS
            # ----------------------------------------------------------

            await self._complete_steps(job)

            # ----------------------------------------------------------
            # SINGLE FINAL COMMIT
            # ----------------------------------------------------------

            await self.db.commit()

            await self.db.refresh(job)

            logger.info(
                "Processing job completed successfully | "
                "job_id=%s | result_id=%s",
                job.id,
                persisted_result.id,
            )

            return job

        except Exception as exc:
            logger.exception(
                "Processing job failed | job_id=%s | error=%s",
                job.id,
                exc,
            )

            await self._persist_failure(
                job_id=job.id,
                error=exc,
            )

            raise

    # ==================================================================
    # ENSURE INTELLIGENCE RESULT
    # ==================================================================

    async def ensure_intelligence_result(
        self,
        job_id: UUID,
    ) -> DocumentIntelligenceResult | None:
        """
        Ensure a completed processing job has a canonical intelligence
        result.

        This is safe to call from an API endpoint or recovery path.

        It does not rerun processing.

        Returns:
            DocumentIntelligenceResult if available.
            None if the job is not completed yet.
        """

        job = await self._load_job(job_id)

        if job is None:
            raise ValueError(
                f"Processing job {job_id} was not found."
            )

        existing = await self._get_intelligence_result(
            processing_id=job.id
        )

        if existing is not None:
            return existing

        status = self._status_value(job.status)

        if status != "completed":
            return None

        logger.warning(
            "Ensuring missing intelligence result for completed job | "
            "job_id=%s",
            job.id,
        )

        await self._backfill_completed_job_intelligence(
            job=job
        )

        return await self._get_intelligence_result(
            processing_id=job.id
        )

    # ==================================================================
    # BACKFILL
    # ==================================================================

    async def _backfill_completed_job_intelligence(
        self,
        *,
        job: ProcessingJob,
    ) -> DocumentIntelligenceResult:
        """
        Backfill DocumentIntelligenceResult from the existing
        ProcessingJob.result.

        IMPORTANT:
            This does NOT rerun the processing pipeline.
        """

        existing = await self._get_intelligence_result(
            processing_id=job.id
        )

        if existing is not None:
            return existing

        legacy_result = getattr(
            job,
            "result",
            None,
        )

        if not isinstance(
            legacy_result,
            dict,
        ):
            raise ValueError(
                "Cannot backfill intelligence result because "
                f"processing job {job.id} has no usable result object."
            )

        logger.info(
            "Backfilling intelligence result from legacy processing "
            "result | job_id=%s",
            job.id,
        )

        document_result = (
            self._build_document_intelligence_result(
                job=job,
                raw_result=legacy_result,
            )
        )

        persisted_result = (
            await self._persist_intelligence_result(
                job=job,
                document_result=document_result,
            )
        )

        await self.db.commit()

        await self.db.refresh(
            persisted_result
        )

        logger.info(
            "Legacy intelligence result backfilled successfully | "
            "job_id=%s | result_id=%s",
            job.id,
            persisted_result.id,
        )

        return persisted_result

    # ==================================================================
    # RESULT BUILDING
    # ==================================================================

    def _build_document_intelligence_result(
        self,
        *,
        job: ProcessingJob,
        raw_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert either a modern pipeline result or the legacy
        ProcessingJob.result into the canonical intelligence result
        representation expected by the persistence layer.
        """

        if not isinstance(
            raw_result,
            dict,
        ):
            raw_result = {}

        document_id = self._first_value(
            raw_result.get("document_id"),
            getattr(
                job,
                "document_id",
                None,
            ),
        )

        document_version_id = self._first_value(
            raw_result.get("document_version_id"),
            getattr(
                job,
                "document_version_id",
                None,
            ),
        )

        document_type = self._first_value(
            raw_result.get("document_type"),
            self._nested_value(
                raw_result,
                "classification",
                "document_type",
            ),
        )

        classification_confidence = self._first_value(
            raw_result.get("classification_confidence"),
            self._nested_value(
                raw_result,
                "classification",
                "confidence",
            ),
        )

        stage_results = raw_result.get(
            "stage_results",
            {},
        )

        if not isinstance(
            stage_results,
            dict,
        ):
            stage_results = {}

        # --------------------------------------------------------------
        # Canonical stage mapping
        # --------------------------------------------------------------

        text_extraction = self._first_mapping(
            raw_result.get("text_extraction"),
            stage_results.get("text_extraction"),
            stage_results.get("extraction"),
        )

        ocr = self._first_mapping(
            raw_result.get("ocr"),
            stage_results.get("ocr"),
        )

        classification = self._first_mapping(
            raw_result.get("classification"),
            stage_results.get("classification"),
        )

        layout = self._first_mapping(
            raw_result.get("layout"),
            stage_results.get("layout_analysis"),
        )

        structure = self._first_mapping(
            raw_result.get("structure"),
            stage_results.get("structure_detection"),
        )

        cleaning = self._first_mapping(
            raw_result.get("cleaning"),
            stage_results.get("cleaning"),
        )

        chunking = self._first_mapping(
            raw_result.get("chunking"),
            stage_results.get("chunking"),
        )

        metadata_enrichment = self._first_mapping(
            raw_result.get("metadata_enrichment"),
            stage_results.get("metadata_enrichment"),
        )

        embedding = self._first_mapping(
            raw_result.get("embedding"),
            stage_results.get("embedding"),
        )

        indexing = self._first_mapping(
            raw_result.get("indexing"),
            raw_result.get("indexing_result"),
            stage_results.get("indexing"),
        )

        # --------------------------------------------------------------
        # Chunks
        # --------------------------------------------------------------

        chunks = raw_result.get(
            "chunks"
        )

        if chunks is None:
            chunks = self._extract_from_stage(
                stage_results.get("chunking"),
                "chunks",
            )

        if chunks is None:
            chunks = []

        # --------------------------------------------------------------
        # Raw / cleaned text
        # --------------------------------------------------------------

        raw_text = self._first_value(
            raw_result.get("raw_text"),
            self._extract_from_stage(
                text_extraction,
                "raw_text",
            ),
            self._extract_from_stage(
                text_extraction,
                "text",
            ),
        )

        cleaned_text = self._first_value(
            raw_result.get("cleaned_text"),
            self._extract_from_stage(
                cleaning,
                "cleaned_text",
            ),
            self._extract_from_stage(
                cleaning,
                "text",
            ),
        )

        # --------------------------------------------------------------
        # Structured data
        # --------------------------------------------------------------

        extracted_data = raw_result.get(
            "extracted_data",
            {},
        )

        if not isinstance(
            extracted_data,
            dict,
        ):
            extracted_data = {}

        structured_data = self._build_structured_data(
            raw_result=raw_result,
            extracted_data=extracted_data,
        )

        # --------------------------------------------------------------
        # Validation
        # --------------------------------------------------------------

        validation_results = (
            self._build_validation_results(
                raw_result
            )
        )

        # --------------------------------------------------------------
        # Artifacts
        # --------------------------------------------------------------

        artifacts = self._build_artifacts(
            raw_result
        )

        # --------------------------------------------------------------
        # Knowledge
        # --------------------------------------------------------------

        knowledge = self._build_knowledge(
            raw_result
        )

        # --------------------------------------------------------------
        # Canonical result
        # --------------------------------------------------------------

        canonical = {
            "document": {
                "id": (
                    str(document_id)
                    if document_id is not None
                    else None
                ),
                "version_id": (
                    str(document_version_id)
                    if document_version_id is not None
                    else None
                ),
                "file_name": raw_result.get(
                    "file_name"
                ),
                "mime_type": raw_result.get(
                    "mime_type"
                ),
            },

            "schema_version": "1.0",

            "status": self._first_value(
                raw_result.get("status"),
                "completed",
            ),

            "stages": {
                "text_extraction": text_extraction,
                "ocr": ocr,
                "classification": classification,
                "layout_analysis": layout,
                "structure_detection": structure,
                "cleaning": cleaning,
                "chunking": chunking,
                "metadata_enrichment": metadata_enrichment,
                "embedding": embedding,
                "indexing": indexing,
            },

            "classification": classification,

            "layout": layout,

            "text_extraction": text_extraction,

            "structure": structure,

            "cleaned_text": cleaned_text,

            "chunks": chunks,

            "metadata": (
                raw_result.get("metadata")
                if isinstance(
                    raw_result.get("metadata"),
                    dict,
                )
                else {}
            ),

            "embeddings": embedding,

            "indexing": indexing,

            "document_type": document_type,

            "classification_confidence": (
                classification_confidence
            ),

            "structured_data": structured_data,

            "validation_results": validation_results,

            "artifacts": artifacts,

            "knowledge": knowledge,

            "raw_text": raw_text,

            "execution": {
                "job_id": str(job.id),

                "status": raw_result.get(
                    "status",
                    "completed",
                ),

                "success": raw_result.get(
                    "success",
                    True,
                ),

                "chunk_count": raw_result.get(
                    "chunk_count"
                ),

                "embedding_count": raw_result.get(
                    "embedding_count"
                ),

                "embedding_dimension": raw_result.get(
                    "embedding_dimension"
                ),

                "enriched_chunk_count": raw_result.get(
                    "enriched_chunk_count"
                ),

                "duration_seconds": raw_result.get(
                    "duration_seconds"
                ),

                "completed_stages": raw_result.get(
                    "completed_stages",
                    [],
                ),

                "failed_stages": raw_result.get(
                    "failed_stages",
                    [],
                ),

                "skipped_stages": raw_result.get(
                    "skipped_stages",
                    [],
                ),

                "cancelled_stages": raw_result.get(
                    "cancelled_stages",
                    [],
                ),
            },
        }

        return canonical

    # ==================================================================
    # STRUCTURED DATA
    # ==================================================================

    def _build_structured_data(
        self,
        *,
        raw_result: dict[str, Any],
        extracted_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build the JSONB structured_data field.

        extracted_data is the primary source.

        We deliberately do not put large operational fields such as
        raw_text, artifacts, knowledge, or validation results inside
        structured_data.
        """

        structured_data = dict(
            extracted_data
        )

        if raw_result.get(
            "document_subtype"
        ) is not None:
            structured_data.setdefault(
                "document_subtype",
                raw_result.get(
                    "document_subtype"
                ),
            )

        return self._json_safe(
            structured_data
        )

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def _build_validation_results(
        self,
        raw_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize validation information from legacy or modern results.
        """

        value = raw_result.get(
            "validation_results"
        )

        if isinstance(
            value,
            dict,
        ):
            return self._json_safe(
                value
            )

        if isinstance(
            value,
            list,
        ):
            return {
                "items": self._json_safe(
                    value
                )
            }

        errors = raw_result.get(
            "errors"
        )

        warnings = raw_result.get(
            "warnings"
        )

        return self._json_safe(
            {
                "errors": (
                    errors
                    if errors is not None
                    else []
                ),
                "warnings": (
                    warnings
                    if warnings is not None
                    else []
                ),
            }
        )

    # ==================================================================
    # ARTIFACTS
    # ==================================================================

    def _build_artifacts(
        self,
        raw_result: dict[str, Any],
    ) -> list[Any]:
        """
        Normalize artifacts.
        """

        artifacts = raw_result.get(
            "artifacts"
        )

        if artifacts is None:
            artifacts = []

        if isinstance(
            artifacts,
            list,
        ):
            return self._json_safe(
                artifacts
            )

        return self._json_safe(
            [artifacts]
        )

    # ==================================================================
    # KNOWLEDGE
    # ==================================================================

    def _build_knowledge(
        self,
        raw_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize knowledge/indexing information.
        """

        knowledge = raw_result.get(
            "knowledge"
        )

        if isinstance(
            knowledge,
            dict,
        ):
            return self._json_safe(
                knowledge
            )

        indexing_result = raw_result.get(
            "indexing_result"
        )

        if isinstance(
            indexing_result,
            dict,
        ):
            return self._json_safe(
                {
                    "indexing": indexing_result,
                }
            )

        return {}

    # ==================================================================
    # PERSISTENCE
    # ==================================================================

    async def _persist_intelligence_result(
        self,
        *,
        job: ProcessingJob,
        document_result: dict[str, Any],
    ) -> DocumentIntelligenceResult:
        """
        Persist canonical intelligence result.

        IntelligenceResultService is responsible for persistence.
        """

        existing = await self._get_intelligence_result(
            processing_id=job.id
        )

        document_id = self._uuid_or_none(
            self._first_value(
                self._nested_value(
                    document_result,
                    "document",
                    "id",
                ),
                getattr(
                    job,
                    "document_id",
                    None,
                ),
            )
        )

        document_version_id = self._uuid_or_none(
            self._first_value(
                self._nested_value(
                    document_result,
                    "document",
                    "version_id",
                ),
                getattr(
                    job,
                    "document_version_id",
                    None,
                ),
            )
        )

        if document_id is None:
            raise ValueError(
                f"Cannot persist intelligence result for job {job.id}: "
                "document_id is missing."
            )

        if document_version_id is None:
            raise ValueError(
                f"Cannot persist intelligence result for job {job.id}: "
                "document_version_id is missing."
            )

        document_type = document_result.get(
            "document_type"
        )

        confidence = document_result.get(
            "classification_confidence"
        )

        structured_data = document_result.get(
            "structured_data",
            {},
        )

        validation_results = document_result.get(
            "validation_results",
            {},
        )

        artifacts = document_result.get(
            "artifacts",
            [],
        )

        knowledge = document_result.get(
            "knowledge",
            {},
        )

        raw_text = document_result.get(
            "raw_text"
        )

        if existing is not None:
            logger.info(
                "Updating existing intelligence result | "
                "job_id=%s | result_id=%s",
                job.id,
                existing.id,
            )

        return await self.intelligence_result_service.create_result(
            processing_id=job.id,
            document_id=document_id,
            document_version_id=document_version_id,
            document_type=document_type,
            classification_confidence=confidence,
            structured_data=structured_data,
            validation_results=validation_results,
            artifacts=artifacts,
            knowledge=knowledge,
            raw_text=raw_text,
        )

    # ==================================================================
    # DATABASE
    # ==================================================================

    async def _load_job(
        self,
        job_id: UUID,
    ) -> ProcessingJob | None:
        """
        Load a processing job together with the relationships required
        by DocumentProcessor and the runner.

        DocumentProcessor.process() requires job.document_version to be
        available, so it must be eagerly loaded here.

        Processing steps are also eagerly loaded because the runner
        completes them after successful execution.
        """

        stmt = (
            select(ProcessingJob)
            .where(
                ProcessingJob.id == job_id
            )
            .options(
                selectinload(
                    ProcessingJob.document_version
                ),
                selectinload(
                    ProcessingJob.steps
                ),
            )
        )

        result = await self.db.execute(
            stmt
        )

        return result.scalar_one_or_none()

    async def _get_intelligence_result(
        self,
        *,
        processing_id: UUID,
    ) -> DocumentIntelligenceResult | None:
        return (
            await self.intelligence_result_service
            .get_by_processing_id(
                processing_id
            )
        )

    # ==================================================================
    # JOB CLAIM
    # ==================================================================

    async def _claim_job(
        self,
        job: ProcessingJob,
    ) -> bool:
        """
        Claim the job for processing.
        """

        status = self._status_value(
            job.status
        )

        if status in {
            "running",
            "processing",
        }:
            logger.info(
                "Job is already running | job_id=%s",
                job.id,
            )

            return False

        if status in {
            "completed",
            "failed",
            "cancelled",
        }:
            return False

        job.status = "processing"

        if hasattr(
            job,
            "progress",
        ):
            job.progress = 0

        if hasattr(
            job,
            "started_at",
        ):
            job.started_at = datetime.now(
                timezone.utc
            )

        await self.db.flush()

        return True

    # ==================================================================
    # PIPELINE
    # ==================================================================

    def _build_pipeline(self) -> Any:
        """
        Build the canonical ProcessingPipeline from StageRegistry.

        StageRegistry is the single source of truth for:

        - registered stages
        - canonical stage ordering
        - stage validation
        - stage resolution
        - pipeline construction

        The runner deliberately does not duplicate the canonical
        ProcessingStage list.
        """

        if self.stage_registry is None:
            raise RuntimeError(
                "StageRegistry is required to build the "
                "processing pipeline."
            )

        # StageRegistry owns canonical pipeline construction.
        build_canonical_pipeline = getattr(
            self.stage_registry,
            "build_canonical_pipeline",
            None,
        )

        if not callable(
            build_canonical_pipeline
        ):
            raise RuntimeError(
                "StageRegistry does not expose "
                "build_canonical_pipeline()."
            )

        pipeline = build_canonical_pipeline(
            fail_fast=True,
        )

        if pipeline is None:
            raise RuntimeError(
                "StageRegistry returned no processing pipeline."
            )

        logger.info(
            "Canonical processing pipeline built successfully | "
            "stages=%s",
            getattr(
                self.stage_registry,
                "pipeline_stages",
                lambda: (),
            )(),
        )

        return pipeline

    # ==================================================================
    # PROCESSOR
    # ==================================================================

    async def _build_processor(self) -> Any:
        """
        Build the DocumentProcessor.

        IMPORTANT:

        DocumentProcessor receives the job-scoped AsyncSession from
        this runner.

        The session is NOT stored in ProcessingContext.

        Expected constructor:

            DocumentProcessor(
                pipeline=...,
                storage_service=...,
                session=self.db,
                progress_callback=...,
            )
        """

        if self.storage_service is None:
            raise RuntimeError(
                "StorageService is required to build "
                "DocumentProcessor."
            )

        pipeline = self._build_pipeline()

        # --------------------------------------------------------------
        # CUSTOM PROCESSOR FACTORY
        # --------------------------------------------------------------

        if self.processor_factory is not None:
            processor_factory = (
                self.processor_factory
            )

            if not callable(
                processor_factory
            ):
                raise RuntimeError(
                    "Invalid processor_factory configured."
                )

            # ----------------------------------------------------------
            # Pass the job-scoped AsyncSession to custom processors.
            #
            # The compatibility check allows an older custom factory
            # without a session parameter to continue working.
            # ----------------------------------------------------------

            factory_kwargs = {
                "pipeline": pipeline,
                "storage_service": self.storage_service,
            }

            try:
                signature = inspect.signature(
                    processor_factory
                )

                if "session" in signature.parameters:
                    factory_kwargs["session"] = self.db

            except (
                TypeError,
                ValueError,
            ):
                # If the callable does not expose an inspectable
                # signature, use the modern session-aware contract.
                factory_kwargs["session"] = self.db

            return processor_factory(
                **factory_kwargs
            )

        # --------------------------------------------------------------
        # DEFAULT DOCUMENT PROCESSOR
        # --------------------------------------------------------------

        from app.processing.processor import (
            DocumentProcessor,
        )

        return DocumentProcessor(
            pipeline=pipeline,
            storage_service=self.storage_service,
            session=self.db,
        )

    # ==================================================================
    # STEPS
    # ==================================================================

    async def _complete_steps(
        self,
        job: ProcessingJob,
    ) -> None:
        """
        Mark processing steps complete if the model supports workflow
        step tracking.

        This method intentionally tolerates projects where ProcessingJob
        does not expose a steps relationship.
        """

        steps = getattr(
            job,
            "steps",
            None,
        )

        if not steps:
            return

        for step in steps:
            if hasattr(
                step,
                "status",
            ):
                step.status = "completed"

            if hasattr(
                step,
                "progress",
            ):
                step.progress = 100

            if hasattr(
                step,
                "completed_at",
            ):
                step.completed_at = datetime.now(
                    timezone.utc
                )

    # ==================================================================
    # FAILURE
    # ==================================================================

    async def _persist_failure(
        self,
        *,
        job_id: UUID,
        error: Exception,
    ) -> None:
        """
        Persist processing failure state.
        """

        await self.db.rollback()

        job = await self._load_job(
            job_id
        )

        if job is None:
            return

        job.status = "failed"

        if hasattr(
            job,
            "progress",
        ):
            job.progress = 0

        if hasattr(
            job,
            "error_code",
        ):
            job.error_code = type(
                error
            ).__name__

        if hasattr(
            job,
            "error_message",
        ):
            job.error_message = str(
                error
            )

        if hasattr(
            job,
            "completed_at",
        ):
            job.completed_at = datetime.now(
                timezone.utc
            )

        try:
            await self.db.commit()

            await self.db.refresh(
                job
            )

        except Exception:
            logger.exception(
                "Failed to persist processing failure | job_id=%s",
                job_id,
            )

            await self.db.rollback()

    # ==================================================================
    # STATUS
    # ==================================================================

    @staticmethod
    def _status_value(
        status: Any,
    ) -> str:
        """
        Normalize enum/string status values.
        """

        if status is None:
            return ""

        value = getattr(
            status,
            "value",
            status,
        )

        return str(
            value
        ).strip().lower()

    # ==================================================================
    # VALUE HELPERS
    # ==================================================================

    @staticmethod
    def _first_value(
        *values: Any,
    ) -> Any:
        """
        Return the first non-None value.
        """

        for value in values:
            if value is not None:
                return value

        return None

    @staticmethod
    def _first_mapping(
        *values: Any,
    ) -> dict[str, Any]:
        """
        Return the first dictionary value.
        """

        for value in values:
            if isinstance(
                value,
                dict,
            ):
                return value

        return {}

    @staticmethod
    def _nested_value(
        value: Any,
        *keys: str,
    ) -> Any:
        """
        Safely retrieve a nested dictionary value.
        """

        current = value

        for key in keys:
            if not isinstance(
                current,
                dict,
            ):
                return None

            current = current.get(
                key
            )

        return current

    @staticmethod
    def _extract_from_stage(
        stage: Any,
        key: str,
    ) -> Any:
        """
        Safely extract a field from a stage result.
        """

        if not isinstance(
            stage,
            dict,
        ):
            return None

        return stage.get(
            key
        )

    @staticmethod
    def _uuid_or_none(
        value: Any,
    ) -> UUID | None:
        """
        Convert a value into UUID if possible.
        """

        if value is None:
            return None

        if isinstance(
            value,
            UUID,
        ):
            return value

        try:
            return UUID(
                str(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    # ==================================================================
    # JSON NORMALIZATION
    # ==================================================================

    @classmethod
    def _json_safe(
        cls,
        value: Any,
    ) -> Any:
        """
        Recursively normalize values before storing them in JSONB.

        Handles:

        - UUID
        - datetime
        - NaN
        - infinity
        - sets
        - tuples
        - mappings
        """

        import math

        if value is None:
            return None

        if isinstance(
            value,
            UUID,
        ):
            return str(
                value
            )

        if isinstance(
            value,
            datetime,
        ):
            return value.isoformat()

        if isinstance(
            value,
            float,
        ):
            if not math.isfinite(
                value
            ):
                return None

            return value

        if isinstance(
            value,
            dict,
        ):
            return {
                str(key): cls._json_safe(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):
            return [
                cls._json_safe(
                    item
                )
                for item in value
            ]

        if isinstance(
            value,
            (
                str,
                int,
                bool,
            ),
        ):
            return value

        try:
            return str(
                value
            )
        except Exception:
            return None


__all__ = [
    "ProcessingJobRunner",
]