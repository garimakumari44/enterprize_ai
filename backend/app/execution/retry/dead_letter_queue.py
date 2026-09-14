from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.models.execution import Execution


class DeadLetterQueue:
    """
    Handles permanently failed executions.

    Executions are moved here after all retry attempts
    have been exhausted or when the error is not retryable.
    """

    def __init__(
        self,
        session: AsyncSession
    ):
        self.session = session


    async def move_to_dead_letter(
        self,
        execution: Execution,
        reason: str
    ) -> Execution:
        """
        Mark an execution as dead-lettered.
        """

        execution.is_dead_letter = True
        execution.dead_letter_reason = reason

        self.session.add(execution)

        await self.session.commit()

        await self.session.refresh(execution)

        return execution


    async def get_execution(
        self,
        execution_id: UUID
    ) -> Optional[Execution]:
        """
        Retrieve a dead-letter execution.
        """

        result = await self.session.execute(
            select(Execution).where(
                Execution.id == execution_id,
                Execution.is_dead_letter.is_(True)
            )
        )

        return result.scalar_one_or_none()


    async def list_dead_letters(
        self
    ) -> List[Execution]:
        """
        Return all dead-letter executions.
        """

        result = await self.session.execute(
            select(Execution).where(
                Execution.is_dead_letter.is_(True)
            )
        )

        return list(result.scalars().all())


    async def restore(
        self,
        execution: Execution
    ) -> Execution:
        """
        Remove execution from the dead-letter queue.

        This allows an administrator to manually retry it.
        """

        execution.is_dead_letter = False
        execution.dead_letter_reason = None
        execution.retry_exhausted = False
        execution.retry_count = 0

        self.session.add(execution)

        await self.session.commit()

        await self.session.refresh(execution)

        return execution