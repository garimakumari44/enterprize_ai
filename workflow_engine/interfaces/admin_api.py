# interfaces/admin_api.py

from fastapi import APIRouter, HTTPException

from orchestration.workflow_orchestrator import WorkflowOrchestrator
from memory.execution_memory import ExecutionMemory
from memory.state_store import StateStore

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

orchestrator = WorkflowOrchestrator()
execution_memory = ExecutionMemory()
state_store = StateStore()


@router.get("/system/status")
async def system_status():
    """
    Overall workflow engine status.
    """

    return {
        "active_workflows": orchestrator.active_workflow_count(),
        "stored_executions": execution_memory.count(),
        "stored_states": state_store.count(),
    }


@router.get("/executions")
async def list_executions():
    """
    Return all execution records.
    """

    return execution_memory.list_all()


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str):

    execution = execution_memory.get(execution_id)

    if execution is None:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )

    return execution


@router.delete("/executions/{execution_id}")
async def delete_execution(execution_id: str):

    removed = execution_memory.delete(execution_id)

    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )

    return {
        "status": "deleted",
        "execution_id": execution_id,
    }


@router.get("/states")
async def list_states():

    return state_store.list_all()


@router.get("/states/{workflow_id}")
async def get_workflow_state(workflow_id: str):

    state = state_store.get(workflow_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="State not found"
        )

    return state


@router.delete("/states/{workflow_id}")
async def clear_workflow_state(workflow_id: str):

    state_store.delete(workflow_id)

    return {
        "status": "cleared",
        "workflow_id": workflow_id,
    }


@router.post("/memory/clear")
async def clear_memory():

    execution_memory.clear()

    return {
        "status": "success",
        "message": "Execution memory cleared",
    }