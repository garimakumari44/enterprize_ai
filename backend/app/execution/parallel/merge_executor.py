from __future__ import annotations

import copy
import logging
from enum import Enum
from typing import Any, Dict

from app.execution.parallel.execution_group import ExecutionGroup

logger = logging.getLogger(__name__)


class MergeStrategy(str, Enum):
    """
    Strategies for combining parallel branch outputs.
    """

    OVERRIDE = "override"
    PRESERVE = "preserve"
    LIST = "list"
    NAMESPACE = "namespace"
    CUSTOM = "custom"


class MergeExecutor:
    """
    Combines outputs from all completed branches into
    a single runtime context.
    """

    def __init__(
        self,
        strategy: MergeStrategy = MergeStrategy.NAMESPACE,
    ) -> None:

        self.strategy = strategy

    # ---------------------------------------------------------

    def merge(
        self,
        parent_context: Dict[str, Any],
        group: ExecutionGroup,
    ) -> Dict[str, Any]:
        """
        Merge branch outputs with the parent context.
        """

        context = copy.deepcopy(parent_context)

        if self.strategy == MergeStrategy.OVERRIDE:
            return self._merge_override(context, group)

        if self.strategy == MergeStrategy.PRESERVE:
            return self._merge_preserve(context, group)

        if self.strategy == MergeStrategy.LIST:
            return self._merge_list(context, group)

        if self.strategy == MergeStrategy.NAMESPACE:
            return self._merge_namespace(context, group)

        return context

    # ---------------------------------------------------------

    def _merge_override(
        self,
        context: Dict[str, Any],
        group: ExecutionGroup,
    ) -> Dict[str, Any]:

        for branch in group.branches:

            if not isinstance(branch.result, dict):
                continue

            context.update(branch.result)

        return context

    # ---------------------------------------------------------

    def _merge_preserve(
        self,
        context: Dict[str, Any],
        group: ExecutionGroup,
    ) -> Dict[str, Any]:

        for branch in group.branches:

            if not isinstance(branch.result, dict):
                continue

            for key, value in branch.result.items():

                context.setdefault(key, value)

        return context

    # ---------------------------------------------------------

    def _merge_list(
        self,
        context: Dict[str, Any],
        group: ExecutionGroup,
    ) -> Dict[str, Any]:

        merged = {}

        for branch in group.branches:

            if not isinstance(branch.result, dict):
                continue

            for key, value in branch.result.items():

                merged.setdefault(key, [])

                merged[key].append(value)

        context.update(merged)

        return context

    # ---------------------------------------------------------

    def _merge_namespace(
        self,
        context: Dict[str, Any],
        group: ExecutionGroup,
    ) -> Dict[str, Any]:

        namespace = {}

        for branch in group.branches:

            namespace[str(branch.branch_id)] = branch.result

        context["parallel_results"] = namespace

        return context

    # ---------------------------------------------------------

    def merge_errors(
        self,
        group: ExecutionGroup,
    ) -> Dict[str, str]:
        """
        Collect branch errors.
        """

        errors = {}

        for branch in group.branches:

            if branch.error:

                errors[str(branch.branch_id)] = branch.error

        return errors

    # ---------------------------------------------------------

    def validate(
        self,
        group: ExecutionGroup,
    ) -> bool:
        """
        Ensure every branch has finished.
        """

        return group.is_finished