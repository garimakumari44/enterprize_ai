"""
nodes/logic/wait_node.py

Wait node.

Pauses workflow execution until an external signal,
event, webhook, or user action resumes it.
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.nodes.metadata.node_categories import NodeCategory


class WaitNode(BaseNode):
    """
    Wait for an external event.

    Example configuration:

    {
        "event": "document.approved",
        "timeout": 86400,
        "resume_on_timeout": false
    }
    """

    node_type = "wait"
    display_name = "Wait"
    category = NodeCategory.LOGIC

    async def execute(self, context: NodeContext) -> NodeResult:
        config = self.config

        event_name = config.get("event")
        timeout = config.get("timeout")
        resume_on_timeout = config.get(
            "resume_on_timeout",
            False,
        )

        if not event_name:
            raise ValueError(
                "WaitNode requires an 'event' configuration."
            )

        return NodeResult.wait(
            event=event_name,
            timeout=timeout,
            resume_on_timeout=resume_on_timeout,
            output={
                "waiting_for": event_name,
                "timeout": timeout,
            },
        )