from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db

from app.schemas.workflow.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowUpdate,
)

from app.schemas.workflow.workflow_step import (
    WorkflowStepCreate,
    WorkflowStepResponse,
    WorkflowStepUpdate,
)

from app.services.workflow.workflow_service import (
    WorkflowService,
)


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"],
)


# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_workflow_service(
    db: AsyncSession = Depends(
        get_async_db,
    ),
) -> WorkflowService:
    return WorkflowService(db)


# ============================================================================
# WORKFLOW CRUD
# ============================================================================


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    data: WorkflowCreate,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    """
    Create a workflow.
    """

    config = dict(
        data.config or {},
    )

    return await service.create_workflow(
        name=data.name,
        description=data.description,
        workflow_type=data.workflow_type,
        config=config,
        is_active=data.is_active,
    )


@router.get(
    "",
    response_model=list[WorkflowResponse],
)
async def list_workflows(
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    """
    List all workflows.
    """

    return await service.list_workflows()


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
)
async def get_workflow(
    workflow_id: UUID,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    workflow = await service.get_workflow(
        workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    return workflow


@router.patch(
    "/{workflow_id}",
    response_model=WorkflowResponse,
)
async def update_workflow(
    workflow_id: UUID,
    data: WorkflowUpdate,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    try:
        return await service.update_workflow(
            workflow_id,
            name=data.name,
            description=data.description,
            workflow_type=data.workflow_type,
            config=data.config,
            is_active=data.is_active,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workflow(
    workflow_id: UUID,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    try:
        await service.delete_workflow(
            workflow_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return None


# ============================================================================
# VALIDATION
# ============================================================================


@router.post(
    "/{workflow_id}/validate",
)
async def validate_workflow(
    workflow_id: UUID,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    workflow = await service.get_workflow(
        workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    try:
        from app.processing.workflow.compiler import (
            WorkflowCompiler,
        )

        compiler = WorkflowCompiler()

        result = compiler.validate(
            workflow,
        )

        return {
            "valid": True,
            "workflow_id": str(workflow_id),
            "result": result,
        }

    except ValueError as exc:
        return {
            "valid": False,
            "workflow_id": str(workflow_id),
            "error": str(exc),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow validation failed: {exc}",
        ) from exc


# ============================================================================
# COMPILATION
# ============================================================================


@router.post(
    "/{workflow_id}/compile",
)
async def compile_workflow(
    workflow_id: UUID,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    workflow = await service.get_workflow(
        workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    try:
        from app.processing.workflow.compiler import (
            WorkflowCompiler,
        )

        compiler = WorkflowCompiler()

        compiled_workflow = compiler.compile(
            workflow,
        )

        return {
            "workflow_id": str(workflow_id),
            "compiled": True,
            "pipeline": compiled_workflow,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow compilation failed: {exc}",
        ) from exc


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================


@router.post(
    "/{workflow_id}/execute",
)
async def execute_workflow(
    workflow_id: UUID,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    workflow = await service.get_workflow(
        workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Workflow execution must be wired through the "
            "application StageRegistry and WorkflowExecutor. "
            "Do not instantiate WorkflowExecutor directly "
            "inside this router."
        ),
    )


# ============================================================================
# WORKFLOW STEPS
# ============================================================================


@router.post(
    "/{workflow_id}/steps",
    response_model=WorkflowStepResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_step(
    workflow_id: UUID,
    data: WorkflowStepCreate,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    if data.workflow_id != workflow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "workflow_id in request body does not "
                "match workflow_id in URL"
            ),
        )

    try:
        return await service.add_step(
            workflow_id,
            name=data.name,
            step_type=data.step_type,
            description=data.description,
            step_order=data.step_order,
            is_enabled=data.is_enabled,
            executor=data.executor,
            config=data.config,
            data_mapping=data.data_mapping,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{workflow_id}/steps",
    response_model=list[WorkflowStepResponse],
)
async def list_workflow_steps(
    workflow_id: UUID,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    try:
        return await service.get_steps(
            workflow_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{workflow_id}/steps/{step_id}",
    response_model=WorkflowStepResponse,
)
async def get_workflow_step(
    workflow_id: UUID,
    step_id: UUID,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    workflow = await service.get_workflow(
        workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    step = await service.get_step(
        step_id,
    )

    if (
        step is None
        or step.workflow_id != workflow_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow step not found",
        )

    return step


@router.patch(
    "/{workflow_id}/steps/{step_id}",
    response_model=WorkflowStepResponse,
)
async def update_workflow_step(
    workflow_id: UUID,
    step_id: UUID,
    data: WorkflowStepUpdate,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    workflow = await service.get_workflow(
        workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    step = await service.get_step(
        step_id,
    )

    if (
        step is None
        or step.workflow_id != workflow_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow step not found",
        )

    try:
        return await service.update_step(
            step_id,
            name=data.name,
            step_type=data.step_type,
            description=data.description,
            step_order=data.step_order,
            is_enabled=data.is_enabled,
            executor=data.executor,
            config=data.config,
            data_mapping=data.data_mapping,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{workflow_id}/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workflow_step(
    workflow_id: UUID,
    step_id: UUID,
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
):
    workflow = await service.get_workflow(
        workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    step = await service.get_step(
        step_id,
    )

    if (
        step is None
        or step.workflow_id != workflow_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow step not found",
        )

    try:
        await service.delete_step(
            step_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return None