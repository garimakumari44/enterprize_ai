"""
app/processing/pipeline/result.py

Normalized immutable public result of a document-processing execution.

Architecture:

    ProcessingContext
            |
            v
    ProcessingResult
            |
            +--> ResultMapper
            +--> API
            +--> persistence
            +--> observability

ProcessingResult contains execution output only.
It does not execute processing and does not modify ProcessingContext.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.processing.pipeline.context import (
    ProcessingContext,
    StageExecution,
)


@dataclass(frozen=True)
class ProcessingResult:
    """
    Immutable snapshot of a completed processing execution.

    The internal ProcessingContext remains mutable while processing.
    Once converted to ProcessingResult, the result becomes a stable
    representation of that execution.
    """

    # ==================================================================
    # Identity
    # ==================================================================

    document_id: str

    success: bool

    processing_job_id: str | None = None

    document_version_id: str | None = None

    # ==================================================================
    # Document information
    # ==================================================================

    file_name: str | None = None

    mime_type: str | None = None

    file_size: int | None = None

    checksum: str | None = None

    # ==================================================================
    # Classification
    # ==================================================================

    document_type: str | None = None

    document_subtype: str | None = None

    classification_confidence: float | None = None

    # ==================================================================
    # Content
    # ==================================================================

    raw_text: str | None = None

    cleaned_text: str | None = None

    # ==================================================================
    # Structured information
    # ==================================================================

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    extracted_data: dict[str, Any] = field(
        default_factory=dict,
    )

    # ==================================================================
    # Artifact statistics
    # ==================================================================

    chunk_count: int = 0

    enriched_chunk_count: int = 0

    embedding_count: int = 0

    indexing_result: Any | None = None

    # ==================================================================
    # Execution state
    # ==================================================================

    current_stage: str | None = None

    completed_stages: tuple[str, ...] = ()

    failed_stages: tuple[str, ...] = ()

    skipped_stages: tuple[str, ...] = ()

    # ==================================================================
    # Stage execution history
    # ==================================================================

    stage_executions: tuple[
        StageExecution,
        ...
    ] = ()

    # ==================================================================
    # Diagnostics
    # ==================================================================

    stage_results: dict[str, Any] = field(
        default_factory=dict,
    )

    errors: tuple[str, ...] = ()

    warnings: tuple[str, ...] = ()

    # ==================================================================
    # Lifecycle
    # ==================================================================

    started_at: datetime | None = None

    completed_at: datetime | None = None

    cancelled_at: datetime | None = None

    cancelled: bool = False

    duration_seconds: float | None = None

    # ==================================================================
    # Construction
    # ==================================================================

    @classmethod
    def from_context(
        cls,
        context: ProcessingContext,
    ) -> ProcessingResult:
        """
        Create an immutable result snapshot from ProcessingContext.
        """

        if not isinstance(
            context,
            ProcessingContext,
        ):
            raise TypeError(
                "ProcessingResult.from_context() requires "
                "a ProcessingContext.",
            )

        return cls(
            document_id=context.document_id,

            success=context.is_successful,

            processing_job_id=(
                context.processing_job_id
            ),

            document_version_id=(
                context.document_version_id
            ),

            file_name=context.file_name,

            mime_type=context.mime_type,

            file_size=context.file_size,

            checksum=context.checksum,

            document_type=context.document_type,

            document_subtype=context.document_subtype,

            classification_confidence=(
                context.classification_confidence
            ),

            raw_text=context.raw_text,

            cleaned_text=context.cleaned_text,

            metadata=deepcopy(
                context.metadata,
            ),

            extracted_data=deepcopy(
                context.extracted_data,
            ),

            chunk_count=len(
                context.chunks,
            ),

            enriched_chunk_count=len(
                context.enriched_chunks,
            ),

            embedding_count=len(
                context.embeddings,
            ),

            indexing_result=deepcopy(
                context.indexing_result,
            ),

            current_stage=context.current_stage,

            completed_stages=tuple(
                context.completed_stages,
            ),

            failed_stages=tuple(
                context.failed_stages,
            ),

            skipped_stages=tuple(
                context.skipped_stages,
            ),

            stage_executions=tuple(
                deepcopy(
                    context.stage_executions,
                ),
            ),

            stage_results=deepcopy(
                context.stage_results,
            ),

            errors=tuple(
                context.errors,
            ),

            warnings=tuple(
                context.warnings,
            ),

            started_at=context.started_at,

            completed_at=context.completed_at,

            cancelled_at=context.cancelled_at,

            cancelled=context.cancelled,

            duration_seconds=(
                context.duration_seconds
            ),
        )

    # ==================================================================
    # Status helpers
    # ==================================================================

    @property
    def failed(self) -> bool:
        """Return whether processing failed."""

        return bool(
            self.failed_stages
        ) or bool(
            self.errors
        )

    @property
    def completed(self) -> bool:
        """Return whether processing reached a terminal state."""

        return (
            self.completed_at is not None
            or self.cancelled
        )

    # ==================================================================
    # Serialization
    # ==================================================================

    def to_dict(
        self,
        *,
        include_raw_text: bool = True,
        include_cleaned_text: bool = True,
    ) -> dict[str, Any]:
        """
        Convert the result into a JSON-friendly dictionary.

        Text inclusion can be disabled for API responses where returning
        the entire document content is undesirable.
        """

        return {
            "document_id": self.document_id,
            "success": self.success,
            "processing_job_id": (
                self.processing_job_id
            ),
            "document_version_id": (
                self.document_version_id
            ),
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "checksum": self.checksum,
            "document_type": self.document_type,
            "document_subtype": self.document_subtype,
            "classification_confidence": (
                self.classification_confidence
            ),
            "raw_text": (
                self.raw_text
                if include_raw_text
                else None
            ),
            "cleaned_text": (
                self.cleaned_text
                if include_cleaned_text
                else None
            ),
            "metadata": deepcopy(
                self.metadata,
            ),
            "extracted_data": deepcopy(
                self.extracted_data,
            ),
            "chunk_count": self.chunk_count,
            "enriched_chunk_count": (
                self.enriched_chunk_count
            ),
            "embedding_count": (
                self.embedding_count
            ),
            "indexing_result": deepcopy(
                self.indexing_result,
            ),
            "current_stage": self.current_stage,
            "completed_stages": list(
                self.completed_stages,
            ),
            "failed_stages": list(
                self.failed_stages,
            ),
            "skipped_stages": list(
                self.skipped_stages,
            ),
            "stage_executions": [
                self._stage_execution_to_dict(
                    execution,
                )
                for execution
                in self.stage_executions
            ],
            "stage_results": deepcopy(
                self.stage_results,
            ),
            "errors": list(
                self.errors,
            ),
            "warnings": list(
                self.warnings,
            ),
            "started_at": (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),
            "cancelled_at": (
                self.cancelled_at.isoformat()
                if self.cancelled_at
                else None
            ),
            "cancelled": self.cancelled,
            "duration_seconds": (
                self.duration_seconds
            ),
        }

    # ==================================================================
    # Internal serialization
    # ==================================================================

    @staticmethod
    def _stage_execution_to_dict(
        execution: StageExecution,
    ) -> dict[str, Any]:
        """Serialize a stage execution."""

        return {
            "stage": execution.stage,
            "started_at": (
                execution.started_at.isoformat()
            ),
            "completed_at": (
                execution.completed_at.isoformat()
                if execution.completed_at
                else None
            ),
            "duration_seconds": (
                execution.duration_seconds
            ),
            "success": execution.success,
            "error": execution.error,
            "attempt": execution.attempt,
        }


__all__ = [
    "ProcessingResult",
]