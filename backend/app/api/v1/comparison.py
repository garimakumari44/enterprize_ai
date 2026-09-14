"""
Comparison Service

Provides a high-level interface for comparing documents,
datasets, and extracted business metrics.
"""

from __future__ import annotations

from typing import Any

from app.comparison.comparison_engine import ComparisonEngine


class ComparisonService:
    """Application service for comparison operations."""

    def __init__(
        self,
        engine: ComparisonEngine | None = None,
    ) -> None:
        self.engine = engine or ComparisonEngine()

    async def compare_documents(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compare two extracted documents.
        """
        return await self.engine.compare_documents(left, right)

    async def compare_metrics(
        self,
        baseline: dict[str, Any],
        current: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compare business metrics.
        """
        return await self.engine.compare_metrics(baseline, current)

    async def summarize(
        self,
        comparison: dict[str, Any],
    ) -> str:
        """
        Generate a natural language summary.
        """
        return await self.engine.generate_summary(comparison)