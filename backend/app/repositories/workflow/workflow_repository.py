from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workflow import Workflow


class WorkflowRepository:
    """
    Repository for Workflow database operations.
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
        workflow: Workflow,
    ) -> Workflow:
        self.db.add(workflow)

        await self.db.flush()
        await self.db.refresh(workflow)

        return workflow

    # ============================================================
    # GET
    # ============================================================

    async def get_by_id(
        self,
        workflow_id: UUID,
    ) -> Workflow | None:
        result = await self.db.execute(
            select(Workflow).where(
                Workflow.id == workflow_id
            )
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
    ) -> list[Workflow]:
        result = await self.db.execute(
            select(Workflow).order_by(
                Workflow.created_at.desc()
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
        workflow: Workflow,
    ) -> Workflow:
        self.db.add(workflow)

        await self.db.flush()
        await self.db.refresh(workflow)

        return workflow

    # ============================================================
    # DELETE
    # ============================================================

    async def delete(
        self,
        workflow: Workflow,
    ) -> None:
        await self.db.delete(
            workflow
        )

        await self.db.flush()