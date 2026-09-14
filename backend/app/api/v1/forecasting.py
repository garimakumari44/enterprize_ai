"""
Forecasting Service

Provides forecasting capabilities for financial,
operational, and business metrics.
"""

from __future__ import annotations

from typing import Any

from app.forecasting.forecasting_engine import ForecastingEngine


class ForecastingService:
    """Application service for forecasting."""

    def __init__(
        self,
        engine: ForecastingEngine | None = None,
    ) -> None:
        self.engine = engine or ForecastingEngine()

    async def forecast_revenue(
        self,
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Forecast future revenue.
        """
        return await self.engine.forecast_revenue(history)

    async def forecast_costs(
        self,
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Forecast future costs.
        """
        return await self.engine.forecast_costs(history)

    async def forecast_cash_flow(
        self,
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Forecast cash flow.
        """
        return await self.engine.forecast_cash_flow(history)

    async def forecast_document_volume(
        self,
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Forecast document processing volume.
        """
        return await self.engine.forecast_document_volume(history)