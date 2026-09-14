# """
# app/services/workflow/workflow_executor.py

# Workflow execution engine.

# Architecture:

#     Database Workflow
#             |
#             v
#       WorkflowExecutor
#             |
#             +--> WorkflowRepository
#             |
#             +--> WorkflowStepRepository
#             |
#             v
#       ordered WorkflowSteps
#             |
#             v
#       WorkflowCompiler
#             |
#             v
#       StageRegistry
#             |
#             v
#       ProcessingPipeline
#             |
#             v
#       ProcessingContext
#             |
#             v
#       ProcessingStage implementations

# Responsibilities:

#     - Load persisted workflow
#     - Load persisted workflow steps
#     - Validate workflow state
#     - Preserve persisted step order
#     - Execute active/enabled workflow steps
#     - Convert processing workflow steps into compiler nodes
#     - Delegate processing execution to WorkflowCompiler
#     - Delegate actual processing execution to ProcessingPipeline
#     - Maintain shared ProcessingContext
#     - Track execution state
#     - Handle execution failures

# The executor orchestrates.

# The compiler compiles.

# The pipeline executes processing stages.

# StageRegistry resolves concrete processing stages.
# """

# from __future__ import annotations

# import logging
# from dataclasses import dataclass, field
# from typing import Any
# from uuid import UUID, uuid4

# from sqlalchemy.ext.asyncio import AsyncSession

# from app.dz
# from app.db.models.workflow_step import WorkflowStep

# from app.processing.pipeline.context import ProcessingContext
# from app.processing.stage_registry import StageRegistry
# from app.processing.workflow.compiler import (
#     CompiledWorkflow,
#     WorkflowCompilationError,
#     WorkflowCompiler,
# )

# from app.repositories.workflow.workflow_repository import (
#     WorkflowRepository,
# )
# from app.repositories.workflow.workflow_step_repository import (
#     WorkflowStepRepository,
# )


# logger = logging.getLogger(__name__)


# # ============================================================================
# # WORKFLOW EXECUTION CONTEXT
# # ============================================================================


# @dataclass
# class WorkflowExecutionContext:
#     """
#     Runtime context for one workflow execution.

#     This is the workflow-level execution context.

#     Processing stages receive the shared ProcessingContext stored
#     in ``processing_context``.
#     """

#     execution_id: UUID
#     workflow_id: UUID
#     input: dict[str, Any]

#     output: Any = None

#     steps: dict[str, dict[str, Any]] = field(
#         default_factory=dict
#     )

#     processing_context: ProcessingContext | None = None

#     def current_input(self) -> Any:
#         """
#         Return the current workflow value.

#         If a previous workflow step produced output, use that.
#         Otherwise use the original workflow input.
#         """

#         if self.output is not None:
#             return self.output

#         return self.input


# # ============================================================================
# # WORKFLOW EXECUTOR
# # ============================================================================


# class WorkflowExecutor:
#     """
#     Execute persisted workflows.

#     The executor is intentionally responsible for orchestration only.

#     Database:
#         WorkflowRepository
#         WorkflowStepRepository

#     Compilation:
#         WorkflowCompiler

#     Stage resolution:
#         StageRegistry

#     Processing execution:
#         ProcessingPipeline
#     """

#     def __init__(
#         self,
#         db: AsyncSession,
#         stage_registry: StageRegistry,
#     ) -> None:
#         """
#         Initialize the workflow executor.
#         """

#         self.db = db

#         self.workflow_repository = WorkflowRepository(
#             db
#         )

#         self.workflow_step_repository = (
#             WorkflowStepRepository(db)
#         )

#         self.stage_registry = stage_registry

#         self.compiler = WorkflowCompiler(
#             stage_registry
#         )

#     # ========================================================================
#     # PUBLIC EXECUTION API
#     # ========================================================================

#     async def execute(
#         self,
#         workflow_id: UUID,
#         *,
#         input_data: dict[str, Any] | None = None,
#     ) -> dict[str, Any]:
#         """
#         Execute a persisted workflow.
#         """

#         return await self.start_execution(
#             workflow_id,
#             input_data=input_data,
#         )

#     async def start_execution(
#         self,
#         workflow_id: UUID,
#         *,
#         input_data: dict[str, Any] | None = None,
#     ) -> dict[str, Any]:
#         """
#         Load and execute a persisted workflow.

#         Execution order is determined by WorkflowStep.step_order.
#         Disabled steps are skipped.
#         """

#         # ------------------------------------------------------------------
#         # Load workflow
#         # ------------------------------------------------------------------

#         workflow = await self.workflow_repository.get_by_id(
#             workflow_id
#         )

#         if workflow is None:
#             raise ValueError(
#                 f"Workflow '{workflow_id}' not found."
#             )

#         # ------------------------------------------------------------------
#         # Validate workflow state
#         # ------------------------------------------------------------------

#         if not workflow.is_active:
#             raise ValueError(
#                 f"Workflow '{workflow_id}' is not active."
#             )

#         # ------------------------------------------------------------------
#         # Load persisted workflow steps
#         # ------------------------------------------------------------------

#         steps = (
#             await self.workflow_step_repository.list_by_workflow(
#                 workflow_id
#             )
#         )

#         # The repository already orders by step_order.
#         # We still normalize the order here so the executor is
#         # defensive if the repository implementation changes.
#         steps = self._sort_steps(
#             steps
#         )

#         if not steps:
#             raise ValueError(
#                 f"Workflow '{workflow_id}' contains no steps."
#             )

#         # ------------------------------------------------------------------
#         # Create execution context
#         # ------------------------------------------------------------------

#         execution_id = uuid4()

#         context = WorkflowExecutionContext(
#             execution_id=execution_id,
#             workflow_id=workflow_id,
#             input=input_data or {},
#         )

#         logger.info(
#             "Starting workflow execution",
#             extra={
#                 "execution_id": str(
#                     execution_id
#                 ),
#                 "workflow_id": str(
#                     workflow_id
#                 ),
#                 "workflow_name": workflow.name,
#                 "step_count": len(steps),
#             },
#         )

#         # ------------------------------------------------------------------
#         # Execute workflow
#         # ------------------------------------------------------------------

#         try:
#             for step in steps:

#                 # ----------------------------------------------------------
#                 # Disabled workflow step
#                 # ----------------------------------------------------------

#                 if not step.is_enabled:

#                     self._mark_step_skipped(
#                         step=step,
#                         context=context,
#                     )

#                     continue

#                 # ----------------------------------------------------------
#                 # Execute active/enabled step
#                 # ----------------------------------------------------------

#                 await self._run_step(
#                     step=step,
#                     context=context,
#                 )

#         except Exception:

#             logger.exception(
#                 "Workflow execution failed",
#                 extra={
#                     "execution_id": str(
#                         execution_id
#                     ),
#                     "workflow_id": str(
#                         workflow_id
#                     ),
#                 },
#             )

#             raise

#         # ------------------------------------------------------------------
#         # Complete
#         # ------------------------------------------------------------------

#         logger.info(
#             "Workflow execution completed",
#             extra={
#                 "execution_id": str(
#                     execution_id
#                 ),
#                 "workflow_id": str(
#                     workflow_id
#                 ),
#             },
#         )

#         return self._build_execution_result(
#             workflow=workflow,
#             context=context,
#         )

#     # ========================================================================
#     # STEP EXECUTION
#     # ========================================================================

#     async def _run_step(
#         self,
#         *,
#         step: WorkflowStep,
#         context: WorkflowExecutionContext,
#     ) -> None:
#         """
#         Execute one persisted workflow step.
#         """

#         step_id = str(
#             step.id
#         )

#         logger.info(
#             "Executing workflow step",
#             extra={
#                 "execution_id": str(
#                     context.execution_id
#                 ),
#                 "workflow_id": str(
#                     context.workflow_id
#                 ),
#                 "step_id": step_id,
#                 "step_name": step.name,
#                 "step_type": step.step_type,
#                 "step_order": step.step_order,
#             },
#         )

#         context.steps[step_id] = {
#             "status": "running",
#             "step_id": step_id,
#             "name": step.name,
#             "step_type": step.step_type,
#             "step_order": step.step_order,
#         }

#         try:

#             result = await self.execute_step(
#                 step=step,
#                 context=context,
#             )

#             context.steps[step_id] = {
#                 "status": "completed",
#                 "step_id": step_id,
#                 "name": step.name,
#                 "step_type": step.step_type,
#                 "step_order": step.step_order,
#                 "result": result,
#             }

#             context.output = result

#         except Exception as exc:

#             context.steps[step_id] = {
#                 "status": "failed",
#                 "step_id": step_id,
#                 "name": step.name,
#                 "step_type": step.step_type,
#                 "step_order": step.step_order,
#                 "error": str(exc),
#             }

#             logger.exception(
#                 "Workflow step failed",
#                 extra={
#                     "execution_id": str(
#                         context.execution_id
#                     ),
#                     "workflow_id": str(
#                         context.workflow_id
#                     ),
#                     "step_id": step_id,
#                     "step_name": step.name,
#                 },
#             )

#             # Current workflow strategy is fail-fast.
#             raise

#     # ========================================================================
#     # SKIPPED STEP
#     # ========================================================================

#     @staticmethod
#     def _mark_step_skipped(
#         *,
#         step: WorkflowStep,
#         context: WorkflowExecutionContext,
#     ) -> None:
#         """
#         Mark a disabled workflow step as skipped.
#         """

#         step_id = str(
#             step.id
#         )

#         context.steps[step_id] = {
#             "status": "skipped",
#             "step_id": step_id,
#             "name": step.name,
#             "step_type": step.step_type,
#             "step_order": step.step_order,
#         }

#         logger.debug(
#             "Skipping disabled workflow step",
#             extra={
#                 "execution_id": str(
#                     context.execution_id
#                 ),
#                 "workflow_id": str(
#                     context.workflow_id
#                 ),
#                 "step_id": step_id,
#                 "step_name": step.name,
#             },
#         )

#     # ========================================================================
#     # GENERIC STEP DISPATCH
#     # ========================================================================

#     async def execute_step(
#         self,
#         *,
#         step: WorkflowStep,
#         context: WorkflowExecutionContext,
#     ) -> Any:
#         """
#         Execute one workflow step.

#         Supported workflow-level step types:

#             input
#             processing
#             ai
#             knowledge
#         """

#         step_type = self._normalize_step_type(
#             step.step_type
#         )

#         if step_type == "input":

#             return await self._execute_input_step(
#                 step=step,
#                 context=context,
#             )

#         if step_type == "processing":

#             return await self._execute_processing_step(
#                 step=step,
#                 context=context,
#             )

#         if step_type == "ai":

#             return await self._execute_ai_step(
#                 step=step,
#                 context=context,
#             )

#         if step_type == "knowledge":

#             return await self._execute_knowledge_step(
#                 step=step,
#                 context=context,
#             )

#         raise ValueError(
#             f"Unsupported workflow step type "
#             f"'{step.step_type}' for step "
#             f"'{step.name}'."
#         )

#     # ========================================================================
#     # INPUT STEP
#     # ========================================================================

#     async def _execute_input_step(
#         self,
#         *,
#         step: WorkflowStep,
#         context: WorkflowExecutionContext,
#     ) -> dict[str, Any]:
#         """
#         Execute an input step.

#         Input steps expose the original workflow input.
#         """

#         logger.debug(
#             "Executing input step",
#             extra={
#                 "execution_id": str(
#                     context.execution_id
#                 ),
#                 "step_id": str(
#                     step.id
#                 ),
#             },
#         )

#         return context.input

#     # ========================================================================
#     # PROCESSING STEP
#     # ========================================================================

#     async def _execute_processing_step(
#         self,
#         *,
#         step: WorkflowStep,
#         context: WorkflowExecutionContext,
#     ) -> dict[str, Any]:
#         """
#         Execute a persisted processing workflow step.

#         Database representation:

#             WorkflowStep(
#                 step_type="processing",
#                 name="OCR",
#                 step_order=2,
#                 config={
#                     "stage": "ocr"
#                 }
#             )

#         Compiler representation:

#             {
#                 "id": "...",
#                 "operation": "ocr"
#             }

#         Execution:

#             WorkflowCompiler
#                     |
#                     v
#             ProcessingPipeline
#                     |
#                     v
#                 OCRStage
#         """

#         logger.debug(
#             "Preparing processing workflow step",
#             extra={
#                 "execution_id": str(
#                     context.execution_id
#                 ),
#                 "step_id": str(
#                     step.id
#                 ),
#                 "step_name": step.name,
#                 "step_order": step.step_order,
#             },
#         )

#         # ------------------------------------------------------------------
#         # Ensure ProcessingContext exists
#         # ------------------------------------------------------------------

#         processing_context = (
#             self._get_or_create_processing_context(
#                 context=context,
#             )
#         )

#         # ------------------------------------------------------------------
#         # Convert persisted WorkflowStep into compiler node
#         # ------------------------------------------------------------------

#         node = self._workflow_step_to_compiler_node(
#             step
#         )

#         logger.info(
#             "Compiling workflow processing step",
#             extra={
#                 "execution_id": str(
#                     context.execution_id
#                 ),
#                 "step_id": str(
#                     step.id
#                 ),
#                 "workflow_step": step.name,
#                 "operation": node["operation"],
#             },
#         )

#         # ------------------------------------------------------------------
#         # Compile this processing step
#         #
#         # We compile one processing step at a time because the overall
#         # workflow may contain input/AI/knowledge steps between processing
#         # steps. This preserves the persisted WorkflowStep execution order.
#         # ------------------------------------------------------------------

#         try:

#             compiled: CompiledWorkflow = (
#                 self.compiler.compile_nodes(
#                     [node],
#                     fail_fast=True,
#                 )
#             )

#         except WorkflowCompilationError:

#             logger.exception(
#                 "Failed to compile workflow processing step",
#                 extra={
#                     "execution_id": str(
#                         context.execution_id
#                     ),
#                     "step_id": str(
#                         step.id
#                     ),
#                     "workflow_step": step.name,
#                 },
#             )

#             raise

#         # ------------------------------------------------------------------
#         # Execute compiled ProcessingPipeline
#         # ------------------------------------------------------------------

#         logger.info(
#             "Executing compiled processing pipeline",
#             extra={
#                 "execution_id": str(
#                     context.execution_id
#                 ),
#                 "step_id": str(
#                     step.id
#                 ),
#                 "workflow_step": step.name,
#                 "stage_names": (
#                     compiled.stage_names
#                 ),
#             },
#         )

#         result = await compiled.pipeline.execute(
#             processing_context
#         )

#         # ------------------------------------------------------------------
#         # Keep shared ProcessingContext
#         # ------------------------------------------------------------------

#         if isinstance(
#             result,
#             ProcessingContext,
#         ):
#             context.processing_context = result

#             return self._build_processing_result(
#                 stage_names=compiled.stage_names,
#                 node_ids=compiled.node_ids,
#                 processing_context=result,
#             )

#         # ------------------------------------------------------------------
#         # Defensive fallback
#         # ------------------------------------------------------------------

#         return {
#             "status": "completed",
#             "stage_names": compiled.stage_names,
#             "node_ids": compiled.node_ids,
#             "result": result,
#         }

#     # ========================================================================
#     # AI STEP
#     # ========================================================================

#     async def _execute_ai_step(
#         self,
#         *,
#         step: WorkflowStep,
#         context: WorkflowExecutionContext,
#     ) -> dict[str, Any]:
#         """
#         Execute an AI workflow step.

#         AI execution remains intentionally separate from document
#         processing until the AI pipeline is connected.
#         """

#         current_input = context.current_input()

#         logger.debug(
#             "Executing AI step",
#             extra={
#                 "execution_id": str(
#                     context.execution_id
#                 ),
#                 "step_id": str(
#                     step.id
#                 ),
#                 "step_name": step.name,
#             },
#         )

#         return {
#             "step": step.name,
#             "step_type": step.step_type,
#             "status": "completed",
#             "input": current_input,
#             "config": step.config or {},
#             "data_mapping": step.data_mapping or {},
#         }

#     # ========================================================================
#     # KNOWLEDGE STEP
#     # ========================================================================

#     async def _execute_knowledge_step(
#         self,
#         *,
#         step: WorkflowStep,
#         context: WorkflowExecutionContext,
#     ) -> dict[str, Any]:
#         """
#         Execute a knowledge/retrieval workflow step.

#         Knowledge execution remains separate from document processing
#         until the knowledge pipeline is connected.
#         """

#         current_input = context.current_input()

#         logger.debug(
#             "Executing knowledge step",
#             extra={
#                 "execution_id": str(
#                     context.execution_id
#                 ),
#                 "step_id": str(
#                     step.id
#                 ),
#                 "step_name": step.name,
#             },
#         )

#         return {
#             "step": step.name,
#             "step_type": step.step_type,
#             "status": "completed",
#             "input": current_input,
#             "config": step.config or {},
#             "data_mapping": step.data_mapping or {},
#         }

#     # ========================================================================
#     # PROCESSING CONTEXT
#     # ========================================================================

#     def _get_or_create_processing_context(
#         self,
#         *,
#         context: WorkflowExecutionContext,
#     ) -> ProcessingContext:
#         """
#         Create or return the shared ProcessingContext.

#         All processing workflow steps in one workflow execution
#         operate on the same ProcessingContext.
#         """

#         if context.processing_context is not None:
#             return context.processing_context

#         input_data = context.input

#         # ------------------------------------------------------------------
#         # document_id is required for document processing
#         # ------------------------------------------------------------------

#         document_id = input_data.get(
#             "document_id"
#         )

#         if document_id is None:
#             raise ValueError(
#                 "Processing workflow requires "
#                 "'document_id' in workflow input."
#             )

#         # ------------------------------------------------------------------
#         # Create ProcessingContext
#         # ------------------------------------------------------------------

#         processing_context = ProcessingContext(
#             document_id=str(
#                 document_id
#             ),
#             file_path=self._optional_string(
#                 input_data.get(
#                     "file_path"
#                 )
#             ),
#             file_name=self._optional_string(
#                 input_data.get(
#                     "file_name"
#                 )
#             ),
#             mime_type=self._optional_string(
#                 input_data.get(
#                     "mime_type"
#                 )
#             ),
#             file_size=self._optional_int(
#                 input_data.get(
#                     "file_size"
#                 )
#             ),
#             checksum=self._optional_string(
#                 input_data.get(
#                     "checksum"
#                 )
#             ),
#             raw_text=self._optional_string(
#                 input_data.get(
#                     "raw_text"
#                 )
#             ),
#             metadata=self._dictionary(
#                 input_data.get(
#                     "metadata"
#                 )
#             ),
#         )

#         context.processing_context = (
#             processing_context
#         )

#         return processing_context

#     # ========================================================================
#     # DATABASE STEP -> COMPILER NODE
#     # ========================================================================

#     @staticmethod
#     def _workflow_step_to_compiler_node(
#         step: WorkflowStep,
#     ) -> dict[str, Any]:
#         """
#         Convert a persisted WorkflowStep into the node format expected
#         by WorkflowCompiler.

#         WorkflowStep stores:

#             step_type
#             name
#             config

#         WorkflowCompiler expects:

#             operation
#         """

#         config = (
#             step.config
#             if isinstance(
#                 step.config,
#                 dict,
#             )
#             else {}
#         )

#         operation = (
#             config.get(
#                 "stage"
#             )
#             or config.get(
#                 "stage_name"
#             )
#         )

#         # --------------------------------------------------------------
#         # Fall back to executor/stage/name when no explicit stage exists.
#         # --------------------------------------------------------------

#         if operation is None:

#             operation = (
#                 config.get(
#                     "operation"
#                 )
#             )

#         if operation is None:

#             operation = step.name

#         if not isinstance(
#             operation,
#             str,
#         ):
#             raise ValueError(
#                 f"Invalid processing operation for workflow step "
#                 f"'{step.name}'. Expected a string."
#             )

#         operation = (
#             operation
#             .strip()
#             .lower()
#             .replace(
#                 " ",
#                 "_",
#             )
#             .replace(
#                 "-",
#                 "_",
#             )
#         )

#         if not operation:
#             raise ValueError(
#                 f"Workflow processing step "
#                 f"'{step.name}' has an empty operation."
#             )

#         return {
#             "id": str(
#                 step.id
#             ),
#             "operation": operation,
#             "config": config,
#         }

#     # ========================================================================
#     # PROCESSING RESULT
#     # ========================================================================

#     @staticmethod
#     def _build_processing_result(
#         *,
#         stage_names: tuple[str, ...],
#         node_ids: tuple[str, ...],
#         processing_context: ProcessingContext,
#     ) -> dict[str, Any]:
#         """
#         Convert ProcessingContext state into workflow step output.
#         """

#         return {
#             "status": (
#                 "failed"
#                 if processing_context.is_failed
#                 else "completed"
#             ),
#             "stage_names": stage_names,
#             "node_ids": node_ids,
#             "document": {
#                 "document_id": (
#                     processing_context.document_id
#                 ),
#                 "file_name": (
#                     processing_context.file_name
#                 ),
#                 "mime_type": (
#                     processing_context.mime_type
#                 ),
#             },
#             "classification": {
#                 "document_type": (
#                     processing_context.document_type
#                 ),
#                 "document_subtype": (
#                     processing_context.document_subtype
#                 ),
#                 "confidence": (
#                     processing_context.classification_confidence
#                 ),
#             },
#             "content": {
#                 "raw_text": (
#                     processing_context.raw_text
#                 ),
#                 "cleaned_text": (
#                     processing_context.cleaned_text
#                 ),
#             },
#             "metadata": (
#                 processing_context.metadata
#             ),
#             "extracted_data": (
#                 processing_context.extracted_data
#             ),
#             "completed_stages": (
#                 processing_context.completed_stages
#             ),
#             "failed_stages": (
#                 processing_context.failed_stages
#             ),
#             "warnings": (
#                 processing_context.warnings
#             ),
#             "errors": (
#                 processing_context.errors
#             ),
#         }

#     # ========================================================================
#     # SORTING
#     # ========================================================================

#     @staticmethod
#     def _sort_steps(
#         steps: list[WorkflowStep],
#     ) -> list[WorkflowStep]:
#         """
#         Sort persisted workflow steps by step_order.
#         """

#         return sorted(
#             steps,
#             key=lambda step: step.step_order,
#         )

#     # ========================================================================
#     # NORMALIZATION
#     # ========================================================================

#     @staticmethod
#     def _normalize_step_type(
#         step_type: str,
#     ) -> str:
#         """
#         Normalize a workflow step type.
#         """

#         if not isinstance(
#             step_type,
#             str,
#         ):
#             raise ValueError(
#                 "Workflow step type must be a string."
#             )

#         normalized = (
#             step_type
#             .strip()
#             .lower()
#         )

#         if not normalized:
#             raise ValueError(
#                 "Workflow step type cannot be empty."
#             )

#         return normalized

#     # ========================================================================
#     # TYPE HELPERS
#     # ========================================================================

#     @staticmethod
#     def _optional_string(
#         value: Any,
#     ) -> str | None:
#         """
#         Safely convert an optional value to string.
#         """

#         if value is None:
#             return None

#         if isinstance(
#             value,
#             str,
#         ):
#             return value

#         return str(value)

#     @staticmethod
#     def _optional_int(
#         value: Any,
#     ) -> int | None:
#         """
#         Safely convert an optional value to int.
#         """

#         if value is None:
#             return None

#         try:
#             return int(
#                 value
#             )

#         except (
#             TypeError,
#             ValueError,
#         ) as exc:

#             raise ValueError(
#                 f"Invalid integer value: {value!r}"
#             ) from exc

#     @staticmethod
#     def _dictionary(
#         value: Any,
#     ) -> dict[str, Any]:
#         """
#         Return a dictionary or an empty dictionary.
#         """

#         if value is None:
#             return {}

#         if not isinstance(
#             value,
#             dict,
#         ):
#             raise ValueError(
#                 "Expected a dictionary value."
#             )

#         return dict(
#             value
#         )

#     # ========================================================================
#     # PUBLIC RESULT
#     # ========================================================================

#     @staticmethod
#     def _build_execution_result(
#         *,
#         workflow: Workflow,
#         context: WorkflowExecutionContext,
#     ) -> dict[str, Any]:
#         """
#         Build the public workflow execution result.
#         """

#         processing_context = (
#             context.processing_context
#         )

#         result: dict[str, Any] = {
#             "execution_id": (
#                 context.execution_id
#             ),
#             "workflow_id": (
#                 context.workflow_id
#             ),
#             "workflow_name": (
#                 workflow.name
#             ),
#             "status": "completed",
#             "input": context.input,
#             "output": context.output,
#             "steps": context.steps,
#         }

#         # ------------------------------------------------------------------
#         # Processing information
#         # ------------------------------------------------------------------

#         if processing_context is not None:

#             result["processing"] = {
#                 "document_id": (
#                     processing_context.document_id
#                 ),
#                 "current_stage": (
#                     processing_context.current_stage
#                 ),
#                 "completed_stages": (
#                     processing_context.completed_stages
#                 ),
#                 "failed_stages": (
#                     processing_context.failed_stages
#                 ),
#                 "document_type": (
#                     processing_context.document_type
#                 ),
#                 "document_subtype": (
#                     processing_context.document_subtype
#                 ),
#                 "classification_confidence": (
#                     processing_context.classification_confidence
#                 ),
#                 "raw_text": (
#                     processing_context.raw_text
#                 ),
#                 "cleaned_text": (
#                     processing_context.cleaned_text
#                 ),
#                 "metadata": (
#                     processing_context.metadata
#                 ),
#                 "extracted_data": (
#                     processing_context.extracted_data
#                 ),
#                 "stage_results": (
#                     processing_context.stage_results
#                 ),
#                 "errors": (
#                     processing_context.errors
#                 ),
#                 "warnings": (
#                     processing_context.warnings
#                 ),
#                 "duration_seconds": (
#                     processing_context.duration_seconds
#                 ),
#             }

#         return result


# __all__ = [
#     "WorkflowExecutionContext",
#     "WorkflowExecutor",
# ]