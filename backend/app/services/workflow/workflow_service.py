from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep

from app.repositories.workflow.workflow_repository import (
    WorkflowRepository,
)
from app.repositories.workflow.workflow_step_repository import (
    WorkflowStepRepository,
)


class WorkflowService:
    """
    Business logic for workflow management.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

        self.workflow_repository = WorkflowRepository(db)

        self.workflow_step_repository = WorkflowStepRepository(db)

    # ========================================================================
    # WORKFLOW CRUD
    # ========================================================================

    async def create_workflow(
        self,
        *,
        name: str,
        description: str | None = None,
        workflow_type: str,
        config: dict[str, Any] | None = None,
        is_active: bool = True,
    ) -> Workflow:

        workflow = Workflow(
            name=name,
            description=description,
            workflow_type=workflow_type,
            config=config or {},
            is_active=is_active,
        )

        return await self.workflow_repository.create(
            workflow,
        )

    async def get_workflow(
        self,
        workflow_id: UUID,
    ) -> Workflow | None:

        return await self.workflow_repository.get_by_id(
            workflow_id,
        )

    async def list_workflows(
        self,
    ) -> list[Workflow]:

        return await self.workflow_repository.get_all()

    async def update_workflow(
        self,
        workflow_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        workflow_type: str | None = None,
        config: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> Workflow:

        workflow = await self.workflow_repository.get_by_id(
            workflow_id,
        )

        if workflow is None:
            raise ValueError("Workflow not found")

        changed = False

        if name is not None:
            workflow.name = name
            changed = True

        if description is not None:
            workflow.description = description
            changed = True

        if workflow_type is not None:
            workflow.workflow_type = workflow_type
            changed = True

        if config is not None:
            workflow.config = config
            changed = True

        if is_active is not None:
            workflow.is_active = is_active
            changed = True

        if changed:
            workflow.version += 1

        return await self.workflow_repository.update(
            workflow,
        )

    async def delete_workflow(
        self,
        workflow_id: UUID,
    ) -> None:

        workflow = await self.workflow_repository.get_by_id(
            workflow_id,
        )

        if workflow is None:
            raise ValueError("Workflow not found")

        await self.workflow_repository.delete(
            workflow,
        )

    # ========================================================================
    # WORKFLOW STEPS
    # ========================================================================

    async def add_step(
        self,
        workflow_id: UUID,
        *,
        name: str,
        step_type: str,
        description: str | None = None,
        step_order: int = 0,
        is_enabled: bool = True,
        executor: str | None = None,
        config: dict[str, Any] | None = None,
        data_mapping: dict[str, Any] | None = None,
    ) -> WorkflowStep:

        workflow = await self.workflow_repository.get_by_id(
            workflow_id,
        )

        if workflow is None:
            raise ValueError("Workflow not found")

        step = WorkflowStep(
            workflow_id=workflow_id,
            name=name,
            step_type=step_type,
            description=description,
            step_order=step_order,
            is_enabled=is_enabled,
            executor=executor,
            config=config or {},
            data_mapping=data_mapping or {},
        )

        return await self.workflow_step_repository.create(
            step,
        )

    async def get_step(
        self,
        step_id: UUID,
    ) -> WorkflowStep | None:

        return await self.workflow_step_repository.get_by_id(
            step_id,
        )

    async def get_steps(
        self,
        workflow_id: UUID,
    ) -> list[WorkflowStep]:

        workflow = await self.workflow_repository.get_by_id(
            workflow_id,
        )

        if workflow is None:
            raise ValueError("Workflow not found")

        return await self.workflow_step_repository.list_by_workflow(
            workflow_id,
        )

    async def update_step(
        self,
        step_id: UUID,
        *,
        name: str | None = None,
        step_type: str | None = None,
        description: str | None = None,
        step_order: int | None = None,
        is_enabled: bool | None = None,
        executor: str | None = None,
        config: dict[str, Any] | None = None,
        data_mapping: dict[str, Any] | None = None,
    ) -> WorkflowStep:

        step = await self.workflow_step_repository.get_by_id(
            step_id,
        )

        if step is None:
            raise ValueError("Workflow step not found")

        if name is not None:
            step.name = name

        if step_type is not None:
            step.step_type = step_type

        if description is not None:
            step.description = description

        if step_order is not None:
            step.step_order = step_order

        if is_enabled is not None:
            step.is_enabled = is_enabled

        if executor is not None:
            step.executor = executor

        if config is not None:
            step.config = config

        if data_mapping is not None:
            step.data_mapping = data_mapping

        return await self.workflow_step_repository.update(
            step,
        )

    async def delete_step(
        self,
        step_id: UUID,
    ) -> None:

        step = await self.workflow_step_repository.get_by_id(
            step_id,
        )

        if step is None:
            raise ValueError("Workflow step not found")

        await self.workflow_step_repository.delete(
            step,
        )

    async def reorder_steps(
        self,
        workflow_id: UUID,
        step_ids: list[UUID],
    ) -> list[WorkflowStep]:

        workflow = await self.workflow_repository.get_by_id(
            workflow_id,
        )

        if workflow is None:
            raise ValueError("Workflow not found")

        steps = await self.workflow_step_repository.list_by_workflow(
            workflow_id,
        )

        steps_by_id = {
            step.id: step
            for step in steps
        }

        ordered_steps: list[WorkflowStep] = []

        for index, step_id in enumerate(
            step_ids,
            start=1,
        ):
            step = steps_by_id.get(step_id)

            if step is None:
                raise ValueError(
                    f"Workflow step {step_id} "
                    f"does not belong to workflow",
                )

            step.step_order = index
            ordered_steps.append(step)

        await self.workflow_step_repository.reorder(
            ordered_steps,
        )

        return ordered_steps