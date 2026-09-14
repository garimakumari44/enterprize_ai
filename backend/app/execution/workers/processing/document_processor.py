"""
app/processing/processor.py

Execution boundary for one document-processing job.

Architecture:

    ProcessingJobRunner
            |
            v
    DocumentProcessor
            |
            v
    ProcessingContext
            |
            v
    ProcessingPipeline
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

DocumentProcessor:

    - Receive an already-loaded ProcessingJob
    - Resolve its DocumentVersion
    - Create the canonical ProcessingContext
    - Populate document/file metadata
    - Execute the ProcessingPipeline
    - Normalize the final ProcessingContext into a result

DocumentProcessor does NOT:

    - Construct pipelines
    - Register stages
    - Discover stages
    - Manage workers
    - Implement processing stages
    - Manage ProcessingJob database state

Those responsibilities belong to other layers.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from app.db.models.document import DocumentVersion
from app.db.models.processing_job import ProcessingJob
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import ProcessingPipeline



logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Execution boundary for one document-processing job.

    The processor converts a ProcessingJob + DocumentVersion into the
    canonical ProcessingContext consumed by the processing pipeline.
    """

    def __init__(
        self,
        pipeline: ProcessingPipeline,
    ) -> None:
        self.pipeline = pipeline

    # ==================================================================
    # PROCESS
    # ==================================================================

    async def process(
        self,
        job: ProcessingJob,
    ) -> dict[str, Any]:
        """
        Execute one ProcessingJob through the processing pipeline.

        Parameters
        ----------
        job:
            Already-loaded ProcessingJob. The runner is responsible for
            loading the associated DocumentVersion relationship.

        Returns
        -------
        dict[str, Any]
            Normalized result produced from ProcessingContext.
        """

        logger.info(
            "Starting document processing",
            extra={
                "processing_job_id": str(job.id),
                "document_version_id": str(
                    job.document_version_id,
                ),
            },
        )

        # --------------------------------------------------------------
        # Resolve DocumentVersion
        # --------------------------------------------------------------

        document_version = getattr(
            job,
            "document_version",
            None,
        )

        if document_version is None:
            raise ValueError(
                f"Processing job {job.id} does not have "
                "a loaded document_version."
            )

        # --------------------------------------------------------------
        # Build canonical ProcessingContext
        # --------------------------------------------------------------

        context = self._build_context(
            job=job,
            document_version=document_version,
        )

        logger.info(
            "Processing context created",
            extra={
                "processing_job_id": str(job.id),
                "document_id": context.document_id,
                "document_version_id": str(
                    job.document_version_id,
                ),
            },
        )

        # --------------------------------------------------------------
        # Execute processing pipeline
        # --------------------------------------------------------------

        try:
            context = await self.pipeline.execute(
                context,
            )

        except Exception as exc:
            logger.exception(
                "Document processing pipeline failed",
                extra={
                    "processing_job_id": str(job.id),
                    "document_version_id": str(
                        job.document_version_id,
                    ),
                    "current_stage": context.current_stage,
                    "error": str(exc),
                },
            )

            raise

        # --------------------------------------------------------------
        # Finalize context
        # --------------------------------------------------------------

        if not context.is_completed:
            context.finish()

        # --------------------------------------------------------------
        # Log stage failures
        # --------------------------------------------------------------

        if context.is_failed:
            logger.error(
                "Document processing completed with stage failures",
                extra={
                    "processing_job_id": str(job.id),
                    "failed_stages": list(
                        context.failed_stages,
                    ),
                    "errors": list(
                        context.errors,
                    ),
                },
            )

        else:
            logger.info(
                "Document processing completed successfully",
                extra={
                    "processing_job_id": str(job.id),
                    "completed_stages": list(
                        context.completed_stages,
                    ),
                    "duration_seconds": (
                        context.duration_seconds
                    ),
                },
            )

        # --------------------------------------------------------------
        # Return normalized pipeline result
        # --------------------------------------------------------------

        return context.to_result()

    # ==================================================================
    # BUILD CONTEXT
    # ==================================================================

    @staticmethod
    def _build_context(
        job: ProcessingJob,
        document_version: DocumentVersion,
    ) -> ProcessingContext:
        """
        Build the canonical ProcessingContext.

        DocumentVersion is the source of truth for uploaded-file
        identity and object-storage information.
        """

        context = ProcessingContext(
            document_id=str(
                document_version.document_id,
            ),
            file_name=document_version.original_filename,
            mime_type=document_version.mime_type,
            file_size=document_version.file_size,
            checksum=document_version.checksum,
        )

        # --------------------------------------------------------------
        # Processing job metadata
        # --------------------------------------------------------------

        context.metadata.update(
            {
                "processing_job_id": str(
                    job.id,
                ),
                "document_version_id": str(
                    document_version.id,
                ),
                "job_type": job.job_type,
                "version_number": (
                    document_version.version_number
                ),
            }
        )

        # --------------------------------------------------------------
        # Object-storage information
        # --------------------------------------------------------------

        context.metadata.update(
            {
                "storage_provider": (
                    document_version.storage_provider
                ),
                "object_storage_bucket": (
                    document_version.object_storage_bucket
                ),
                "object_storage_key": (
                    document_version.object_storage_key
                ),
            }
        )

        # --------------------------------------------------------------
        # Existing document metadata
        # --------------------------------------------------------------

        if isinstance(
            document_version.metadata_,
            dict,
        ):
            context.metadata.update(
                document_version.metadata_
            )

        # --------------------------------------------------------------
        # Existing extracted document information
        # --------------------------------------------------------------

        if document_version.page_count is not None:
            context.metadata["page_count"] = (
                document_version.page_count
            )

        if document_version.detected_language is not None:
            context.metadata["detected_language"] = (
                document_version.detected_language
            )

        # --------------------------------------------------------------
        # Processing configuration
        # --------------------------------------------------------------

        if isinstance(
            job.config,
            dict,
        ):
            context.metadata["job_config"] = dict(
                job.config,
            )

        # --------------------------------------------------------------
        # Storage note
        # --------------------------------------------------------------
        #
        # `ProcessingContext.file_path` intentionally remains None.
        #
        # DocumentVersion stores an object-storage reference, not a local
        # filesystem path. A storage/download stage can resolve the object
        # later and populate file_path if required by downstream stages.
        #

        return context


__all__ = [
    "DocumentProcessor",
]