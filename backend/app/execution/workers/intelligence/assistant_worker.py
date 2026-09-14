"""
Background worker for AI Assistant requests.

Responsibilities
----------------
- Load session context
- Build assistant context
- Invoke the orchestration engine
- Persist conversation
- Publish events
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.assistant.orchestrator import AssistantOrchestrator
from app.events.assistant_events import AssistantEvents
from app.repositories.intelligence.assistant_repository import (
    AssistantRepository,
)

logger = logging.getLogger(__name__)


class AssistantWorker:
    """
    Executes assistant requests asynchronously.
    """

    def __init__(
        self,
        repository: AssistantRepository,
        orchestrator: AssistantOrchestrator,
    ):
        self.repository = repository
        self.orchestrator = orchestrator

    async def execute(
        self,
        session_id: UUID,
        message: str,
    ) -> dict:
        """
        Process one assistant message.
        """

        logger.info("Assistant execution started (%s)", session_id)

        AssistantEvents.execution_started(session_id)

        try:
            session = await self.repository.get_session(session_id)

            response = await self.orchestrator.run(
                session=session,
                user_message=message,
            )

            await self.repository.save_message(
                session_id=session_id,
                role="assistant",
                content=response.answer,
            )

            AssistantEvents.execution_completed(session_id)

            logger.info("Assistant execution completed")

            return {
                "success": True,
                "session_id": str(session_id),
                "response": response.answer,
            }

        except Exception as exc:

            logger.exception(exc)

            AssistantEvents.execution_failed(
                session_id=session_id,
                error=str(exc),
            )

            return {
                "success": False,
                "error": str(exc),
            }