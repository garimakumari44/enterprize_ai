"""
Background worker responsible for fraud analysis.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.ai.risk.fraud_detector import FraudDetector
from app.events.risk_events import RiskEvents
from app.repositories.intelligence.fraud_repository import FraudRepository

logger = logging.getLogger(__name__)


class FraudWorker:
    """
    Executes fraud detection asynchronously.
    """

    def __init__(
        self,
        repository: FraudRepository,
        detector: FraudDetector,
    ):
        self.repository = repository
        self.detector = detector

    async def execute(
        self,
        case_id: UUID,
    ) -> dict:
        """
        Analyze a fraud case.
        """

        logger.info("Fraud analysis started (%s)", case_id)

        RiskEvents.fraud_analysis_started(case_id)

        try:
            case = await self.repository.get_case(case_id)

            result = await self.detector.analyze(case)

            await self.repository.save_result(
                case_id=case_id,
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                indicators=result.indicators,
                explanation=result.explanation,
            )

            RiskEvents.fraud_analysis_completed(case_id)

            logger.info("Fraud analysis completed")

            return {
                "success": True,
                "case_id": str(case_id),
                "risk_score": result.risk_score,
                "risk_level": result.risk_level,
            }

        except Exception as exc:
            logger.exception(exc)

            RiskEvents.fraud_analysis_failed(
                case_id=case_id,
                error=str(exc),
            )

            return {
                "success": False,
                "error": str(exc),
            }