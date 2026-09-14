from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workflow_step import WorkflowStep


class WorkflowStepRepository:
    """
    Repository for WorkflowStep database operations.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    # ============================================================
    # CREATE
    # ============================================================

    async def create(
        self,
        step: WorkflowStep,
    ) -> WorkflowStep:
        self.db.add(step)

        await self.db.flush()
        await self.db.refresh(step)

        return step

    # ============================================================
    # GET
    # ============================================================

    async def get_by_id(
        self,
        step_id: UUID,
    ) -> WorkflowStep | None:
        result = await self.db.execute(
            select(WorkflowStep).where(
                WorkflowStep.id == step_id
            )
        )

        return result.scalar_one_or_none()

    async def list_by_workflow(
        self,
        workflow_id: UUID,
    ) -> list[WorkflowStep]:
        """
        Retrieve workflow steps in execution order.
        """

        result = await self.db.execute(
            select(WorkflowStep)
            .where(
                WorkflowStep.workflow_id
                == workflow_id
            )
            .order_by(
                WorkflowStep.step_order.asc()
            )
        )

        return list(
            result.scalars().all()
        )

    # ============================================================
    # UPDATE
    # ============================================================

    async def update(
        self,
        step: WorkflowStep,
    ) -> WorkflowStep:
        self.db.add(step)

        await self.db.flush()
        await self.db.refresh(step)

        return step

    # ============================================================
    # DELETE
    # ============================================================

    async def delete(
        self,
        step: WorkflowStep,
    ) -> None:
        await self.db.delete(step)

        await self.db.flush()

    # ============================================================
    # REORDER
    # ============================================================

    async def reorder(
        self,
        steps: list[WorkflowStep],
    ) -> list[WorkflowStep]:
        """
        Persist the supplied execution order.

        Step orders are stored as:

            1, 2, 3, ...
        """

        for step_order, step in enumerate(
            steps,
            start=1,
        ):
            step.step_order = step_order
            self.db.add(step)

        await self.db.flush()

        return steps