"""
nodes/logic/merge_node.py

Merge node.

Waits for multiple incoming branches to complete and merges
their outputs into a single payload before continuing.
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.nodes.metadata.node_categories import NodeCategory


class MergeNode(BaseNode):
    """
    Synchronization node.

    Configuration:

    {
        "expected_inputs": 3,
        "merge_strategy": "dict"
    }

    Merge strategies:
        - dict
        - list
        - first
        - last
    """

    node_type = "merge"
    display_name = "Merge"
    category = NodeCategory.LOGIC

    MERGE_STATE_KEY = "__merge_state__"

    async def execute(self, context: NodeContext) -> NodeResult:
        config = self.config

        expected_inputs = config.get("expected_inputs", 2)
        strategy = config.get("merge_strategy", "dict")

        state = context.execution_state.setdefault(
            self.MERGE_STATE_KEY,
            {}
        )

        merge_state = state.setdefault(
            self.id,
            {
                "inputs": [],
            },
        )

        # Store current branch output
        merge_state["inputs"].append(context.inputs)

        # Still waiting for other branches
        if len(merge_state["inputs"]) < expected_inputs:
            return NodeResult.wait(
                message="Waiting for additional branches."
            )

        merged = self._merge(
            merge_state["inputs"],
            strategy,
        )

        # Cleanup
        state.pop(self.id, None)

        return NodeResult.success(
            output=merged
        )

    # ---------------------------------------------------------
    # Merge Strategies
    # ---------------------------------------------------------

    def _merge(
        self,
        inputs: list[dict[str, Any]],
        strategy: str,
    ) -> Any:

        if strategy == "list":
            return inputs

        if strategy == "first":
            return inputs[0]

        if strategy == "last":
            return inputs[-1]

        if strategy == "dict":
            merged = {}

            for item in inputs:
                merged.update(item)

            return merged

        raise ValueError(
            f"Unknown merge strategy: {strategy}"
        )