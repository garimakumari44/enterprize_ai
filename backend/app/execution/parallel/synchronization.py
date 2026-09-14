from __future__ import annotations

import asyncio
import logging
from typing import Dict
from uuid import UUID

from app.execution.parallel.execution_group import ExecutionGroup

logger = logging.getLogger(__name__)


class SynchronizationManager:
    """
    Coordinates synchronization of parallel execution groups.

    A synchronization point (barrier) is reached when all
    branches in an ExecutionGroup have completed (successfully
    or unsuccessfully).
    """

    def __init__(self) -> None:
        self._events: Dict[UUID, asyncio.Event] = {}

    # ------------------------------------------------------------------ #

    def register_group(
        self,
        group: ExecutionGroup,
    ) -> None:
        """
        Register a new execution group.
        """

        self._events[group.group_id] = asyncio.Event()

    # ------------------------------------------------------------------ #

    def unregister_group(
        self,
        group_id: UUID,
    ) -> None:
        """
        Remove a completed group from memory.
        """

        self._events.pop(group_id, None)

    # ------------------------------------------------------------------ #

    async def notify_branch_finished(
        self,
        group: ExecutionGroup,
    ) -> None:
        """
        Notify the synchronization manager that one branch
        has finished execution.

        If all branches are complete, release the barrier.
        """

        if not group.is_finished:
            return

        event = self._events.get(group.group_id)

        if event is not None:
            logger.info(
                "Parallel group %s synchronized.",
                group.group_id,
            )
            event.set()

    # ------------------------------------------------------------------ #

    async def wait_for_group(
        self,
        group: ExecutionGroup,
    ) -> None:
        """
        Wait until every branch in the group completes.
        """

        event = self._events.get(group.group_id)

        if event is None:
            raise RuntimeError(
                f"Synchronization group {group.group_id} "
                "has not been registered."
            )

        if group.is_finished:
            event.set()

        await event.wait()

    # ------------------------------------------------------------------ #

    async def synchronize(
        self,
        group: ExecutionGroup,
    ) -> ExecutionGroup:
        """
        Convenience method used by the ParallelExecutor.

        Wait for every branch and return the group.
        """

        await self.wait_for_group(group)
        return group

    # ------------------------------------------------------------------ #

    def is_registered(
        self,
        group_id: UUID,
    ) -> bool:
        """
        Check whether a group has been registered.
        """

        return group_id in self._events

    # ------------------------------------------------------------------ #

    def active_groups(self) -> int:
        """
        Number of synchronization groups currently active.
        """

        return len(self._events)

    # ------------------------------------------------------------------ #

    def clear(self) -> None:
        """
        Clear all synchronization state.

        Primarily useful during shutdown or testing.
        """

        self._events.clear()