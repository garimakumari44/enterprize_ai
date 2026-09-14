"""
app/processing/pipeline/context.py

Canonical mutable execution state for one document-processing run.

Architecture
------------

    ProcessingJob
         |
         v
    ProcessingContext
         |
         +--> document information
         +--> extracted content
         +--> structured data
         +--> chunks
         +--> enriched chunks
         +--> embeddings
         +--> indexing result
         |
         v
    ProcessingResult

Design principles
-----------------

1. One context belongs to exactly one processing execution.
2. Stages mutate this context and return the same instance.
3. The context does not access the database.
4. The context does not execute stages.
5. The context does not contain infrastructure providers.
6. The context does not resolve providers.
7. The context does not know about StageRegistry.
8. Public API serialization belongs to ProcessingResult.
9. Stage state is tracked centrally.
10. Runtime errors are recorded as strings.
11. UTC-aware datetimes are used throughout.
12. Stage identifiers are canonical strings.
13. Artifact ownership stays inside ProcessingContext.
14. Embeddings correspond positionally to the current embedding source.
15. Replacing chunks invalidates downstream chunk-derived artifacts.
16. Replacing embedding-source artifacts invalidates embeddings/indexing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from math import isfinite
from typing import Any


# ============================================================================
# CONTEXT STATUS
# ============================================================================


class ProcessingContextStatus(StrEnum):
    """Lifecycle state of one processing execution."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# STAGE EXECUTION
# ============================================================================


@dataclass(slots=True)
class StageExecution:
    """Runtime information for one stage execution."""

    stage: str
    started_at: datetime
    completed_at: datetime | None = None
    success: bool = False
    error: str | None = None
    duration_seconds: float | None = None

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None


# ============================================================================
# PROCESSING CONTEXT
# ============================================================================


@dataclass(slots=True)
class ProcessingContext:
    """Mutable state shared by all stages of one processing execution."""

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    job_id: str
    document_id: str
    document_version_id: str | None = None

    # ------------------------------------------------------------------
    # Document information
    # ------------------------------------------------------------------

    file_path: str | None = None
    file_name: str | None = None
    mime_type: str | None = None

    file_size: int | None = None
    checksum: str | None = None

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    document_type: str | None = None
    document_subtype: str | None = None
    classification_confidence: float | None = None

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    raw_text: str | None = None
    cleaned_text: str | None = None

    # ------------------------------------------------------------------
    # Structured data
    # ------------------------------------------------------------------

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    extracted_data: dict[str, Any] = field(
        default_factory=dict,
    )

    # ------------------------------------------------------------------
    # Processing artifacts
    # ------------------------------------------------------------------

    chunks: list[Any] = field(
        default_factory=list,
    )

    enriched_chunks: list[Any] = field(
        default_factory=list,
    )

    embeddings: list[list[float]] = field(
        default_factory=list,
    )

    indexing_result: Any | None = None

    # ------------------------------------------------------------------
    # Execution state
    # ------------------------------------------------------------------

    status: ProcessingContextStatus = (
        ProcessingContextStatus.CREATED
    )

    current_stage: str | None = None

    completed_stages: list[str] = field(
        default_factory=list,
    )

    failed_stages: list[str] = field(
        default_factory=list,
    )

    skipped_stages: list[str] = field(
        default_factory=list,
    )

    cancelled_stages: list[str] = field(
        default_factory=list,
    )

    # ------------------------------------------------------------------
    # Stage information
    # ------------------------------------------------------------------

    stage_results: dict[str, Any] = field(
        default_factory=dict,
    )

    stage_executions: list[StageExecution] = field(
        default_factory=list,
    )

    # ------------------------------------------------------------------
    # Errors
    # ------------------------------------------------------------------

    errors: list[str] = field(
        default_factory=list,
    )

    warnings: list[str] = field(
        default_factory=list,
    )

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    # =========================================================================
    # INITIAL VALIDATION
    # =========================================================================

    def __post_init__(self) -> None:
        self.job_id = self._validate_identifier(
            self.job_id,
            "job_id",
        )

        self.document_id = self._validate_identifier(
            self.document_id,
            "document_id",
        )

        if self.document_version_id is not None:
            self.document_version_id = (
                self._validate_identifier(
                    self.document_version_id,
                    "document_version_id",
                )
            )

        if self.file_size is not None:
            if isinstance(self.file_size, bool):
                raise TypeError(
                    "file_size must be an integer or None."
                )

            if not isinstance(self.file_size, int):
                raise TypeError(
                    "file_size must be an integer or None."
                )

            if self.file_size < 0:
                raise ValueError(
                    "file_size cannot be negative."
                )

        if self.classification_confidence is not None:
            self.classification_confidence = (
                self._normalize_confidence(
                    self.classification_confidence
                )
            )

        self._ensure_utc_datetime(
            self.created_at,
            field_name="created_at",
        )

        if self.started_at is not None:
            self._ensure_utc_datetime(
                self.started_at,
                field_name="started_at",
            )

        if self.completed_at is not None:
            self._ensure_utc_datetime(
                self.completed_at,
                field_name="completed_at",
            )

        self._validate_artifact_alignment()

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def start(self) -> None:
        """Transition CREATED -> RUNNING."""

        if self.status is ProcessingContextStatus.CREATED:
            self.status = ProcessingContextStatus.RUNNING

            if self.started_at is None:
                self.started_at = self._now()

            return

        if self.status is ProcessingContextStatus.RUNNING:
            return

        raise RuntimeError(
            "ProcessingContext cannot be started from "
            f"status '{self.status.value}'."
        )

    def finish(self) -> None:
        """Finalize the processing context."""

        if self.status is ProcessingContextStatus.CANCELLED:
            self.current_stage = None

            if self.completed_at is None:
                self.completed_at = self._now()

            return

        if self.status not in {
            ProcessingContextStatus.CREATED,
            ProcessingContextStatus.RUNNING,
            ProcessingContextStatus.FAILED,
            ProcessingContextStatus.COMPLETED,
        }:
            raise RuntimeError(
                "ProcessingContext cannot be finalized from "
                f"status '{self.status.value}'."
            )

        if self.started_at is None:
            self.started_at = self._now()

        if self.completed_at is None:
            self.completed_at = self._now()

        self.current_stage = None

        if (
            self.failed_stages
            or self.cancelled_stages
            or self.status is ProcessingContextStatus.FAILED
        ):
            self.status = ProcessingContextStatus.FAILED
        else:
            self.status = ProcessingContextStatus.COMPLETED

    def fail(
        self,
        error: str,
    ) -> None:
        """Mark the complete processing execution as failed."""

        normalized_error = self._normalize_message(
            error,
            field_name="error",
        )

        if self.status is ProcessingContextStatus.COMPLETED:
            raise RuntimeError(
                "A completed ProcessingContext cannot fail."
            )

        self.errors.append(normalized_error)

        self.status = ProcessingContextStatus.FAILED
        self.current_stage = None

        if self.completed_at is None:
            self.completed_at = self._now()

    def cancel(self) -> None:
        """Mark processing as cancelled."""

        if self.status in {
            ProcessingContextStatus.COMPLETED,
            ProcessingContextStatus.FAILED,
            ProcessingContextStatus.CANCELLED,
        }:
            raise RuntimeError(
                "ProcessingContext cannot be cancelled from "
                f"status '{self.status.value}'."
            )

        self.current_stage = None
        self.status = ProcessingContextStatus.CANCELLED

        if self.completed_at is None:
            self.completed_at = self._now()

    # =========================================================================
    # STAGE NORMALIZATION
    # =========================================================================

    @staticmethod
    def normalize_stage(
        stage: str,
    ) -> str:
        if not isinstance(stage, str):
            raise TypeError(
                "stage must be a string."
            )

        normalized = stage.strip().lower()

        if not normalized:
            raise ValueError(
                "stage cannot be empty."
            )

        return normalized

    # =========================================================================
    # STAGE START
    # =========================================================================

    def set_stage(
        self,
        stage: str,
    ) -> None:
        """Mark a stage as currently executing."""

        normalized_stage = self.normalize_stage(
            stage
        )

        if self.status is ProcessingContextStatus.CREATED:
            self.start()

        if self.status is not ProcessingContextStatus.RUNNING:
            raise RuntimeError(
                "Cannot start stage "
                f"'{normalized_stage}' while context status is "
                f"'{self.status.value}'."
            )

        if self.current_stage is not None:
            raise RuntimeError(
                "Cannot start stage "
                f"'{normalized_stage}' while stage "
                f"'{self.current_stage}' is still active."
            )

        self.current_stage = normalized_stage

        self.stage_executions.append(
            StageExecution(
                stage=normalized_stage,
                started_at=self._now(),
            )
        )

    # =========================================================================
    # CURRENT STAGE EXECUTION
    # =========================================================================

    def _current_stage_execution(
        self,
        stage: str,
    ) -> StageExecution | None:
        for execution in reversed(
            self.stage_executions
        ):
            if (
                execution.stage == stage
                and not execution.is_completed
            ):
                return execution

        return None

    # =========================================================================
    # STAGE RESULT
    # =========================================================================

    def set_stage_result(
        self,
        stage: str,
        result: Any,
    ) -> None:
        """Store a result produced by one processing stage."""

        normalized_stage = self.normalize_stage(
            stage
        )

        self.stage_results[
            normalized_stage
        ] = result

    def get_stage_result(
        self,
        stage: str,
        default: Any = None,
    ) -> Any:
        """Return a stored stage result."""

        normalized_stage = self.normalize_stage(
            stage
        )

        return self.stage_results.get(
            normalized_stage,
            default,
        )

    # =========================================================================
    # COMPLETE STAGE
    # =========================================================================

    def complete_stage(
        self,
        stage: str,
        result: Any = None,
    ) -> None:
        """Mark a stage as successfully completed."""

        normalized_stage = self.normalize_stage(
            stage
        )

        if self.current_stage != normalized_stage:
            raise RuntimeError(
                f"Stage '{normalized_stage}' is not the "
                "currently active stage."
            )

        execution = self._current_stage_execution(
            normalized_stage
        )

        if execution is None:
            raise RuntimeError(
                f"No active execution exists for stage "
                f"'{normalized_stage}'."
            )

        execution.completed_at = self._now()
        execution.success = True
        execution.error = None
        execution.duration_seconds = (
            execution.completed_at
            - execution.started_at
        ).total_seconds()

        if normalized_stage not in self.completed_stages:
            self.completed_stages.append(
                normalized_stage
            )

        for collection in (
            self.failed_stages,
            self.skipped_stages,
            self.cancelled_stages,
        ):
            if normalized_stage in collection:
                collection.remove(
                    normalized_stage
                )

        if result is not None:
            self.set_stage_result(
                normalized_stage,
                result,
            )

        self.current_stage = None

    # =========================================================================
    # FAIL STAGE
    # =========================================================================

    def fail_stage(
        self,
        stage: str,
        error: str,
    ) -> None:
        """Record a stage failure."""

        normalized_stage = self.normalize_stage(
            stage
        )

        error_message = self._normalize_message(
            error,
            field_name="error",
        )

        if normalized_stage not in self.failed_stages:
            self.failed_stages.append(
                normalized_stage
            )

        self.errors.append(
            f"{normalized_stage}: {error_message}"
        )

        execution = self._current_stage_execution(
            normalized_stage
        )

        if execution is not None:
            execution.completed_at = self._now()
            execution.success = False
            execution.error = error_message
            execution.duration_seconds = (
                execution.completed_at
                - execution.started_at
            ).total_seconds()

        self.current_stage = None
        self.status = ProcessingContextStatus.FAILED

        if self.completed_at is None:
            self.completed_at = self._now()

    # =========================================================================
    # SKIP STAGE
    # =========================================================================

    def skip_stage(
        self,
        stage: str,
        reason: str | None = None,
    ) -> None:
        """Mark a stage as intentionally skipped."""

        normalized_stage = self.normalize_stage(
            stage
        )

        if self.current_stage == normalized_stage:
            self.current_stage = None

        if normalized_stage not in self.skipped_stages:
            self.skipped_stages.append(
                normalized_stage
            )

        if reason:
            self.add_warning(
                f"{normalized_stage}: {reason}"
            )

    # =========================================================================
    # CANCEL STAGE
    # =========================================================================

    def cancel_stage(
        self,
        stage: str,
    ) -> None:
        """Record a stage as cancelled."""

        normalized_stage = self.normalize_stage(
            stage
        )

        if normalized_stage not in self.cancelled_stages:
            self.cancelled_stages.append(
                normalized_stage
            )

        execution = self._current_stage_execution(
            normalized_stage
        )

        if execution is not None:
            execution.completed_at = self._now()
            execution.success = False
            execution.error = "Stage cancelled."
            execution.duration_seconds = (
                execution.completed_at
                - execution.started_at
            ).total_seconds()

        if self.current_stage == normalized_stage:
            self.current_stage = None

    # =========================================================================
    # METADATA
    # =========================================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        normalized_key = self._validate_key(
            key,
            field_name="metadata key",
        )

        self.metadata[normalized_key] = value

    def update_metadata(
        self,
        values: Mapping[str, Any],
    ) -> None:
        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping."
            )

        for key, value in values.items():
            self.set_metadata(
                key,
                value,
            )

    # =========================================================================
    # EXTRACTED DATA
    # =========================================================================

    def set_extracted_data(
        self,
        key: str,
        value: Any,
    ) -> None:
        normalized_key = self._validate_key(
            key,
            field_name="extracted-data key",
        )

        self.extracted_data[
            normalized_key
        ] = value

    def update_extracted_data(
        self,
        values: Mapping[str, Any],
    ) -> None:
        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping."
            )

        for key, value in values.items():
            self.set_extracted_data(
                key,
                value,
            )

    # =========================================================================
    # DOCUMENT CONTENT
    # =========================================================================

    def set_raw_text(
        self,
        text: str | None,
    ) -> None:
        if text is not None and not isinstance(
            text,
            str,
        ):
            raise TypeError(
                "raw_text must be a string or None."
            )

        self.raw_text = text

    def set_cleaned_text(
        self,
        text: str | None,
    ) -> None:
        if text is not None and not isinstance(
            text,
            str,
        ):
            raise TypeError(
                "cleaned_text must be a string or None."
            )

        self.cleaned_text = text

    # =========================================================================
    # CHUNKS
    # =========================================================================

    def set_chunks(
        self,
        chunks: Sequence[Any],
    ) -> None:
        """Replace chunks and invalidate downstream artifacts."""

        self._validate_sequence(
            chunks,
            field_name="chunks",
        )

        self.chunks = list(chunks)

        self.enriched_chunks.clear()
        self.embeddings.clear()
        self.indexing_result = None

    # =========================================================================
    # ENRICHED CHUNKS
    # =========================================================================

    def set_enriched_chunks(
        self,
        chunks: Sequence[Any],
    ) -> None:
        """Replace enriched chunks."""

        self._validate_sequence(
            chunks,
            field_name="enriched_chunks",
        )

        if (
            self.chunks
            and len(chunks) != len(self.chunks)
        ):
            raise ValueError(
                "enriched_chunks must contain the same number "
                "of items as chunks."
            )

        self.enriched_chunks = list(chunks)

        self.embeddings.clear()
        self.indexing_result = None

    # =========================================================================
    # EMBEDDINGS
    # =========================================================================

    def set_embeddings(
        self,
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        """
        Store embedding vectors.

        Embeddings correspond positionally to the current
        embedding-source chunk collection.
        """

        self._validate_sequence(
            embeddings,
            field_name="embeddings",
        )

        source_chunks = self.embedding_source_chunks

        if (
            source_chunks
            and len(embeddings) != len(source_chunks)
        ):
            raise ValueError(
                "The number of embeddings must match the number "
                "of embedding source chunks. "
                f"Got {len(embeddings)} embeddings for "
                f"{len(source_chunks)} chunks."
            )

        normalized_embeddings: list[list[float]] = []

        for index, embedding in enumerate(
            embeddings
        ):
            if isinstance(
                embedding,
                (str, bytes),
            ):
                raise TypeError(
                    f"Embedding at index {index} must be "
                    "a numeric sequence."
                )

            try:
                values = list(embedding)
            except TypeError as exc:
                raise TypeError(
                    f"Embedding at index {index} must be "
                    "a numeric sequence."
                ) from exc

            if not values:
                raise ValueError(
                    f"Embedding at index {index} cannot be empty."
                )

            vector: list[float] = []

            for value in values:
                if isinstance(value, bool):
                    raise TypeError(
                        f"Embedding at index {index} contains "
                        "a boolean value."
                    )

                if not isinstance(
                    value,
                    (int, float),
                ):
                    raise TypeError(
                        f"Embedding at index {index} contains "
                        f"non-numeric value of type "
                        f"{type(value).__name__}."
                    )

                numeric_value = float(value)

                if not isfinite(numeric_value):
                    raise ValueError(
                        f"Embedding at index {index} contains "
                        "a non-finite numeric value."
                    )

                vector.append(numeric_value)

            normalized_embeddings.append(
                vector
            )

        if normalized_embeddings:
            dimension = len(
                normalized_embeddings[0]
            )

            for index, vector in enumerate(
                normalized_embeddings
            ):
                if len(vector) != dimension:
                    raise ValueError(
                        "Embedding vectors must have a consistent "
                        f"dimension. Vector 0 has dimension "
                        f"{dimension}, but vector {index} has "
                        f"dimension {len(vector)}."
                    )

        self.embeddings = normalized_embeddings

        # New embeddings mean a previous indexing result is stale.
        self.indexing_result = None

    @property
    def embedding_source_chunks(self) -> list[Any]:
        if self.enriched_chunks:
            return self.enriched_chunks

        return self.chunks

    @property
    def has_chunks(self) -> bool:
        return bool(self.chunks)

    @property
    def has_enriched_chunks(self) -> bool:
        return bool(self.enriched_chunks)

    @property
    def has_embeddings(self) -> bool:
        return bool(self.embeddings)

    @property
    def embedding_dimension(self) -> int | None:
        if not self.embeddings:
            return None

        dimension = len(
            self.embeddings[0]
        )

        for index, embedding in enumerate(
            self.embeddings
        ):
            if len(embedding) != dimension:
                raise ValueError(
                    "Embedding vectors must have a consistent "
                    f"dimension. Vector 0 has dimension "
                    f"{dimension}, but vector {index} has "
                    f"dimension {len(embedding)}."
                )

        return dimension

    # =========================================================================
    # INDEXING
    # =========================================================================

    def set_indexing_result(
        self,
        result: Any,
    ) -> None:
        """Store the indexing-stage result."""

        self.indexing_result = result

    # =========================================================================
    # WARNINGS / ERRORS
    # =========================================================================

    def add_warning(
        self,
        message: str,
    ) -> None:
        self.warnings.append(
            self._normalize_message(
                message,
                field_name="warning",
            )
        )

    def add_error(
        self,
        message: str,
    ) -> None:
        self.errors.append(
            self._normalize_message(
                message,
                field_name="error",
            )
        )

    # =========================================================================
    # STATUS
    # =========================================================================

    @property
    def is_failed(self) -> bool:
        return (
            self.status is ProcessingContextStatus.FAILED
            or bool(self.failed_stages)
        )

    @property
    def is_cancelled(self) -> bool:
        return (
            self.status
            is ProcessingContextStatus.CANCELLED
        )

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    @property
    def is_successful(self) -> bool:
        return (
            self.status is ProcessingContextStatus.COMPLETED
            and self.completed_at is not None
            and not self.failed_stages
            and not self.cancelled_stages
        )

    # =========================================================================
    # TIMING
    # =========================================================================

    @property
    def duration_seconds(self) -> float | None:
        if (
            self.started_at is None
            or self.completed_at is None
        ):
            return None

        return max(
            0.0,
            (
                self.completed_at
                - self.started_at
            ).total_seconds(),
        )

    @property
    def current_stage_duration_seconds(
        self,
    ) -> float | None:
        if self.current_stage is None:
            return None

        execution = self._current_stage_execution(
            self.current_stage
        )

        if execution is None:
            return None

        return max(
            0.0,
            (
                self._now()
                - execution.started_at
            ).total_seconds(),
        )

    # =========================================================================
    # COUNTS
    # =========================================================================

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def enriched_chunk_count(self) -> int:
        return len(self.enriched_chunks)

    @property
    def embedding_count(self) -> int:
        return len(self.embeddings)

    # =========================================================================
    # ARTIFACT VALIDATION
    # =========================================================================

    def _validate_artifact_alignment(self) -> None:
        if (
            self.enriched_chunks
            and self.chunks
            and len(self.enriched_chunks)
            != len(self.chunks)
        ):
            raise ValueError(
                "enriched_chunks must contain the same number "
                "of items as chunks."
            )

        source_chunks = self.embedding_source_chunks

        if (
            self.embeddings
            and source_chunks
            and len(self.embeddings)
            != len(source_chunks)
        ):
            raise ValueError(
                "The number of embeddings must match the number "
                "of embedding source chunks."
            )

        self.embedding_dimension

    # =========================================================================
    # SNAPSHOT
    # =========================================================================

    def snapshot(self) -> dict[str, Any]:
        """Return a defensive diagnostic snapshot."""

        return deepcopy(
            {
                "job_id": self.job_id,
                "document_id": self.document_id,
                "document_version_id": self.document_version_id,
                "file_path": self.file_path,
                "file_name": self.file_name,
                "mime_type": self.mime_type,
                "file_size": self.file_size,
                "checksum": self.checksum,
                "document_type": self.document_type,
                "document_subtype": self.document_subtype,
                "classification_confidence": (
                    self.classification_confidence
                ),
                "raw_text": self.raw_text,
                "cleaned_text": self.cleaned_text,
                "metadata": self.metadata,
                "extracted_data": self.extracted_data,
                "chunk_count": self.chunk_count,
                "enriched_chunk_count": (
                    self.enriched_chunk_count
                ),
                "embedding_count": self.embedding_count,
                "embedding_dimension": (
                    self.embedding_dimension
                ),
                "indexing_result": self.indexing_result,
                "status": self.status.value,
                "current_stage": self.current_stage,
                "completed_stages": self.completed_stages,
                "failed_stages": self.failed_stages,
                "skipped_stages": self.skipped_stages,
                "cancelled_stages": self.cancelled_stages,
                "stage_results": self.stage_results,
                "stage_executions": [
                    {
                        "stage": execution.stage,
                        "started_at": (
                            execution.started_at.isoformat()
                        ),
                        "completed_at": (
                            execution.completed_at.isoformat()
                            if execution.completed_at
                            else None
                        ),
                        "success": execution.success,
                        "error": execution.error,
                        "duration_seconds": (
                            execution.duration_seconds
                        ),
                    }
                    for execution in self.stage_executions
                ],
                "errors": self.errors,
                "warnings": self.warnings,
                "created_at": (
                    self.created_at.isoformat()
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
                "duration_seconds": (
                    self.duration_seconds
                ),
                "success": self.is_successful,
            }
        )

    # =========================================================================
    # INTERNAL RESULT REPRESENTATION
    # =========================================================================

    def to_result(self) -> dict[str, Any]:
        """Return normalized internal result representation."""

        return {
            "job_id": self.job_id,
            "document_id": self.document_id,
            "document_version_id": (
                self.document_version_id
            ),
            "file_path": self.file_path,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "checksum": self.checksum,
            "document_type": self.document_type,
            "document_subtype": self.document_subtype,
            "classification_confidence": (
                self.classification_confidence
            ),
            "raw_text": self.raw_text,
            "cleaned_text": self.cleaned_text,
            "metadata": deepcopy(self.metadata),
            "extracted_data": deepcopy(
                self.extracted_data
            ),
            "chunk_count": self.chunk_count,
            "enriched_chunk_count": (
                self.enriched_chunk_count
            ),
            "embedding_count": self.embedding_count,
            "embedding_dimension": (
                self.embedding_dimension
            ),
            "indexing_result": deepcopy(
                self.indexing_result
            ),
            "status": self.status.value,
            "current_stage": self.current_stage,
            "completed_stages": list(
                self.completed_stages
            ),
            "failed_stages": list(
                self.failed_stages
            ),
            "skipped_stages": list(
                self.skipped_stages
            ),
            "cancelled_stages": list(
                self.cancelled_stages
            ),
            "stage_results": deepcopy(
                self.stage_results
            ),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "created_at": (
                self.created_at.isoformat()
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
            "duration_seconds": self.duration_seconds,
            "success": self.is_successful,
        }

    # =========================================================================
    # RESET
    # =========================================================================

    def reset_runtime(
        self,
        *,
        preserve_stage_results: bool = False,
    ) -> None:
        """
        Reset runtime state while preserving document artifacts.

        By default stage results are also cleared.
        """

        self.status = ProcessingContextStatus.CREATED
        self.current_stage = None

        self.completed_stages.clear()
        self.failed_stages.clear()
        self.skipped_stages.clear()
        self.cancelled_stages.clear()

        if not preserve_stage_results:
            self.stage_results.clear()

        self.stage_executions.clear()

        self.errors.clear()
        self.warnings.clear()

        self.started_at = None
        self.completed_at = None

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    @staticmethod
    def _validate_identifier(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return normalized

    @staticmethod
    def _validate_key(
        key: str,
        *,
        field_name: str,
    ) -> str:
        if not isinstance(key, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized = key.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_message(
        message: str,
        *,
        field_name: str,
    ) -> str:
        if not isinstance(message, str):
            raise TypeError(
                f"{field_name} message must be a string."
            )

        normalized = message.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} message cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_confidence(
        confidence: Any,
    ) -> float:
        if confidence is None:
            return 0.0

        if isinstance(confidence, bool):
            return 0.0

        try:
            if isinstance(confidence, str):
                value = confidence.strip()

                if not value:
                    return 0.0

                if ":" in value:
                    value = value.split(
                        ":",
                        1,
                    )[1].strip()

                percentage = value.endswith("%")

                if percentage:
                    value = value[:-1].strip()

                number = float(value)

                if percentage:
                    number /= 100.0
            else:
                number = float(confidence)

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0

        if not isfinite(number):
            return 0.0

        if number > 1.0:
            number /= 100.0

        return max(
            0.0,
            min(
                number,
                1.0,
            ),
        )

    @staticmethod
    def _validate_sequence(
        value: Sequence[Any],
        *,
        field_name: str,
    ) -> None:
        if isinstance(
            value,
            (str, bytes),
        ):
            raise TypeError(
                f"{field_name} must be a sequence, "
                "not a string."
            )

        if not isinstance(
            value,
            Sequence,
        ):
            raise TypeError(
                f"{field_name} must be a sequence."
            )

    @staticmethod
    def _ensure_utc_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> None:
        if not isinstance(
            value,
            datetime,
        ):
            raise TypeError(
                f"{field_name} must be a datetime."
            )

        if value.tzinfo is None:
            raise ValueError(
                f"{field_name} must be timezone-aware."
            )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    # =========================================================================
    # REPRESENTATION
    # =========================================================================

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"job_id={self.job_id!r}, "
            f"document_id={self.document_id!r}, "
            f"status={self.status.value!r}, "
            f"current_stage={self.current_stage!r}, "
            f"completed_stages={len(self.completed_stages)}, "
            f"failed_stages={len(self.failed_stages)}, "
            f"chunks={self.chunk_count}, "
            f"embeddings={self.embedding_count}"
            ")"
        )


__all__ = [
    "ProcessingContext",
    "ProcessingContextStatus",
    "StageExecution",
]