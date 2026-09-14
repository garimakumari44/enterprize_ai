import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.execution.timeout.timeout_manager import TimeoutManager

logger = logging.getLogger(__name__)


class Watchdog:
    """
    Background task responsible for monitoring
    workflow and node timeouts.

    It periodically scans active executions and
    delegates timeout handling to TimeoutManager.
    """

    def __init__(
        self,
        timeout_manager: TimeoutManager,
        check_interval: int = 5,
    ):
        self.timeout_manager = timeout_manager
        self.check_interval = check_interval

        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """
        Start watchdog loop.
        """

        if self._running:
            return

        logger.info("Starting timeout watchdog.")

        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """
        Stop watchdog loop.
        """

        logger.info("Stopping timeout watchdog.")

        self._running = False

        if self._task:
            self._task.cancel()

            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        """
        Main monitoring loop.
        """

        while self._running:

            try:
                await self.timeout_manager.check_workflow_timeouts()
                await self.timeout_manager.check_node_timeouts()

            except Exception:
                logger.exception(
                    "Timeout watchdog encountered an error."
                )

            await asyncio.sleep(self.check_interval)

    @property
    def is_running(self) -> bool:
        """
        Returns watchdog status.
        """

        return self._running

    def __repr__(self) -> str:
        return (
            f"Watchdog("
            f"running={self._running}, "
            f"interval={self.check_interval}s)"
        )