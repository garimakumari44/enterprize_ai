"""
app/processing/stage_registry.py

Central registry for document-processing stages.

Responsibilities
----------------

- Register processing stages.
- Resolve stages by canonical name.
- Validate registered stages.
- Validate canonical pipeline completeness.
- Build pipelines from resolved stages.
- Expose registered-stage inspection.

This module does NOT:

- create embedding providers
- create embedding models
- access the database
- execute processing stages
- manage ProcessingContext
- resolve workflow definitions
"""

from __future__ import annotations

from collections.abc import Iterable

from app.core.constants import ProcessingStage
from app.processing.pipeline.pipeline import (
    DocumentProcessingStage,
    ProcessingPipeline,
    ProgressCallback,
)


class StageRegistry:
    """
    Registry of concrete processing-stage implementations.

    The registry is an infrastructure/composition concern.

    It does not execute stages itself.
    """

    def __init__(
        self,
        stages: Iterable[
            DocumentProcessingStage
        ]
        | None = None,
    ) -> None:

        self._stages: dict[
            str,
            DocumentProcessingStage,
        ] = {}

        if stages is not None:
            for stage in stages:
                self.register(stage)

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def register(
        self,
        stage: DocumentProcessingStage,
    ) -> None:
        """Register a concrete processing stage."""

        self._validate_stage_instance(
            stage
        )

        name = self._normalize_name(
            stage.name
        )

        if name in self._stages:
            raise ValueError(
                f"Processing stage '{name}' "
                "is already registered."
            )

        self._stages[name] = stage

    def replace(
        self,
        stage: DocumentProcessingStage,
    ) -> None:
        """Replace an existing stage implementation."""

        self._validate_stage_instance(
            stage
        )

        name = self._normalize_name(
            stage.name
        )

        self._stages[name] = stage

    def unregister(
        self,
        name: str | ProcessingStage,
    ) -> DocumentProcessingStage:
        """Remove and return a registered stage."""

        normalized_name = self._normalize_name(
            name
        )

        try:
            return self._stages.pop(
                normalized_name
            )
        except KeyError as exc:
            raise KeyError(
                f"No processing stage registered for "
                f"'{normalized_name}'."
            ) from exc

    # =========================================================================
    # RESOLUTION
    # =========================================================================

    def resolve(
        self,
        name: str | ProcessingStage,
    ) -> DocumentProcessingStage:
        """Resolve a registered processing stage."""

        normalized_name = self._normalize_name(
            name
        )

        try:
            return self._stages[
                normalized_name
            ]
        except KeyError as exc:
            raise KeyError(
                f"No processing stage registered for "
                f"'{normalized_name}'."
            ) from exc

    def resolve_many(
        self,
        names: Iterable[
            str | ProcessingStage
        ],
    ) -> tuple[
        DocumentProcessingStage,
        ...,
    ]:
        """Resolve several stages in the supplied order."""

        return tuple(
            self.resolve(name)
            for name in names
        )

    def has(
        self,
        name: str | ProcessingStage,
    ) -> bool:
        """Return whether a stage is registered."""

        normalized_name = self._normalize_name(
            name
        )

        return normalized_name in self._stages

    # =========================================================================
    # INSPECTION
    # =========================================================================

    def names(
        self,
    ) -> tuple[str, ...]:
        """Return registered stage names."""

        return tuple(
            self._stages.keys()
        )

    def stages(
        self,
    ) -> tuple[
        DocumentProcessingStage,
        ...,
    ]:
        """Return registered stage instances."""

        return tuple(
            self._stages.values()
        )

    def registered_stages(
        self,
    ) -> tuple[str, ...]:
        """Application-facing alias for names()."""

        return self.names()

    def pipeline_stages(
        self,
    ) -> tuple[str, ...]:
        """
        Return the canonical processing-stage order.

        The order is defined by ProcessingStage, not dictionary
        registration order.
        """

        return tuple(
            stage.value
            for stage in ProcessingStage
        )

    def missing_stages(
        self,
    ) -> tuple[str, ...]:
        """Return canonical stages that are not registered."""

        registered = set(
            self._stages.keys()
        )

        return tuple(
            stage
            for stage in self.pipeline_stages()
            if stage not in registered
        )

    def is_complete(
        self,
    ) -> bool:
        """Return True if every canonical stage is registered."""

        return not self.missing_stages()

    # =========================================================================
    # PIPELINE BUILDING
    # =========================================================================

    def build_pipeline(
        self,
        stage_names: Iterable[
            str | ProcessingStage
        ],
        *,
        fail_fast: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> ProcessingPipeline:
        """
        Resolve stages and construct a ProcessingPipeline.

        The caller explicitly determines stage order.
        """

        stages = self.resolve_many(
            stage_names
        )

        if not stages:
            raise ValueError(
                "Cannot build a processing pipeline "
                "with no stages."
            )

        pipeline = ProcessingPipeline(
            stages=stages,
            fail_fast=fail_fast,
            progress_callback=progress_callback,
        )

        pipeline.validate()

        return pipeline

    def build_canonical_pipeline(
        self,
        *,
        fail_fast: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> ProcessingPipeline:
        """
        Build the complete canonical processing pipeline.
        """

        self.validate_pipeline_order()

        return self.build_pipeline(
            self.pipeline_stages(),
            fail_fast=fail_fast,
            progress_callback=progress_callback,
        )

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate(
        self,
    ) -> None:
        """
        Validate registered stage contents.

        Partial registration is allowed.

        Every registered stage must be a canonical stage.
        """

        canonical_names = set(
            self.pipeline_stages()
        )

        for name, stage in self._stages.items():

            if name not in canonical_names:
                raise ValueError(
                    f"Registered stage '{name}' is not a "
                    "canonical ProcessingStage."
                )

            self._validate_stage_instance(
                stage
            )

            actual_name = self._normalize_name(
                stage.name
            )

            if actual_name != name:
                raise ValueError(
                    "Stage registry key does not match "
                    f"stage.name: key='{name}', "
                    f"stage.name='{actual_name}'."
                )

    def validate_pipeline_order(
        self,
    ) -> None:
        """
        Validate that every canonical stage is registered.

        Registration order is NOT required to equal canonical order,
        because canonical order is explicitly defined by ProcessingStage.

        This makes registry replacement/initialization order independent
        from pipeline execution order.
        """

        self.validate()

        missing = self.missing_stages()

        if missing:
            raise ValueError(
                "Missing required processing stages: "
                f"{list(missing)}"
            )

    # =========================================================================
    # CANONICAL RESOLUTION
    # =========================================================================

    def resolve_canonical_stages(
        self,
    ) -> tuple[
        DocumentProcessingStage,
        ...,
    ]:
        """
        Resolve all canonical stages in canonical order.
        """

        self.validate_pipeline_order()

        return self.resolve_many(
            self.pipeline_stages()
        )

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def clear(self) -> None:
        """
        Remove all registered stages.

        Runtime resources owned by individual stages should be released
        by the composition root.
        """

        self._stages.clear()

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _validate_stage_instance(
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

        # Access name here so malformed implementations fail during
        # registration rather than during pipeline execution.
        name = stage.name

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Processing stage name must be a string."
            )

        if not name.strip():
            raise ValueError(
                "Processing stage name cannot be empty."
            )

    @staticmethod
    def _normalize_name(
        name: str | ProcessingStage,
    ) -> str:

        if isinstance(
            name,
            ProcessingStage,
        ):
            return name.value

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Processing stage name must be a "
                "string or ProcessingStage."
            )

        normalized = name.strip().lower()

        if not normalized:
            raise ValueError(
                "Processing stage name cannot be empty."
            )

        return normalized


__all__ = [
    "StageRegistry",
]