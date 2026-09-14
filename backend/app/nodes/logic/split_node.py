"""
nodes/logic/split_node.py

Split node.

Creates multiple parallel execution branches from a single
workflow execution.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.nodes.metadata.node_categories import NodeCategory


class SplitNode(BaseNode):
    """
    Parallel split node.

    Example configuration:

    {
        "branches": [
            "branch_a",
            "branch_b",
            "branch_c"
        ],
        "copy_variables": true
    }

    The execution engine will create one execution for each branch.
    """

    node_type = "split"
    display_name = "Split"
    category = NodeCategory.LOGIC

    async def execute(self, context: NodeContext) -> NodeResult:
        config = self.config

        branches = config.get("branches", [])
        copy_variables = config.get("copy_variables", True)

        if not branches:
            raise ValueError("Split node requires at least one branch.")

        branch_data = []

        for branch in branches:
            payload = {
                "output": branch,
                "inputs": deepcopy(context.inputs),
                "variables": (
                    deepcopy(context.variables)
                    if copy_variables
                    else context.variables
                ),
            }

            branch_data.append(payload)

        return NodeResult.success(
            output={
                "branch_count": len(branches),
                "branches": branches,
            },
            parallel_outputs=branch_data,
        )