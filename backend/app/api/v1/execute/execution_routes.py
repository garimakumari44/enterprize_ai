"""
Execution API routes.

Handles workflow execution operations.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.execution.execution_service import ExecutionService
from app.repositories.execution.execution_repository import ExecutionRepository
from app.repositories.workflow.workflow_repository import WorkflowRepository


router = APIRouter(
    prefix="/executions",
    tags=["Executions"],
)


def get_execution_service(
    db: Session = Depends(get_db),
) -> ExecutionService:
    """
    Dependency injection for ExecutionService.
    """

    execution_repository = ExecutionRepository(db)
    workflow_repository = WorkflowRepository(db)

    return ExecutionService(
        execution_repository=execution_repository,
        workflow_repository=workflow_repository,
    )


@router.post(
    "/run/{workflow_id}",
    status_code=status.HTTP_201_CREATED,
)
def run_workflow(
    workflow_id: str,
    inputs: Optional[Dict[str, Any]] = None,
    service: ExecutionService = Depends(get_execution_service),
):
    """
    Execute a workflow.
    """

    try:
        return service.run_workflow(
            workflow_id=workflow_id,
            inputs=inputs,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/{execution_id}")
def get_execution(
    execution_id: str,
    service: ExecutionService = Depends(get_execution_service),
):
    """
    Get execution details.
    """

    execution = service.get_execution(execution_id)

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found.",
        )

    return execution


@router.get("/")
def list_executions(
    workflow_id: Optional[str] = Query(default=None),
    service: ExecutionService = Depends(get_execution_service),
):
    """
    List executions.
    """

    return service.list_executions(workflow_id)


@router.post("/{execution_id}/cancel")
def cancel_execution(
    execution_id: str,
    service: ExecutionService = Depends(get_execution_service),
):
    """
    Cancel an execution.
    """

    execution = service.cancel_execution(execution_id)

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found.",
        )

    return execution