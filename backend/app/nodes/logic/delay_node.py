"""
nodes/logic/delay_node.py

Delay node.

Pauses workflow execution for a specified duration.
The scheduler is responsible for resuming execution.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.nodes.metadata.node_categories import NodeCategory


class DelayNode(BaseNode):
    """
    Delays workflow execution.

    Example:

    {
        "duration": 300,
        "unit": "seconds"
    }

    Supported units:
        seconds
        minutes
        hours
        days
    """

    node_type = "delay"
    display_name = "Delay"
    category = NodeCategory.LOGIC

    async def execute(self, context: NodeContext) -> NodeResult:
        config = self.config

        duration = config.get("duration", 0)
        unit = config.get("unit", "seconds")

        seconds = self._to_seconds(duration, unit)

        resume_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)

        return NodeResult.delay(
            resume_at=resume_at,
            output={
                "duration": duration,
                "unit": unit,
                "delay_seconds": seconds,
                "resume_at": resume_at.isoformat(),
            },
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _to_seconds(
        self,
        duration: int | float,
        unit: str,
    ) -> int:
        """
        Convert duration to seconds.
        """

        conversions = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400,
        }

        if unit not in conversions:
            raise ValueError(f"Unsupported delay unit: {unit}")

        return int(duration * conversions[unit])