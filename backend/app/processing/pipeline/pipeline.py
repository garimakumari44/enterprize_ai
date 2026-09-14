"""
app/processing/pipeline/pipeline.py

Core document-processing pipeline primitives.

The pipeline executes already-resolved processing stages sequentially.

The pipeline does not resolve providers or access persistence directly.
It only forwards the job-scoped AsyncSession to stages that require it.
"""

from __future__ import annotations

import inspect
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.processing.pipeline.context import (
    ProcessingContext,
    ProcessingContextStatus,
)


logger = logging.getLogger(__name__)


# ============================================================================
# TYPES
# ============================================================================

ProgressCallback = Callable[
    [str, int, str],
    Awaitable[None] | None,
]


# ============================================================================
# STAGE BASE CLASS
# ============================================================================


class DocumentProcessingStage(ABC):
    """
    Base class for every document-processing stage.

    A stage:

        1. receives ProcessingContext
        2. optionally receives the job-scoped AsyncSession
        3. mutates the context
        4. returns the SAME ProcessingContext instance

    The session is not stored in ProcessingContext.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the canonical stage name."""
        raise NotImplementedError

    @abstractmethod
    def process(
        self,
        context: ProcessingContext,
        *,
        session: AsyncSession | None = None,
    ) -> ProcessingContext | Awaitable[ProcessingContext]:
        """
        Process the shared ProcessingContext.

        Implementations may be synchronous or asynchronous.

        Stages that do not need database access can ignore session.
        """
        raise NotImplementedError

    def __call__(
        self,
        context: ProcessingContext,
        *,
        session: AsyncSession | None = None,
    ) -> ProcessingContext | Awaitable[ProcessingContext]:
        return self.process(
            context,
            session=session,
        )


# ============================================================================
# PROCESSING PIPELINE
# ============================================================================


class ProcessingPipeline:
    """
    Sequential async-aware processing pipeline.

    The pipeline receives already-resolved stage instances.

    It does NOT:

        - resolve providers
        - discover stages
        - construct infrastructure
        - own database sessions
        - close database sessions

    It only forwards the session supplied by the caller to each stage.
    """

    def __init__(
        self,
        *,
        stages: Iterable[DocumentProcessingStage] | None = None,
        fail_fast: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> None:

        self._stages: list[
            DocumentProcessingStage
        ] = []

        self.fail_fast = bool(fail_fast)

        self.progress_callback = progress_callback

        if stages is not None:
            for stage in stages:
                self.add_stage(stage)

    # =========================================================================
    # STAGE MANAGEMENT
    # =========================================================================

    @property
    def stages(
        self,
    ) -> tuple[DocumentProcessingStage, ...]:
        return tuple(self._stages)

    def add_stage(
        self,
        stage: DocumentProcessingStage,
    ) -> None:

        if not isinstance(
            stage,
            DocumentProcessingStage,
        ):
            raise TypeError(
                "stage must be an instance of "
                "DocumentProcessingStage."
            )

        self._stages.append(stage)

    def clear(self) -> None:
        self._stages.clear()

    # =========================================================================
    # INSPECTION
    # =========================================================================

    def stage_names(self) -> tuple[str, ...]:
        return tuple(
            self._normalize_stage_name(
                stage.name
            )
            for stage in self._stages
        )

    def has_stage(
        self,
        name: str,
    ) -> bool:

        normalized_name = self._normalize_stage_name(
            name
        )

        return any(
            self._normalize_stage_name(
                stage.name
            )
            == normalized_name
            for stage in self._stages
        )

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate(self) -> None:
        """Validate all configured stages."""

        seen: set[str] = set()

        for stage in self._stages:

            if not isinstance(
                stage,
                DocumentProcessingStage,
            ):
                raise TypeError(
                    "All pipeline stages must be instances of "
                    "DocumentProcessingStage."
                )

            normalized_name = (
                self._normalize_stage_name(
                    stage.name
                )
            )

            if normalized_name in seen:
                raise ValueError(
                    "Duplicate processing stage "
                    f"'{normalized_name}' in pipeline."
                )

            seen.add(normalized_name)

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def execute(
        self,
        context: ProcessingContext,
        *,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        """
        Execute every configured stage sequentially.

        Stages must mutate and return the same context instance.

        The supplied session belongs to the current processing execution.
        It is forwarded to stages but never stored in ProcessingContext.
        """

        if not isinstance(
            context,
            ProcessingContext,
        ):
            raise TypeError(
                "ProcessingPipeline.execute() requires a "
                "ProcessingContext."
            )

        self.validate()

        if not self._stages:
            raise ValueError(
                "Processing pipeline contains no stages."
            )

        total_stages = len(
            self._stages
        )

        logger.info(
            "Starting processing pipeline with %d stages.",
            total_stages,
        )

        # ------------------------------------------------------------------
        # Start context
        # ------------------------------------------------------------------

        if (
            context.status
            is ProcessingContextStatus.CREATED
        ):
            context.start()

        elif (
            context.status
            is not ProcessingContextStatus.RUNNING
        ):
            raise RuntimeError(
                "ProcessingPipeline cannot execute with context "
                f"status '{context.status.value}'."
            )

        # ------------------------------------------------------------------
        # Execute stages
        # ------------------------------------------------------------------

        for index, stage in enumerate(
            self._stages,
            start=1,
        ):

            stage_name = self._normalize_stage_name(
                stage.name
            )

            start_progress = self._calculate_progress(
                index - 1,
                total_stages,
            )

            completed_progress = self._calculate_progress(
                index,
                total_stages,
            )

            logger.info(
                "Starting processing stage '%s' "
                "(%d/%d, %d%%).",
                stage_name,
                index,
                total_stages,
                start_progress,
            )

            context.set_stage(
                stage_name
            )

            await self._report_progress(
                stage_name=stage_name,
                progress=start_progress,
                status="running",
            )

            try:

                # ----------------------------------------------------------
                # Execute stage
                # ----------------------------------------------------------

                result = stage.process(
                    context,
                    session=session,
                )

                if inspect.isawaitable(result):
                    result = await result

                # ----------------------------------------------------------
                # Validate returned context
                # ----------------------------------------------------------

                if not isinstance(
                    result,
                    ProcessingContext,
                ):
                    raise TypeError(
                        f"Processing stage '{stage_name}' "
                        "must return ProcessingContext, "
                        f"got {type(result).__name__}."
                    )

                if result is not context:
                    raise ValueError(
                        f"Processing stage '{stage_name}' "
                        "returned a different ProcessingContext "
                        "instance. Stages must mutate and return "
                        "the existing pipeline context."
                    )

                # ----------------------------------------------------------
                # Complete stage
                # ----------------------------------------------------------

                context.complete_stage(
                    stage_name
                )

                await self._report_progress(
                    stage_name=stage_name,
                    progress=completed_progress,
                    status="completed",
                )

                logger.info(
                    "Completed processing stage '%s' "
                    "(%d/%d, %d%%).",
                    stage_name,
                    index,
                    total_stages,
                    completed_progress,
                )

            except Exception as exc:

                logger.exception(
                    "Processing stage '%s' failed.",
                    stage_name,
                )

                context.fail_stage(
                    stage_name,
                    self._exception_message(exc),
                )

                await self._report_progress(
                    stage_name=stage_name,
                    progress=start_progress,
                    status="failed",
                )

                if self.fail_fast:
                    raise

                # ----------------------------------------------------------
                # Recoverable stage failure
                # ----------------------------------------------------------

                logger.warning(
                    "Continuing pipeline after failed stage '%s' "
                    "because fail_fast=False.",
                    stage_name,
                )

                context.status = (
                    ProcessingContextStatus.RUNNING
                )

                context.current_stage = None
                context.completed_at = None

        # ------------------------------------------------------------------
        # Finalize
        # ------------------------------------------------------------------

        context.finish()

        final_status = (
            "failed"
            if context.is_failed
            else "completed"
        )

        await self._report_progress(
            stage_name="",
            progress=100,
            status=final_status,
        )

        if context.is_failed:

            logger.warning(
                "Processing pipeline completed with "
                "one or more failed stages.",
                extra={
                    "failed_stages": list(
                        context.failed_stages
                    ),
                    "completed_stages": list(
                        context.completed_stages
                    ),
                },
            )

        else:

            logger.info(
                "Processing pipeline completed successfully."
            )

        return context

    # =========================================================================
    # PROGRESS
    # =========================================================================

    async def _report_progress(
        self,
        *,
        stage_name: str,
        progress: int,
        status: str,
    ) -> None:

        callback = self.progress_callback

        if callback is None:
            return

        progress = max(
            0,
            min(
                100,
                int(progress),
            ),
        )

        try:

            result = callback(
                stage_name,
                progress,
                status,
            )

            if inspect.isawaitable(result):
                await result

        except Exception:

            logger.exception(
                "Processing progress callback failed.",
                extra={
                    "stage_name": stage_name,
                    "progress": progress,
                    "status": status,
                },
            )

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _normalize_stage_name(
        name: Any,
    ) -> str:

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Processing stage name must be a string."
            )

        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError(
                "Processing stage name cannot be empty."
            )

        return normalized_name

    @staticmethod
    def _calculate_progress(
        completed: int,
        total: int,
    ) -> int:

        if total <= 0:
            return 0

        return int(
            (completed / total) * 100
        )

    @staticmethod
    def _exception_message(
        exc: Exception,
    ) -> str:

        message = str(exc).strip()

        if message:
            return message

        return type(exc).__name__


# ============================================================================
# PIPELINE BUILDER
# ============================================================================


class PipelineBuilder:
    """
    Constructs ProcessingPipeline instances.

    Stage resolution belongs outside this class.
    """

    @staticmethod
    def build(
        *,
        stages: Iterable[DocumentProcessingStage],
        fail_fast: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> ProcessingPipeline:

        pipeline = ProcessingPipeline(
            stages=stages,
            fail_fast=fail_fast,
            progress_callback=progress_callback,
        )

        pipeline.validate()

        return pipeline


__all__ = [
    "DocumentProcessingStage",
    "ProcessingPipeline",
    "PipelineBuilder",
    "ProgressCallback",
]