"""
Background worker responsible for forecasting.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.ai.forecasting.forecasting_engine import ForecastingEngine
from app.events.risk_events import RiskEvents
from app.repositories.intelligence.forecast_repository import ForecastRepository

logger = logging.getLogger(__name__)


class ForecastingWorker:
    """
    Executes forecasting jobs asynchronously.
    """

    def __init__(
        self,
        repository: ForecastRepository,
        engine: ForecastingEngine,
    ):
        self.repository = repository
        self.engine = engine

    async def execute(
        self,
        forecast_id: UUID,
    ) -> dict:
        """
        Generate a forecast.
        """

        logger.info("Forecast generation started (%s)", forecast_id)

        RiskEvents.forecast_started(forecast_id)

        try:
            forecast = await self.repository.get_forecast(
                forecast_id
            )

            result = await self.engine.generate(
                forecast
            )

            await self.repository.save_result(
                forecast_id=forecast_id,
                values=result.values,
                confidence=result.confidence,
                summary=result.summary,
            )

            RiskEvents.forecast_completed(
                forecast_id
            )

            logger.info("Forecast generation completed")

            return {
                "success": True,
                "forecast_id": str(forecast_id),
                "confidence": result.confidence,
            }

        except Exception as exc:
            logger.exception(exc)

            RiskEvents.forecast_failed(
                forecast_id=forecast_id,
                error=str(exc),
            )

            return {
                "success": False,
                "error": str(exc),
            }