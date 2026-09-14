"""
Comparison Engine

Provides utilities for comparing:

- Documents
- AI responses
- Workflow outputs
- Search results
- Structured dictionaries
- Lists
- Numeric metrics

This module is intentionally generic so every application
inside the platform can reuse it.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List


@dataclass
class ComparisonResult:
    similarity: float
    added: List[Any]
    removed: List[Any]
    changed: Dict[str, Any]
    identical: bool


class ComparisonEngine:
    """
    Generic comparison engine.

    Examples

    compare_text()

    compare_dicts()

    compare_lists()

    compare_metrics()

    """

    # ---------------------------------------------------------
    # TEXT
    # ---------------------------------------------------------

    def compare_text(
        self,
        old_text: str,
        new_text: str,
    ) -> ComparisonResult:
        """
        Compare two text values.
        """

        similarity = SequenceMatcher(
            None,
            old_text,
            new_text,
        ).ratio()

        identical = old_text == new_text

        return ComparisonResult(
            similarity=round(similarity, 4),
            added=[],
            removed=[],
            changed={},
            identical=identical,
        )

    # ---------------------------------------------------------
    # LISTS
    # ---------------------------------------------------------

    def compare_lists(
        self,
        old: List[Any],
        new: List[Any],
    ) -> ComparisonResult:

        old_set = set(old)
        new_set = set(new)

        added = list(new_set - old_set)
        removed = list(old_set - new_set)

        similarity = 1.0

        if old or new:
            similarity = (
                len(old_set & new_set)
                / max(len(old_set | new_set), 1)
            )

        return ComparisonResult(
            similarity=round(similarity, 4),
            added=added,
            removed=removed,
            changed={},
            identical=not added and not removed,
        )

    # ---------------------------------------------------------
    # DICTIONARIES
    # ---------------------------------------------------------

    def compare_dicts(
        self,
        old: Dict[str, Any],
        new: Dict[str, Any],
    ) -> ComparisonResult:

        changes = {}

        keys = set(old.keys()) | set(new.keys())

        for key in keys:

            if old.get(key) != new.get(key):
                changes[key] = {
                    "old": old.get(key),
                    "new": new.get(key),
                }

        similarity = (
            (len(keys) - len(changes))
            / max(len(keys), 1)
        )

        return ComparisonResult(
            similarity=round(similarity, 4),
            added=[],
            removed=[],
            changed=changes,
            identical=len(changes) == 0,
        )

    # ---------------------------------------------------------
    # METRICS
    # ---------------------------------------------------------

    def compare_metrics(
        self,
        baseline: Dict[str, float],
        current: Dict[str, float],
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare numeric metrics.

        Example

        accuracy
        latency
        confidence
        precision
        recall
        """

        results = {}

        metrics = (
            set(baseline.keys())
            | set(current.keys())
        )

        for metric in metrics:

            old = baseline.get(metric, 0.0)
            new = current.get(metric, 0.0)

            delta = new - old

            pct = (
                (delta / old * 100)
                if old != 0
                else 0.0
            )

            results[metric] = {
                "baseline": old,
                "current": new,
                "delta": round(delta, 4),
                "percent_change": round(pct, 2),
            }

        return results

    # ---------------------------------------------------------
    # SEARCH RESULTS
    # ---------------------------------------------------------

    def compare_search_results(
        self,
        first: List[Dict[str, Any]],
        second: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compare retrieval outputs.

        Assumes each result has an 'id'.
        """

        first_ids = {x["id"] for x in first}
        second_ids = {x["id"] for x in second}

        return {
            "common": list(first_ids & second_ids),
            "added": list(second_ids - first_ids),
            "removed": list(first_ids - second_ids),
        }

    # ---------------------------------------------------------
    # AI RESPONSES
    # ---------------------------------------------------------

    def compare_responses(
        self,
        response_a: str,
        response_b: str,
    ) -> Dict[str, Any]:

        similarity = SequenceMatcher(
            None,
            response_a,
            response_b,
        ).ratio()

        longer = (
            "A"
            if len(response_a) >= len(response_b)
            else "B"
        )

        return {
            "similarity": round(similarity, 4),
            "response_a_length": len(response_a),
            "response_b_length": len(response_b),
            "longer_response": longer,
            "identical": response_a == response_b,
        }

    # ---------------------------------------------------------
    # WORKFLOW OUTPUTS
    # ---------------------------------------------------------

    def compare_workflow_outputs(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
    ) -> ComparisonResult:
        """
        Alias for structured output comparison.
        """

        return self.compare_dicts(
            first,
            second,
        )

    # ---------------------------------------------------------
    # GENERIC
    # ---------------------------------------------------------

    def compare(
        self,
        first: Any,
        second: Any,
    ) -> Any:
        """
        Automatically choose comparison strategy.
        """

        if isinstance(first, str) and isinstance(second, str):
            return self.compare_text(first, second)

        if isinstance(first, list) and isinstance(second, list):
            return self.compare_lists(first, second)

        if isinstance(first, dict) and isinstance(second, dict):
            return self.compare_dicts(first, second)

        raise TypeError(
            f"Unsupported comparison type: "
            f"{type(first)}"
        )