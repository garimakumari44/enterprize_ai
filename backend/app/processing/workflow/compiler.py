"""
app/processing/workflow/compiler.py

Compiles workflow definitions into executable document-processing
pipelines.

Architecture:

    WorkflowDefinition
            |
            v
    WorkflowCompiler
            |
            v
       StageRegistry
            |
            v
    ProcessingPipeline
            |
            v
      DocumentProcessor


Responsibilities:

    - Validate workflow definitions
    - Resolve workflow nodes to canonical processing stages
    - Resolve stages through StageRegistry
    - Preserve workflow node order
    - Build ProcessingPipeline instances
    - Support custom workflow configurations
    - Never execute processing stages

Execution belongs to:

    ProcessingPipeline.execute()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from app.core.constants import ProcessingStage
from app.processing.pipeline.pipeline import (
    DocumentProcessingStage,
    PipelineBuilder,
    ProcessingPipeline,
)
from app.processing.stage_registry import StageRegistry


# ======================================================================
# WORKFLOW COMPILATION ERROR
# ======================================================================


class WorkflowCompilationError(ValueError):
    """
    Raised when a workflow cannot be compiled into a processing pipeline.
    """

    pass


# ======================================================================
# COMPILED WORKFLOW
# ======================================================================


@dataclass(frozen=True)
class CompiledWorkflow:
    """
    Result of compiling a workflow.

    Attributes
    ----------
    pipeline:
        Executable ProcessingPipeline.

    stage_names:
        Canonical names of the stages in execution order.

    node_ids:
        IDs of the workflow nodes used to create the pipeline.
    """

    pipeline: ProcessingPipeline
    stage_names: tuple[str, ...]
    node_ids: tuple[str, ...]


# ======================================================================
# WORKFLOW COMPILER
# ======================================================================


class WorkflowCompiler:
    """
    Compile workflow definitions into ProcessingPipeline instances.

    The compiler is deliberately independent from the HTTP layer
    and database layer.

    It receives:

        workflow nodes
        StageRegistry

    and produces:

        ProcessingPipeline
    """

    # ------------------------------------------------------------------
    # WORKFLOW OPERATION -> PROCESSING STAGE
    # ------------------------------------------------------------------

    OPERATION_TO_STAGE: dict[str, str] = {
        # Layout
        "layout_analysis": ProcessingStage.LAYOUT_ANALYSIS.value,
        "layout": ProcessingStage.LAYOUT_ANALYSIS.value,

        # Extraction
        "text_extraction": ProcessingStage.TEXT_EXTRACTION.value,
        "text_extraction_pdf": ProcessingStage.TEXT_EXTRACTION.value,
        "extract_text": ProcessingStage.TEXT_EXTRACTION.value,
        "extraction": ProcessingStage.TEXT_EXTRACTION.value,

        # OCR
        "ocr": ProcessingStage.OCR.value,
        "ocr_processing": ProcessingStage.OCR.value,

        # Structure
        "structure_detection": (
            ProcessingStage.STRUCTURE_DETECTION.value
        ),
        "structure": ProcessingStage.STRUCTURE_DETECTION.value,

        # Cleaning
        "cleaning": ProcessingStage.CLEANING.value,
        "clean": ProcessingStage.CLEANING.value,
        "normalization": ProcessingStage.CLEANING.value,

        # Chunking
        "chunking": ProcessingStage.CHUNKING.value,
        "chunk": ProcessingStage.CHUNKING.value,

        # Metadata
        "metadata_enrichment": (
            ProcessingStage.METADATA_ENRICHMENT.value
        ),
        "metadata": ProcessingStage.METADATA_ENRICHMENT.value,
        "enrichment": ProcessingStage.METADATA_ENRICHMENT.value,

        # Embedding
        "embedding": ProcessingStage.EMBEDDING.value,
        "embeddings": ProcessingStage.EMBEDDING.value,

        # Indexing
        "indexing": ProcessingStage.INDEXING.value,
        "vector_indexing": ProcessingStage.INDEXING.value,
    }

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------

    def __init__(
        self,
        registry: StageRegistry,
    ) -> None:
        """
        Initialize the compiler.

        Parameters
        ----------
        registry:
            Central StageRegistry containing concrete stage
            implementations.
        """

        if not isinstance(
            registry,
            StageRegistry,
        ):
            raise TypeError(
                "registry must be an instance of StageRegistry."
            )

        self.registry = registry

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    @staticmethod
    def normalize_operation(
        operation: str | ProcessingStage,
    ) -> str:
        """
        Normalize a workflow operation.

        Examples:

            "OCR"
            "ocr"
            ProcessingStage.OCR

        all resolve to:

            "ocr"
        """

        if isinstance(
            operation,
            ProcessingStage,
        ):
            return operation.value

        if not isinstance(
            operation,
            str,
        ):
            raise TypeError(
                "Workflow operation must be a string "
                "or ProcessingStage."
            )

        normalized = operation.strip().lower()

        if not normalized:
            raise ValueError(
                "Workflow operation cannot be empty."
            )

        return normalized

    # ==================================================================
    # RESOLVE OPERATION
    # ==================================================================

    def resolve_stage_name(
        self,
        operation: str | ProcessingStage,
    ) -> str:
        """
        Convert a workflow operation into a canonical processing
        stage name.

        Examples:

            "ocr"
                -> "ocr"

            "OCR"
                -> "ocr"

            "extract_text"
                -> "text_extraction"
        """

        normalized_operation = self.normalize_operation(
            operation
        )

        # Direct canonical stage name.
        if normalized_operation in {
            stage.value
            for stage in ProcessingStage
        }:
            return normalized_operation

        # Workflow operation alias.
        try:
            return self.OPERATION_TO_STAGE[
                normalized_operation
            ]

        except KeyError as exc:
            supported = ", ".join(
                sorted(
                    self.OPERATION_TO_STAGE.keys()
                )
            )

            raise WorkflowCompilationError(
                "Unknown workflow operation "
                f"'{normalized_operation}'. "
                f"Supported operations: {supported}."
            ) from exc

    # ==================================================================
    # RESOLVE STAGE
    # ==================================================================

    def resolve_stage(
        self,
        operation: str | ProcessingStage,
    ) -> DocumentProcessingStage:
        """
        Resolve a workflow operation to a registered processing stage.
        """

        stage_name = self.resolve_stage_name(
            operation
        )

        if not self.registry.has(
            stage_name
        ):
            missing = self.registry.missing_stages()

            raise WorkflowCompilationError(
                "Workflow operation "
                f"'{operation}' resolves to processing stage "
                f"'{stage_name}', but that stage is not registered. "
                f"Missing stages: "
                f"{', '.join(missing) if missing else 'none'}."
            )

        return self.registry.get(
            stage_name
        )

    # ==================================================================
    # VALIDATE WORKFLOW NODE
    # ==================================================================

    @staticmethod
    def validate_node(
        node: Mapping[str, Any],
        index: int,
    ) -> None:
        """
        Validate an individual workflow node.

        A node must contain:

            operation

        ID is recommended but not strictly required because some
        frontend-created nodes may not have persistent IDs yet.
        """

        if not isinstance(
            node,
            Mapping,
        ):
            raise WorkflowCompilationError(
                f"Workflow node at index {index} "
                "must be an object."
            )

        operation = node.get(
            "operation"
        )

        if operation is None:
            raise WorkflowCompilationError(
                f"Workflow node at index {index} "
                "is missing 'operation'."
            )

        if not isinstance(
            operation,
            (
                str,
                ProcessingStage,
            ),
        ):
            raise WorkflowCompilationError(
                f"Workflow node at index {index} "
                "'operation' must be a string or ProcessingStage."
            )

    # ==================================================================
    # EXTRACT NODES
    # ==================================================================

    @staticmethod
    def extract_nodes(
        workflow: Any,
    ) -> Sequence[Any]:
        """
        Extract workflow nodes from a workflow definition.

        Supports:

            workflow.nodes

        and:

            workflow.config["nodes"]

        This makes the compiler compatible with both the frontend
        WorkflowDefinition and the backend persisted Workflow model.
        """

        # --------------------------------------------------------------
        # Object-style workflow
        # --------------------------------------------------------------

        nodes = getattr(
            workflow,
            "nodes",
            None,
        )

        if nodes is not None:
            return nodes

        # --------------------------------------------------------------
        # Dictionary-style workflow
        # --------------------------------------------------------------

        if isinstance(
            workflow,
            Mapping,
        ):
            nodes = workflow.get(
                "nodes"
            )

            if nodes is not None:
                return nodes

            config = workflow.get(
                "config"
            )

            if isinstance(
                config,
                Mapping,
            ):
                nodes = config.get(
                    "nodes"
                )

                if nodes is not None:
                    return nodes

        # --------------------------------------------------------------
        # Object with config attribute
        # --------------------------------------------------------------

        config = getattr(
            workflow,
            "config",
            None,
        )

        if isinstance(
            config,
            Mapping,
        ):
            nodes = config.get(
                "nodes"
            )

            if nodes is not None:
                return nodes

        return ()

    # ==================================================================
    # COMPILE NODES
    # ==================================================================

    def compile_nodes(
        self,
        nodes: Sequence[Any],
        *,
        fail_fast: bool = True,
    ) -> CompiledWorkflow:
        """
        Compile workflow nodes into a ProcessingPipeline.

        Node order is preserved exactly.

        Example:

            [
                {"id": "1", "operation": "ocr"},
                {"id": "2", "operation": "cleaning"},
                {"id": "3", "operation": "chunking"},
                {"id": "4", "operation": "embedding"},
            ]

        becomes:

            OCRStage
                |
                v
            CleaningStage
                |
                v
            ChunkingStage
                |
                v
            EmbeddingStage
        """

        if nodes is None:
            raise WorkflowCompilationError(
                "Workflow nodes cannot be None."
            )

        if not isinstance(
            nodes,
            Sequence,
        ):
            raise WorkflowCompilationError(
                "Workflow nodes must be a sequence."
            )

        if len(nodes) == 0:
            raise WorkflowCompilationError(
                "Workflow contains no processing nodes."
            )

        stages: list[
            DocumentProcessingStage
        ] = []

        stage_names: list[str] = []

        node_ids: list[str] = []

        for index, raw_node in enumerate(
            nodes
        ):
            # ----------------------------------------------------------
            # Object -> mapping
            # ----------------------------------------------------------

            if isinstance(
                raw_node,
                Mapping,
            ):
                node = raw_node

            else:
                node = self._object_to_mapping(
                    raw_node
                )

            self.validate_node(
                node,
                index,
            )

            operation = node[
                "operation"
            ]

            # ----------------------------------------------------------
            # Resolve stage
            # ----------------------------------------------------------

            stage_name = self.resolve_stage_name(
                operation
            )

            # ----------------------------------------------------------
            # Resolve implementation
            # ----------------------------------------------------------

            stage = self.resolve_stage(
                stage_name
            )

            # ----------------------------------------------------------
            # Duplicate stages
            # ----------------------------------------------------------

            if stage_name in stage_names:
                raise WorkflowCompilationError(
                    "Workflow contains duplicate processing stage "
                    f"'{stage_name}' at node index {index}. "
                    "A processing stage may only appear once in "
                    "a compiled pipeline."
                )

            stages.append(
                stage
            )

            stage_names.append(
                stage_name
            )

            # ----------------------------------------------------------
            # Node ID
            # ----------------------------------------------------------

            node_id = node.get(
                "id"
            )

            if node_id is None:
                node_ids.append(
                    str(index)
                )
            else:
                node_ids.append(
                    str(node_id)
                )

        # --------------------------------------------------------------
        # Build pipeline
        # --------------------------------------------------------------

        try:
            pipeline = PipelineBuilder.build(
                stages=stages,
                fail_fast=fail_fast,
            )

        except (
            ValueError,
            TypeError,
        ) as exc:
            raise WorkflowCompilationError(
                "Failed to build processing pipeline: "
                f"{exc}"
            ) from exc

        return CompiledWorkflow(
            pipeline=pipeline,
            stage_names=tuple(
                stage_names
            ),
            node_ids=tuple(
                node_ids
            ),
        )

    # ==================================================================
    # COMPILE WORKFLOW
    # ==================================================================

    def compile(
        self,
        workflow: Any,
        *,
        fail_fast: bool = True,
    ) -> ProcessingPipeline:
        """
        Compile a complete workflow into a ProcessingPipeline.

        The returned pipeline is ready for execution:

            pipeline = compiler.compile(workflow)

            result = await pipeline.execute(context)

        The compiler itself does not execute anything.
        """

        nodes = self.extract_nodes(
            workflow
        )

        compiled = self.compile_nodes(
            nodes,
            fail_fast=fail_fast,
        )

        return compiled.pipeline

    # ==================================================================
    # COMPILE WITH METADATA
    # ==================================================================

    def compile_with_metadata(
        self,
        workflow: Any,
        *,
        fail_fast: bool = True,
    ) -> CompiledWorkflow:
        """
        Compile a workflow and return both the pipeline and
        compilation metadata.
        """

        nodes = self.extract_nodes(
            workflow
        )

        return self.compile_nodes(
            nodes,
            fail_fast=fail_fast,
        )

    # ==================================================================
    # CANONICAL PIPELINE
    # ==================================================================

    def compile_default(
        self,
        *,
        fail_fast: bool = True,
    ) -> ProcessingPipeline:
        """
        Compile the complete canonical document-processing pipeline.

        This uses StageRegistry.build_pipeline() and therefore follows:

            layout_analysis
            text_extraction
            ocr
            structure_detection
            cleaning
            chunking
            metadata_enrichment
            embedding
            indexing
        """

        try:
            return self.registry.build_pipeline(
                fail_fast=fail_fast,
            )

        except (
            RuntimeError,
            ValueError,
            TypeError,
        ) as exc:
            raise WorkflowCompilationError(
                "Failed to compile the default document "
                f"processing pipeline: {exc}"
            ) from exc

    # ==================================================================
    # VALIDATE WORKFLOW
    # ==================================================================

    def validate(
        self,
        workflow: Any,
    ) -> tuple[str, ...]:
        """
        Validate a workflow without returning an executable pipeline.

        Returns:

            tuple of resolved canonical stage names.
        """

        nodes = self.extract_nodes(
            workflow
        )

        if not nodes:
            raise WorkflowCompilationError(
                "Workflow contains no processing nodes."
            )

        stage_names: list[str] = []

        for index, raw_node in enumerate(
            nodes
        ):
            if isinstance(
                raw_node,
                Mapping,
            ):
                node = raw_node
            else:
                node = self._object_to_mapping(
                    raw_node
                )

            self.validate_node(
                node,
                index,
            )

            stage_name = self.resolve_stage_name(
                node["operation"]
            )

            if not self.registry.has(
                stage_name
            ):
                raise WorkflowCompilationError(
                    f"Node {index} requires stage "
                    f"'{stage_name}', but it is not registered."
                )

            if stage_name in stage_names:
                raise WorkflowCompilationError(
                    f"Duplicate processing stage "
                    f"'{stage_name}' in workflow."
                )

            stage_names.append(
                stage_name
            )

        return tuple(
            stage_names
        )

    # ==================================================================
    # OBJECT NORMALIZATION
    # ==================================================================

    @staticmethod
    def _object_to_mapping(
        node: Any,
    ) -> dict[str, Any]:
        """
        Convert a Pydantic/dataclass/object workflow node into
        a mapping.

        Supports:

            Pydantic v2 -> model_dump()
            Pydantic v1 -> dict()
            regular object -> __dict__
        """

        if hasattr(
            node,
            "model_dump",
        ):
            result = node.model_dump()

            if isinstance(
                result,
                dict,
            ):
                return result

        if hasattr(
            node,
            "dict",
        ):
            result = node.dict()

            if isinstance(
                result,
                dict,
            ):
                return result

        if hasattr(
            node,
            "__dict__",
        ):
            return dict(
                vars(node)
            )

        raise WorkflowCompilationError(
            "Workflow node must be a mapping or "
            "an object that can be converted to a mapping."
        )


# ======================================================================
# CONVENIENCE FUNCTION
# ======================================================================


def compile_workflow(
    workflow: Any,
    registry: StageRegistry,
    *,
    fail_fast: bool = True,
) -> ProcessingPipeline:
    """
    Convenience function for compiling a workflow.

    Example:

        pipeline = compile_workflow(
            workflow,
            registry,
        )

        result = await pipeline.execute(
            context
        )
    """

    compiler = WorkflowCompiler(
        registry
    )

    return compiler.compile(
        workflow,
        fail_fast=fail_fast,
    )


# ======================================================================
# EXPORTS
# ======================================================================


__all__ = [
    "WorkflowCompilationError",
    "CompiledWorkflow",
    "WorkflowCompiler",
    "compile_workflow",
]