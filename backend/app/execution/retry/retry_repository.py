from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.models.execution import Execution


class RetryRepository:
    """
    Repository responsible for retry-related database operations.
    """

    def __init__(
        self,
        session: AsyncSession
    ):
        self.session = session


    async def get_execution(
        self,
        execution_id: UUID
    ) -> Optional[Execution]:
        """
        Retrieve an execution by its ID.
        """

        result = await self.session.execute(
            select(Execution).where(
                Execution.id == execution_id
            )
        )

        return result.scalar_one_or_none()


    async def increment_retry_count(
        self,
        execution: Execution
    ) -> Execution:
        """
        Increment the retry count for an execution.
        """

        execution.retry_count += 1

        self.session.add(execution)

        await self.session.commit()

        await self.session.refresh(execution)

        return execution


    async def reset_retry_count(
        self,
        execution: Execution
    ) -> Execution:
        """
        Reset retry count after successful execution.
        """

        execution.retry_count = 0

        self.session.add(execution)

        await self.session.commit()

        await self.session.refresh(execution)

        return execution


    async def update_next_retry_time(
        self,
        execution: Execution,
        retry_time
    ) -> Execution:
        """
        Store when the next retry should occur.
        """

        execution.next_retry_at = retry_time

        self.session.add(execution)

        await self.session.commit()

        await self.session.refresh(execution)

        return execution


    async def mark_retry_exhausted(
        self,
        execution: Execution
    ) -> Execution:
        """
        Mark an execution as permanently failed after
        all retry attempts have been exhausted.
        """

        execution.retry_exhausted = True

        self.session.add(execution)

        await self.session.commit()

        await self.session.refresh(execution)

        return execution