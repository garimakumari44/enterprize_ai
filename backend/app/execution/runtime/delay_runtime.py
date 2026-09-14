"""
Delay Runtime

Pauses workflow execution for a specified duration.
"""

from __future__ import annotations

import time
from typing import Any

from app.execution.runtime.base_runtime import BaseRuntime


class DelayRuntime(BaseRuntime):
    """
    Runtime for Delay nodes.

    Expected node.config:

    {
        "seconds": 10
    }

    or

    {
        "seconds": "{{wait_time}}"
    }
    """

    @property
    def node_type(self) -> str:
        return "delay"

    def execute(
        self,
        node: Any,
        execution: Any,
    ) -> dict[str, Any]:
        """
        Execute the delay node.
        """

        config = self.resolve_config(node.config)

        seconds = config.get("seconds", 0)

        try:
            seconds = float(seconds)
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid delay duration: {seconds}"
            )

        if seconds < 0:
            raise ValueError(
                "Delay duration cannot be negative."
            )

        self.log(f"Waiting {seconds} second(s)...")

        start_time = time.time()

        time.sleep(seconds)

        elapsed = round(time.time() - start_time, 3)

        output = {
            "requested_delay": seconds,
            "actual_delay": elapsed,
            "completed": True,
        }

        self.save_output(
            node_id=str(node.id),
            output=output,
        )

        self.log("Delay completed.")

        return output