"""
app/processing/processor.py

Execution boundary for one document-processing job.

Architecture:

    ProcessingJobRunner
            |
            | job-scoped AsyncSession
            v
    DocumentProcessor
            |
            +--> StorageService
            |
            +--> ProcessingContext
            |
            v
    ProcessingPipeline
            |
            | session
            v
    ProcessingContext.to_result()


Responsibilities
----------------
- Validate the ProcessingJob.
- Validate the associated DocumentVersion.
- Download the immutable object-storage artifact.
- Materialize it as a temporary local file.
- Build the canonical ProcessingContext.
- Execute the pre-built ProcessingPipeline.
- Report processing progress through an optional callback.
- Finalize the ProcessingContext.
- Convert the context into a normalized result.
- Always clean up temporary files.

The processor does NOT:
- manage ProcessingJob database state
- update ProcessingJob status
- construct processing stages
- discover stages
- implement OCR
- implement extraction
- implement chunking
- implement embeddings
- implement indexing

Database session
----------------
The processor receives a job-scoped AsyncSession from
ProcessingJobRunner.

The session is passed through pipeline execution but is
NOT stored inside ProcessingContext.
"""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document_version import DocumentVersion
from app.db.models.processing_job import ProcessingJob
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import ProcessingPipeline
from app.storage.service import StorageService


logger = logging.getLogger(__name__)


# ============================================================================
# TYPES
# ============================================================================

ProgressCallback = Callable[
    [str | None, int, str],
    Awaitable[None],
]


class DocumentProcessor:
    """
    Execute one ProcessingJob through a pre-built ProcessingPipeline.

    ProcessingJobRunner owns job lifecycle and persistence.

    DocumentProcessor owns only:
        - artifact materialization
        - ProcessingContext creation
        - pipeline execution
        - progress reporting
        - result normalization
        - temporary-file cleanup

    The AsyncSession is supplied by ProcessingJobRunner and is
    scoped to the current processing execution.
    """

    def __init__(
        self,
        pipeline: ProcessingPipeline,
        storage_service: StorageService,
        session: AsyncSession,
        progress_callback: ProgressCallback | None = None,
    ) -> None:

        if pipeline is None:
            raise ValueError(
                "pipeline is required"
            )

        if storage_service is None:
            raise ValueError(
                "storage_service is required"
            )

        if session is None:
            raise ValueError(
                "session is required"
            )

        self.pipeline = pipeline
        self.storage_service = storage_service
        self.session = session
        self.progress_callback = progress_callback

    # ========================================================================
    # PROGRESS
    # ========================================================================

    async def _report_progress(
        self,
        stage_name: str | None,
        progress: int,
        status: str = "running",
    ) -> None:
        """
        Report progress to ProcessingJobRunner.

        Progress persistence failures must never fail document processing.

        Callback contract:

            callback(
                stage_name,
                progress,
                status,
            )
        """

        if self.progress_callback is None:
            return

        normalized_progress = max(
            0,
            min(
                100,
                int(progress),
            ),
        )

        normalized_status = (
            str(status)
            .strip()
            .lower()
        )

        try:

            await self.progress_callback(
                stage_name,
                normalized_progress,
                normalized_status,
            )

        except Exception:

            logger.exception(
                "Processing progress callback failed",
                extra={
                    "current_stage": stage_name,
                    "progress": normalized_progress,
                    "status": normalized_status,
                },
            )

    # ========================================================================
    # PROCESS
    # ========================================================================

    async def process(
        self,
        job: ProcessingJob,
    ) -> dict[str, Any]:

        if job is None:
            raise ValueError(
                "job is required"
            )

        logger.info(
            "Starting document processing",
            extra={
                "processing_job_id": str(
                    job.id
                ),
                "document_version_id": (
                    str(
                        job.document_version_id
                    )
                    if job.document_version_id is not None
                    else None
                ),
            },
        )

        await self._report_progress(
            stage_name=None,
            progress=0,
            status="running",
        )

        # ====================================================================
        # RESOLVE DOCUMENT VERSION
        # ====================================================================

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

        self._validate_document_version(
            document_version,
        )

        temporary_path: Path | None = None

        try:

            # ================================================================
            # MATERIALIZE IMMUTABLE OBJECT-STORAGE ARTIFACT
            # ================================================================

            temporary_path = self._materialize_document(
                document_version=document_version,
            )

            logger.info(
                "Document materialized for processing",
                extra={
                    "processing_job_id": str(
                        job.id
                    ),
                    "document_version_id": str(
                        document_version.id,
                    ),
                    "file_name": (
                        document_version.original_filename
                    ),
                    "file_size": (
                        document_version.file_size
                    ),
                },
            )

            # ================================================================
            # BUILD PROCESSING CONTEXT
            # ================================================================

            context = self._build_context(
                job=job,
                document_version=document_version,
                file_path=temporary_path,
            )

            logger.info(
                "Processing context created",
                extra={
                    "processing_job_id": str(
                        job.id
                    ),
                    "document_version_id": str(
                        document_version.id
                    ),
                    "document_id": context.document_id,
                },
            )

            # ================================================================
            # EXECUTE PROCESSING PIPELINE
            # ================================================================

            await self._report_progress(
                stage_name=None,
                progress=1,
                status="running",
            )

            try:

                context = await self.pipeline.execute(
                    context,
                    session=self.session,
                )

            except Exception:

                logger.exception(
                    "Document processing pipeline failed",
                    extra={
                        "processing_job_id": str(
                            job.id
                        ),
                        "document_version_id": str(
                            document_version.id
                        ),
                        "current_stage": (
                            context.current_stage
                        ),
                    },
                )

                raise

            # ================================================================
            # PIPELINE RETURNED
            # ================================================================

            final_stage = getattr(
                context,
                "current_stage",
                None,
            )

            logger.info(
                "Processing pipeline returned",
                extra={
                    "processing_job_id": str(
                        job.id
                    ),
                    "document_version_id": str(
                        document_version.id
                    ),
                    "current_stage": final_stage,
                    "status": context.status.value,
                },
            )

            # ================================================================
            # DEFENSIVE FINALIZATION
            # ================================================================

            if not context.is_completed:
                context.finish()

            # ================================================================
            # INSPECT FINAL PROCESSING STATE
            # ================================================================

            if context.is_failed:

                logger.error(
                    "Document processing completed with stage failures",
                    extra={
                        "processing_job_id": str(
                            job.id
                        ),
                        "document_version_id": str(
                            document_version.id
                        ),
                        "failed_stages": list(
                            context.failed_stages
                        ),
                        "error_count": len(
                            context.errors
                        ),
                        "duration_seconds": (
                            context.duration_seconds
                        ),
                    },
                )

                await self._report_progress(
                    stage_name=final_stage,
                    progress=100,
                    status="failed",
                )

            else:

                logger.info(
                    "Document processing completed successfully",
                    extra={
                        "processing_job_id": str(
                            job.id
                        ),
                        "document_version_id": str(
                            document_version.id
                        ),
                        "completed_stages": list(
                            context.completed_stages
                        ),
                        "duration_seconds": (
                            context.duration_seconds
                        ),
                    },
                )

                await self._report_progress(
                    stage_name=final_stage,
                    progress=100,
                    status="completed",
                )

            # ================================================================
            # NORMALIZE RESULT
            # ================================================================

            result = context.to_result()

            if not isinstance(
                result,
                dict,
            ):
                raise TypeError(
                    "ProcessingContext.to_result() must return "
                    "a dictionary."
                )

            return result

        finally:

            # ================================================================
            # ALWAYS CLEAN UP TEMPORARY FILE
            # ================================================================

            if temporary_path is not None:

                self._cleanup_temporary_file(
                    temporary_path,
                )

    # ========================================================================
    # VALIDATE DOCUMENT VERSION
    # ========================================================================

    @staticmethod
    def _validate_document_version(
        document_version: DocumentVersion,
    ) -> None:

        if document_version is None:
            raise ValueError(
                "document_version is required."
            )

        if document_version.document_id is None:
            raise ValueError(
                f"DocumentVersion {document_version.id} does not "
                "contain document_id."
            )

        if not document_version.original_filename:
            raise ValueError(
                f"DocumentVersion {document_version.id} does not "
                "contain original_filename."
            )

        if not document_version.object_storage_key:
            raise ValueError(
                f"DocumentVersion {document_version.id} does not "
                "contain object_storage_key."
            )

        if not document_version.object_storage_bucket:
            raise ValueError(
                f"DocumentVersion {document_version.id} does not "
                "contain object_storage_bucket."
            )

        if not document_version.storage_provider:
            raise ValueError(
                f"DocumentVersion {document_version.id} does not "
                "contain storage_provider."
            )

    # ========================================================================
    # MATERIALIZE DOCUMENT
    # ========================================================================

    def _materialize_document(
        self,
        document_version: DocumentVersion,
    ) -> Path:

        object_storage_key = (
            document_version.object_storage_key
        )

        object_storage_bucket = (
            document_version.object_storage_bucket
        )

        try:

            content = self.storage_service.download(
                key=object_storage_key,
            )

        except Exception as exc:

            logger.exception(
                "Failed to download document from object storage",
                extra={
                    "document_version_id": str(
                        document_version.id
                    ),
                    "storage_provider": (
                        document_version.storage_provider
                    ),
                    "object_storage_bucket": (
                        object_storage_bucket
                    ),
                    "object_storage_key": (
                        object_storage_key
                    ),
                },
            )

            raise RuntimeError(
                "Failed to download document from object storage."
            ) from exc

        if content is None:
            raise RuntimeError(
                "Object storage returned no document content."
            )

        if not isinstance(
            content,
            bytes,
        ):
            raise TypeError(
                "StorageService.download() must return bytes."
            )

        if not content:
            raise ValueError(
                "Downloaded document is empty."
            )

        suffix = Path(
            document_version.original_filename,
        ).suffix

        temporary_file = tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=suffix,
            prefix="enterprise_ai_",
            delete=False,
        )

        temporary_path = Path(
            temporary_file.name,
        )

        try:

            temporary_file.write(content)
            temporary_file.flush()

        except Exception:

            try:

                temporary_path.unlink(
                    missing_ok=True,
                )

            except OSError:

                logger.warning(
                    "Failed to remove incomplete temporary file %s",
                    temporary_path,
                    exc_info=True,
                )

            raise

        finally:

            temporary_file.close()

        if not temporary_path.is_file():

            raise FileNotFoundError(
                "Temporary document file was not created: "
                f"{temporary_path}"
            )

        try:

            actual_size = temporary_path.stat().st_size

        except OSError as exc:

            try:

                temporary_path.unlink(
                    missing_ok=True,
                )

            except OSError:

                logger.warning(
                    "Failed to remove temporary file after "
                    "stat failure: %s",
                    temporary_path,
                    exc_info=True,
                )

            raise RuntimeError(
                "Unable to inspect temporary document file."
            ) from exc

        if actual_size <= 0:

            try:

                temporary_path.unlink(
                    missing_ok=True,
                )

            except OSError:

                logger.warning(
                    "Failed to remove empty temporary file %s",
                    temporary_path,
                    exc_info=True,
                )

            raise ValueError(
                "Temporary document file is empty."
            )

        if (
            document_version.file_size is not None
            and document_version.file_size != actual_size
        ):

            logger.warning(
                "Downloaded document size differs from "
                "DocumentVersion.file_size",
                extra={
                    "document_version_id": str(
                        document_version.id
                    ),
                    "expected_size": (
                        document_version.file_size
                    ),
                    "actual_size": actual_size,
                },
            )

        logger.debug(
            "Document materialized successfully",
            extra={
                "document_version_id": str(
                    document_version.id
                ),
                "temporary_path": str(
                    temporary_path
                ),
                "actual_size": actual_size,
            },
        )

        return temporary_path

    # ========================================================================
    # BUILD CONTEXT
    # ========================================================================

    @staticmethod
    def _build_context(
        job: ProcessingJob,
        document_version: DocumentVersion,
        file_path: Path,
    ) -> ProcessingContext:

        if job is None:
            raise ValueError(
                "job is required to build ProcessingContext."
            )

        if document_version is None:
            raise ValueError(
                "document_version is required to build "
                "ProcessingContext."
            )

        if file_path is None:
            raise ValueError(
                "file_path is required to build ProcessingContext."
            )

        context = ProcessingContext(

            # ----------------------------------------------------------------
            # PROCESSING IDENTITY
            # ----------------------------------------------------------------

            job_id=str(
                job.id,
            ),

            # ----------------------------------------------------------------
            # DOCUMENT IDENTITY
            # ----------------------------------------------------------------

            document_id=str(
                document_version.document_id,
            ),

            document_version_id=str(
                document_version.id,
            ),

            # ----------------------------------------------------------------
            # MATERIALIZED ARTIFACT
            # ----------------------------------------------------------------

            file_path=str(
                file_path,
            ),

            file_name=document_version.original_filename,

            mime_type=document_version.mime_type,

            file_size=document_version.file_size,

            checksum=document_version.checksum,
        )

        # --------------------------------------------------------------------
        # PROCESSING JOB METADATA
        # --------------------------------------------------------------------

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

        # --------------------------------------------------------------------
        # OBJECT STORAGE METADATA
        # --------------------------------------------------------------------

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

        # --------------------------------------------------------------------
        # EXISTING DOCUMENT METADATA
        # --------------------------------------------------------------------

        existing_metadata = getattr(
            document_version,
            "metadata_",
            None,
        )

        if isinstance(
            existing_metadata,
            dict,
        ):

            context.metadata.update(
                existing_metadata,
            )

        # --------------------------------------------------------------------
        # EXISTING EXTRACTED DOCUMENT INFORMATION
        # --------------------------------------------------------------------

        if document_version.page_count is not None:

            context.metadata["page_count"] = (
                document_version.page_count
            )

        if document_version.detected_language is not None:

            context.metadata["detected_language"] = (
                document_version.detected_language
            )

        # --------------------------------------------------------------------
        # PROCESSING CONFIGURATION
        # --------------------------------------------------------------------

        job_config = getattr(
            job,
            "config",
            None,
        )

        if isinstance(
            job_config,
            dict,
        ):

            context.metadata["job_config"] = dict(
                job_config,
            )

        return context

    # ========================================================================
    # CLEANUP
    # ========================================================================

    @staticmethod
    def _cleanup_temporary_file(
        temporary_path: Path,
    ) -> None:

        try:

            temporary_path.unlink(
                missing_ok=True,
            )

            logger.debug(
                "Removed temporary processing file %s",
                temporary_path,
            )

        except Exception:

            logger.warning(
                "Failed to remove temporary processing file",
                exc_info=True,
            )


__all__ = [
    "DocumentProcessor",
]