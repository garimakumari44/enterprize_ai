# workflow_engine/executor/node_executor.py

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from contracts.node import Node
from contracts.state import WorkflowState
from contracts.result import NodeExecutionResult
from contracts.enums import NodeStatus

logger = logging.getLogger(__name__)


class NodeExecutor:
    """
    Executes a single workflow node.

    Responsibilities:
    - Execute node logic
    - Capture outputs
    - Handle retries
    - Update workflow state
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def execute(
        self,
        node: Node,
        state: WorkflowState,
    ) -> NodeExecutionResult:
        """
        Execute a node with retry support.
        """

        attempt = 0

        while attempt <= self.max_retries:
            try:
                logger.info(
                    "Executing node=%s attempt=%s",
                    node.id,
                    attempt + 1,
                )

                result = await node.run(state)

                state.node_outputs[node.id] = result

                logger.info(
                    "Node completed node=%s",
                    node.id,
                )

                return NodeExecutionResult(
                    node_id=node.id,
                    status=NodeStatus.SUCCESS,
                    output=result,
                    error=None,
                    attempts=attempt + 1,
                )

            except Exception as exc:
                logger.exception(
                    "Node failed node=%s attempt=%s",
                    node.id,
                    attempt + 1,
                )

                attempt += 1

                if attempt > self.max_retries:
                    return NodeExecutionResult(
                        node_id=node.id,
                        status=NodeStatus.FAILED,
                        output=None,
                        error=str(exc),
                        attempts=attempt,
                    )

                await self._retry_wait()

        raise RuntimeError("Unexpected execution state")

    async def _retry_wait(self) -> None:
        """
        Backoff hook.
        """
        time.sleep(self.retry_delay)