"""
nodes/logic/parallel_node.py

Parallel node.

Schedules multiple tasks for concurrent execution and allows
the execution engine to synchronize them.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.nodes.metadata.node_categories import NodeCategory


class ParallelNode(BaseNode):
    """
    Parallel execution node.

    Example configuration:

    {
        "tasks": [
            "extract_text",
            "generate_embedding",
            "classify_document"
        ],
        "wait_for_all": True,
        "copy_variables": True
    }
    """

    node_type = "parallel"
    display_name = "Parallel"
    category = NodeCategory.LOGIC

    async def execute(self, context: NodeContext) -> NodeResult:
        config = self.config

        tasks = config.get("tasks", [])
        wait_for_all = config.get("wait_for_all", True)
        copy_variables = config.get("copy_variables", True)

        if not tasks:
            raise ValueError(
                "ParallelNode requires at least one task."
            )

        parallel_tasks = []

        for task in tasks:
            parallel_tasks.append(
                {
                    "output": task,
                    "inputs": deepcopy(context.inputs),
                    "variables": (
                        deepcopy(context.variables)
                        if copy_variables
                        else context.variables
                    ),
                }
            )

        return NodeResult.success(
            output={
                "task_count": len(tasks),
                "wait_for_all": wait_for_all,
            },
            parallel_outputs=parallel_tasks,
            metadata={
                "wait_for_all": wait_for_all,
            },
        )