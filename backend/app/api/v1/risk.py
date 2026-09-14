"""
Risk Service

Coordinates enterprise risk analysis using the RiskEngine.
"""

from __future__ import annotations

from typing import Any

from app.risk.risk_engine import RiskEngine


class RiskService:
    """Application service for risk analysis."""

    def __init__(
        self,
        engine: RiskEngine | None = None,
    ) -> None:
        self.engine = engine or RiskEngine()

    async def analyze(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze document risks.
        """
        return await self.engine.calculate_risk(document)

    async def detect(
        self,
        document: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Detect identified risks.
        """
        return await self.engine.detect_risks(document)

    async def report(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Produce a complete risk report.
        """
        return await self.engine.generate_risk_report(document)