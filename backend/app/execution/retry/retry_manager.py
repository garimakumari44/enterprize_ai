from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.retry.retry_policy import RetryPolicy
from app.execution.retry.exponential_backoff import ExponentialBackoff
from app.execution.retry.retry_repository import RetryRepository
from app.execution.retry.dead_letter_queue import DeadLetterQueue

from app.execution.exceptions.execution_exception import (
    ExecutionException
)


class RetryManager:
    """
    Coordinates retry handling for failed executions.
    """

    def __init__(
        self,
        session: AsyncSession
    ):
        self.repository = RetryRepository(session)

        self.dead_letter_queue = DeadLetterQueue(session)

        self.policy = RetryPolicy()

        self.backoff = ExponentialBackoff()


    async def process_failure(
        self,
        execution_id: UUID,
        error: Exception
    ):
        """
        Process a failed execution.
        """

        execution = await self.repository.get_execution(
            execution_id
        )

        if execution is None:
            raise ExecutionException(
                "Execution not found."
            )

        error_type = type(error).__name__

        current_attempt = execution.retry_count + 1

        if not self.policy.can_retry(current_attempt):

            await self.repository.mark_retry_exhausted(
                execution
            )

            await self.dead_letter_queue.move_to_dead_letter(
                execution=execution,
                reason=str(error)
            )

            return {
                "status": "dead_letter",
                "attempts": execution.retry_count,
                "reason": str(error)
            }

        if not self.policy.is_retryable_error(
            error_type
        ):

            await self.dead_letter_queue.move_to_dead_letter(
                execution=execution,
                reason=f"Non-retryable: {error_type}"
            )

            return {
                "status": "dead_letter",
                "reason": error_type
            }

        execution = await self.repository.increment_retry_count(
            execution
        )

        retry_time = self.backoff.next_retry_time(
            execution.retry_count
        )

        execution = await self.repository.update_next_retry_time(
            execution,
            retry_time
        )

        return {
            "status": "retry",
            "attempt": execution.retry_count,
            "retry_at": retry_time
        }


    async def reset(
        self,
        execution_id: UUID
    ):
        """
        Reset retry state after a successful execution.
        """

        execution = await self.repository.get_execution(
            execution_id
        )

        if execution is None:
            raise ExecutionException(
                "Execution not found."
            )

        return await self.repository.reset_retry_count(
            execution
        )