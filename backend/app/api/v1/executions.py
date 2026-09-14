"""
app/api/v1/executions.py

Execution History API.

This API exposes ProcessingJob records as workflow executions.

Endpoints
---------
GET /executions
    Return paginated execution history.

GET /executions/{execution_id}
    Return detailed execution information including
    processing steps and processing result.
"""

from __future__ import annotations

import uuid
from math import ceil
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_db
from app.db.models.processing_job import ProcessingJob

from app.schemas.executions import (
    ExecutionDetailResponse,
    ExecutionListResponse,
    ExecutionStepResponse,
    ExecutionSummaryResponse,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/executions",
)


# ============================================================
# Helpers
# ============================================================


def calculate_duration(
    started_at: Any,
    completed_at: Any,
) -> float | None:
    """
    Calculate execution duration in seconds.
    """

    if started_at is None or completed_at is None:
        return None

    return (
        completed_at - started_at
    ).total_seconds()


def get_step_duration_ms(
    step: Any,
) -> int | None:
    """
    Calculate a processing step duration.

    Prefer the persisted duration_ms value when available.
    Otherwise calculate it from timestamps.
    """

    duration_ms = getattr(
        step,
        "duration_ms",
        None,
    )

    if duration_ms is not None:
        return int(duration_ms)

    started_at = getattr(
        step,
        "started_at",
        None,
    )

    completed_at = getattr(
        step,
        "completed_at",
        None,
    )

    if started_at is None or completed_at is None:
        return None

    return int(
        (
            completed_at - started_at
        ).total_seconds()
        * 1000
    )


def serialize_step(
    step: Any,
) -> ExecutionStepResponse:
    """
    Convert ProcessingStep into ExecutionStepResponse.
    """

    return ExecutionStepResponse(
        name=step.name,
        step_order=step.step_order,
        status=str(step.status),
        provider=getattr(
            step,
            "provider",
            None,
        ),
        provider_operation=getattr(
            step,
            "provider_operation",
            None,
        ),
        attempt_count=getattr(
            step,
            "attempt_count",
            0,
        ),
        duration_ms=get_step_duration_ms(
            step
        ),
        error_code=getattr(
            step,
            "error_code",
            None,
        ),
        error_message=getattr(
            step,
            "error_message",
            None,
        ),
        created_at=getattr(
            step,
            "created_at",
            None,
        ),
        started_at=getattr(
            step,
            "started_at",
            None,
        ),
        completed_at=getattr(
            step,
            "completed_at",
            None,
        ),
    )


def get_job_steps(
    job: Any,
) -> list[Any]:
    """
    Return processing steps associated with a job.

    ProcessingJob is expected to expose a `steps`
    relationship.
    """

    steps = getattr(
        job,
        "steps",
        None,
    )

    if steps is None:
        return []

    return sorted(
        steps,
        key=lambda step: getattr(
            step,
            "step_order",
            0,
        ),
    )


def get_document_name(
    job: Any,
) -> str | None:
    """
    Resolve the document filename.

    First tries the loaded document relationship.

    Falls back to the stored processing result metadata.
    """

    document = getattr(
        job,
        "document",
        None,
    )

    if document is not None:
        for attribute in (
            "file_name",
            "filename",
            "name",
        ):
            value = getattr(
                document,
                attribute,
                None,
            )

            if value:
                return value

    result = getattr(
        job,
        "result",
        None,
    )

    if isinstance(result, dict):
        value = result.get(
            "file_name"
        )

        if value:
            return value

    return None


def get_workflow_name(
    job: Any,
) -> str | None:
    """
    Resolve workflow name.

    First tries the loaded workflow relationship.

    Falls back to the stored processing result metadata.
    """

    workflow = getattr(
        job,
        "workflow",
        None,
    )

    if workflow is not None:
        return getattr(
            workflow,
            "name",
            None,
        )

    result = getattr(
        job,
        "result",
        None,
    )

    if isinstance(result, dict):
        workflow_name = result.get(
            "workflow_name"
        )

        if workflow_name:
            return workflow_name

    return None


def get_result(
    job: Any,
) -> dict:
    """
    Normalize the stored processing result.
    """

    result = getattr(
        job,
        "result",
        None,
    )

    if isinstance(result, dict):
        return result

    return {}


def get_progress(
    job: Any,
    steps: list[Any],
) -> int:
    """
    Resolve execution progress.

    Prefer the persisted ProcessingJob.progress field.

    Otherwise derive progress from completed steps.
    """

    progress = getattr(
        job,
        "progress",
        None,
    )

    if progress is not None:
        return int(progress)

    if not steps:
        return 0

    completed = sum(
        1
        for step in steps
        if str(
            getattr(
                step,
                "status",
                "",
            )
        ).lower()
        == "completed"
    )

    return int(
        (
            completed
            / len(steps)
        )
        * 100
    )


# ============================================================
# GET /executions
# ============================================================


@router.get(
    "",
    response_model=ExecutionListResponse,
)
async def list_executions(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    status: str | None = Query(
        None,
    ),
    db: AsyncSession = Depends(
        get_async_db
    ),
) -> ExecutionListResponse:
    """
    Return paginated Execution History.

    Example:

        GET /api/v1/executions

    Optional filtering:

        GET /api/v1/executions?status=completed
    """

    # --------------------------------------------------------
    # Count
    # --------------------------------------------------------

    count_query = (
        select(
            func.count()
        )
        .select_from(
            ProcessingJob
        )
    )

    if status:
        count_query = count_query.where(
            ProcessingJob.status
            == status
        )

    count_result = await db.execute(
        count_query
    )

    total = (
        count_result.scalar()
        or 0
    )

    # --------------------------------------------------------
    # Query
    # --------------------------------------------------------

    query = (
        select(
            ProcessingJob
        )
        .options(
            selectinload(
                ProcessingJob.steps
            )
        )
        .order_by(
            ProcessingJob.created_at.desc()
        )
        .offset(
            (page - 1)
            * page_size
        )
        .limit(
            page_size
        )
    )

    if status:
        query = query.where(
            ProcessingJob.status
            == status
        )

    result = await db.execute(
        query
    )

    jobs = (
        result.scalars()
        .unique()
        .all()
    )

    # --------------------------------------------------------
    # Build response
    # --------------------------------------------------------

    items: list[
        ExecutionSummaryResponse
    ] = []

    for job in jobs:

        steps = get_job_steps(
            job
        )

        completed_steps = sum(
            1
            for step in steps
            if str(
                getattr(
                    step,
                    "status",
                    "",
                )
            ).lower()
            == "completed"
        )

        items.append(
            ExecutionSummaryResponse(
                processing_id=job.id,
                document_id=getattr(
                    job,
                    "document_id",
                    None,
                ),
                document_version_id=getattr(
                    job,
                    "document_version_id",
                    None,
                ),
                document_name=get_document_name(
                    job
                ),
                workflow_name=get_workflow_name(
                    job
                ),
                status=str(
                    job.status
                ),
                progress=get_progress(
                    job,
                    steps,
                ),
                current_stage=getattr(
                    job,
                    "current_stage",
                    None,
                ),
                error=getattr(
                    job,
                    "error",
                    None,
                ),
                started_at=getattr(
                    job,
                    "started_at",
                    None,
                ),
                completed_at=getattr(
                    job,
                    "completed_at",
                    None,
                ),
                duration_seconds=calculate_duration(
                    getattr(
                        job,
                        "started_at",
                        None,
                    ),
                    getattr(
                        job,
                        "completed_at",
                        None,
                    ),
                ),
                steps_completed=completed_steps,
                steps_total=len(
                    steps
                ),
            )
        )

    pages = (
        ceil(
            total / page_size
        )
        if total
        else 0
    )

    return ExecutionListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


# ============================================================
# GET /executions/{execution_id}
# ============================================================


@router.get(
    "/{execution_id}",
    response_model=ExecutionDetailResponse,
)
async def get_execution(
    execution_id: uuid.UUID,
    db: AsyncSession = Depends(
        get_async_db
    ),
) -> ExecutionDetailResponse:
    """
    Return detailed execution information.

    Example:

        GET /api/v1/executions/
        e8c24a9d-b9c8-4cfc-a4cd-2f9d6bd70a06
    """

    query = (
        select(
            ProcessingJob
        )
        .options(
            selectinload(
                ProcessingJob.steps
            )
        )
        .where(
            ProcessingJob.id
            == execution_id
        )
    )

    result = await db.execute(
        query
    )

    job = (
        result.scalars()
        .unique()
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Execution not found",
        )

    steps = get_job_steps(
        job
    )

    return ExecutionDetailResponse(
        processing_id=job.id,
        document_id=getattr(
            job,
            "document_id",
            None,
        ),
        document_version_id=getattr(
            job,
            "document_version_id",
            None,
        ),
        document_name=get_document_name(
            job
        ),
        workflow_name=get_workflow_name(
            job
        ),
        status=str(
            job.status
        ),
        progress=get_progress(
            job,
            steps,
        ),
        current_stage=getattr(
            job,
            "current_stage",
            None,
        ),
        error=getattr(
            job,
            "error",
            None,
        ),
        started_at=getattr(
            job,
            "started_at",
            None,
        ),
        completed_at=getattr(
            job,
            "completed_at",
            None,
        ),
        duration_seconds=calculate_duration(
            getattr(
                job,
                "started_at",
                None,
            ),
            getattr(
                job,
                "completed_at",
                None,
            ),
        ),
        result=get_result(
            job
        ),
        steps=[
            serialize_step(
                step
            )
            for step in steps
        ],
    )


# ============================================================
# Exports
# ============================================================

__all__ = [
    "router",
]