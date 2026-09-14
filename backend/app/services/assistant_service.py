"""
app/services/assistant_service.py

Application service for the conversational assistant.

Responsibilities
----------------
- Expose assistant functionality to API/controllers.
- Coordinate AssistantOrchestrator.
- Validate incoming assistant requests.
- Normalize assistant results.
- Keep API/FastAPI concerns outside the core assistant package.

Architecture

    API
     |
     v
AssistantService
     |
     v
AssistantOrchestrator
     |
     +------------------------+
     |                        |
     v                        v
ConversationManager      PromptBuilder
     |                        |
     +------------+-----------+
                  |
                  v
             LLMManager
                  |
                  v
             ModelRouter
                  |
                  v
           ProviderRouter
                  |
                  v
             LLM Provider

The service must NOT:
- directly call OpenRouter
- directly call an LLM provider
- build prompts
- directly manage database sessions
- contain FastAPI route logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.assistant.orchestrator import (
    AssistantOrchestrator,
    AssistantResult,
)


@dataclass
class AssistantServiceResponse:
    """
    Normalized service response.

    Provides a stable boundary between the assistant core
    and API schemas.
    """

    session_id: UUID
    role: str
    content: str
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response into a serializable dictionary.
        """

        return {
            "session_id": str(
                self.session_id
            ),
            "message": {
                "role": self.role,
                "content": self.content,
            },
            "model": self.model,
            "usage": self.usage,
            "metadata": (
                self.metadata or {}
            ),
        }


class AssistantService:
    """
    Application-level service for assistant interactions.

    The service delegates actual conversational execution
    to AssistantOrchestrator.
    """

    def __init__(
        self,
        orchestrator: AssistantOrchestrator,
    ) -> None:
        self.orchestrator = orchestrator

    # ==================================================================
    # CHAT
    # ==================================================================

    async def chat(
        self,
        *,
        message: str,
        session_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AssistantServiceResponse:
        """
        Process one assistant message.
        """

        normalized_message = (
            self._validate_message(
                message
            )
        )

        normalized_context = (
            self._normalize_context(
                context
            )
        )

        result = await self.orchestrator.run(
            session_id=session_id,
            message=normalized_message,
            context=normalized_context,
        )

        return self._normalize_result(
            result
        )

    # ==================================================================
    # SESSION OPERATIONS
    # ==================================================================

    async def create_session(
        self,
        *,
        user_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> Any:
        """
        Create a new assistant conversation session.
        """

        if user_id is not None:
            self._validate_user_id(
                user_id
            )

        normalized_context = (
            self._normalize_context(
                context
            )
        )

        return await (
            self.orchestrator
            .conversation_manager
            .create_session(
                user_id=user_id,
                context=normalized_context,
                title=title,
            )
        )

    async def list_sessions(
        self,
        *,
        user_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Any]:
        """
        Retrieve assistant conversation sessions.

        Parameters
        ----------
        user_id:
            Optional authenticated user identifier.

        limit:
            Optional maximum number of sessions.

        offset:
            Optional pagination offset.
        """

        if user_id is not None:
            self._validate_user_id(
                user_id
            )

        if limit is not None and limit <= 0:
            raise ValueError(
                "Session limit must be greater than zero."
            )

        if offset < 0:
            raise ValueError(
                "Session offset cannot be negative."
            )

        return await (
            self.orchestrator
            .conversation_manager
            .list_sessions(
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        )

    async def get_session(
        self,
        *,
        session_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Any:
        """
        Retrieve an assistant conversation session.
        """

        self._validate_session_id(
            session_id
        )

        if user_id is not None:
            self._validate_user_id(
                user_id
            )

        return await (
            self.orchestrator
            .conversation_manager
            .get_session(
                session_id,
                user_id=user_id,
            )
        )

    async def get_history(
        self,
        *,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history.
        """

        self._validate_session_id(
            session_id
        )

        if limit is not None and limit <= 0:
            raise ValueError(
                "History limit must be greater than zero."
            )

        return await (
            self.orchestrator
            .conversation_manager
            .get_history(
                session_id,
                limit=limit,
            )
        )

    async def delete_session(
        self,
        *,
        session_id: UUID,
    ) -> bool:
        """
        Delete an assistant conversation session.
        """

        self._validate_session_id(
            session_id
        )

        return await (
            self.orchestrator
            .conversation_manager
            .delete_session(
                session_id
            )
        )

    # ==================================================================
    # CONVERSATION MESSAGES
    # ==================================================================

    async def add_user_message(
        self,
        *,
        session_id: UUID,
        content: str,
    ) -> Any:
        """
        Persist a user message without executing the assistant.
        """

        self._validate_session_id(
            session_id
        )

        normalized_content = (
            self._validate_message(
                content
            )
        )

        return await (
            self.orchestrator
            .conversation_manager
            .add_user_message(
                session_id=session_id,
                content=normalized_content,
            )
        )

    async def add_assistant_message(
        self,
        *,
        session_id: UUID,
        content: str,
    ) -> Any:
        """
        Persist an assistant message without executing the assistant.
        """

        self._validate_session_id(
            session_id
        )

        normalized_content = (
            self._validate_message(
                content
            )
        )

        return await (
            self.orchestrator
            .conversation_manager
            .add_assistant_message(
                session_id=session_id,
                content=normalized_content,
            )
        )

    # ==================================================================
    # RESULT NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_result(
        result: AssistantResult,
    ) -> AssistantServiceResponse:
        """
        Convert the assistant-core result into a service response.
        """

        if not isinstance(
            result,
            AssistantResult,
        ):
            raise TypeError(
                "AssistantOrchestrator returned "
                "an invalid result."
            )

        if result.message is None:
            raise RuntimeError(
                "AssistantOrchestrator returned "
                "no message."
            )

        content = (
            result.message.content.strip()
        )

        if not content:
            raise RuntimeError(
                "AssistantOrchestrator returned "
                "an empty response."
            )

        return AssistantServiceResponse(
            session_id=result.session_id,
            role=result.message.role,
            content=content,
            model=result.model,
            usage=result.usage,
            metadata=result.metadata,
        )

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @staticmethod
    def _validate_message(
        message: str,
    ) -> str:
        """
        Validate an incoming assistant message.
        """

        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "Assistant message must be a string."
            )

        normalized = message.strip()

        if not normalized:
            raise ValueError(
                "Assistant message cannot be empty."
            )

        return normalized

    @staticmethod
    def _validate_session_id(
        session_id: UUID,
    ) -> None:
        """
        Validate session UUID.
        """

        if not isinstance(
            session_id,
            UUID,
        ):
            raise TypeError(
                "session_id must be a UUID."
            )

    @staticmethod
    def _validate_user_id(
        user_id: UUID,
    ) -> None:
        """
        Validate authenticated user UUID.
        """

        if not isinstance(
            user_id,
            UUID,
        ):
            raise TypeError(
                "user_id must be a UUID."
            )

    @staticmethod
    def _normalize_context(
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Normalize optional application context.
        """

        if context is None:
            return {}

        if not isinstance(
            context,
            dict,
        ):
            raise TypeError(
                "Assistant context must be a dictionary."
            )

        return {
            str(key).strip(): value
            for key, value in context.items()
            if key is not None
            and str(key).strip()
            and value is not None
        }


__all__ = [
    "AssistantService",
    "AssistantServiceResponse",
]