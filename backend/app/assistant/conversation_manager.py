"""
app/assistant/conversation_manager.py

Conversation/session management for the assistant.

Responsibilities
----------------
- Create assistant conversation sessions.
- List assistant conversation sessions.
- Retrieve conversation sessions.
- Retrieve conversation history.
- Append user/assistant messages.
- Delete sessions.
- Keep persistence concerns behind AssistantRepository.

Architecture

    AssistantOrchestrator
             |
             v
    ConversationManager
             |
             v
    AssistantRepository
             |
             v
        Database

The ConversationManager must NOT:
- contain FastAPI logic
- directly manage SQLAlchemy sessions
- call an LLM
- build prompts
- know about OpenRouter or any LLM provider
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class ConversationMessage:
    """
    Normalized conversation message.

    This is intentionally independent of the database model.
    """

    role: str
    content: str
    created_at: Optional[datetime] = None
    message_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message into a serializable dictionary.
        """

        return {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
            "message_id": (
                str(self.message_id)
                if self.message_id is not None
                else None
            ),
        }


@dataclass
class ConversationSession:
    """
    Normalized assistant session.
    """

    session_id: UUID
    created_at: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the session into a serializable dictionary.
        """

        return {
            "session_id": str(
                self.session_id
            ),
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class ConversationManager:
    """
    Manages assistant conversation lifecycle.

    The repository is injected so this class does not depend on
    a particular persistence implementation.
    """

    VALID_ROLES = {
        "system",
        "user",
        "assistant",
    }

    def __init__(
        self,
        repository: Any,
    ) -> None:
        self.repository = repository

    # ==================================================================
    # SESSION LIFECYCLE
    # ==================================================================

    async def create_session(
        self,
        *,
        user_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> ConversationSession:
        """
        Create a new assistant conversation session.
        """

        if user_id is not None:
            self._validate_session_owner_id(
                user_id
            )

        metadata = dict(
            context or {}
        )

        repository = self.repository

        if not hasattr(
            repository,
            "create_session",
        ):
            raise RuntimeError(
                "AssistantRepository does not implement "
                "create_session()."
            )

        result = repository.create_session(
            user_id=user_id,
            title=title,
            metadata=metadata,
        )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        return self._normalize_session(
            result,
            fallback_session_id=uuid4(),
            fallback_created_at=(
                datetime.now(timezone.utc)
            ),
            fallback_metadata=metadata,
        )

    async def list_sessions(
        self,
        *,
        user_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ConversationSession]:
        """
        Retrieve assistant conversation sessions.

        Results are normalized into ConversationSession objects.
        """

        if user_id is not None:
            self._validate_session_owner_id(
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

        repository = self.repository

        if not hasattr(
            repository,
            "list_sessions",
        ):
            raise RuntimeError(
                "AssistantRepository does not implement "
                "list_sessions()."
            )

        repository_limit = (
            limit
            if limit is not None
            else 50
        )

        result = repository.list_sessions(
            user_id=user_id,
            limit=repository_limit,
            offset=offset,
        )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        if not result:
            return []

        normalized: List[
            ConversationSession
        ] = []

        for item in result:
            normalized.append(
                self._normalize_session(
                    item,
                    fallback_session_id=uuid4(),
                    fallback_created_at=(
                        datetime.now(timezone.utc)
                    ),
                    fallback_metadata={},
                )
            )

        return normalized

    async def get_session(
        self,
        session_id: UUID,
        *,
        user_id: Optional[UUID] = None,
    ) -> Optional[ConversationSession]:
        """
        Retrieve an existing assistant session.

        If user_id is provided, the session must belong to
        that user.
        """

        self._validate_session_id(
            session_id
        )

        if user_id is not None:
            self._validate_session_owner_id(
                user_id
            )

        repository = self.repository

        if (
            user_id is not None
            and hasattr(
                repository,
                "get_session_for_user",
            )
        ):
            result = repository.get_session_for_user(
                session_id=session_id,
                user_id=user_id,
            )

        elif hasattr(
            repository,
            "get_session",
        ):
            result = repository.get_session(
                session_id
            )

        else:
            raise RuntimeError(
                "AssistantRepository does not implement "
                "get_session()."
            )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        if result is None:
            return None

        return self._normalize_session(
            result,
            fallback_session_id=session_id,
            fallback_created_at=(
                datetime.now(timezone.utc)
            ),
            fallback_metadata={},
        )

    async def ensure_session(
        self,
        session_id: Optional[UUID],
        *,
        user_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ConversationSession:
        """
        Return an existing session or create a new one.
        """

        if session_id is None:
            return await self.create_session(
                user_id=user_id,
                context=context,
            )

        session = await self.get_session(
            session_id,
            user_id=user_id,
        )

        if session is None:
            raise ValueError(
                f"Assistant session "
                f"'{session_id}' was not found."
            )

        return session

    # ==================================================================
    # CONVERSATION HISTORY
    # ==================================================================

    async def get_history(
        self,
        session_id: UUID,
        *,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return normalized conversation history.
        """

        self._validate_session_id(
            session_id
        )

        if limit is not None and limit <= 0:
            raise ValueError(
                "History limit must be greater than zero."
            )

        repository = self.repository

        if hasattr(
            repository,
            "get_messages",
        ):
            repository_limit = (
                limit
                if limit is not None
                else 100
            )

            result = repository.get_messages(
                session_id=session_id,
                limit=repository_limit,
            )

            if hasattr(
                result,
                "__await__",
            ):
                result = await result

            return self._normalize_messages(
                result
            )

        if hasattr(
            repository,
            "get_history",
        ):
            result = repository.get_history(
                session_id=session_id,
                limit=limit,
            )

            if hasattr(
                result,
                "__await__",
            ):
                result = await result

            return self._normalize_messages(
                result
            )

        raise RuntimeError(
            "AssistantRepository does not implement "
            "get_messages() or get_history()."
        )

    async def get_messages(
        self,
        session_id: UUID,
        *,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Alias for get_history().
        """

        return await self.get_history(
            session_id=session_id,
            limit=limit,
        )

    # ==================================================================
    # MESSAGE PERSISTENCE
    # ==================================================================

    async def add_message(
        self,
        *,
        session_id: UUID,
        role: str,
        content: str,
    ) -> ConversationMessage:
        """
        Add a message to an existing conversation.
        """

        self._validate_session_id(
            session_id
        )

        role = self._validate_role(
            role
        )

        content = self._validate_content(
            content
        )

        session = await self.get_session(
            session_id
        )

        if session is None:
            raise ValueError(
                f"Assistant session "
                f"'{session_id}' was not found."
            )

        repository = self.repository

        if hasattr(
            repository,
            "add_message",
        ):
            result = repository.add_message(
                session_id=session_id,
                role=role,
                content=content,
            )

            if hasattr(
                result,
                "__await__",
            ):
                result = await result

            return self._normalize_message(
                result,
                fallback_role=role,
                fallback_content=content,
            )

        if hasattr(
            repository,
            "create_message",
        ):
            result = repository.create_message(
                session_id=session_id,
                role=role,
                content=content,
            )

            if hasattr(
                result,
                "__await__",
            ):
                result = await result

            return self._normalize_message(
                result,
                fallback_role=role,
                fallback_content=content,
            )

        raise RuntimeError(
            "AssistantRepository does not implement "
            "add_message() or create_message()."
        )

    async def append_message(
        self,
        *,
        session_id: UUID,
        role: str,
        content: str,
    ) -> ConversationMessage:
        """
        Alias for add_message().
        """

        return await self.add_message(
            session_id=session_id,
            role=role,
            content=content,
        )

    async def add_user_message(
        self,
        *,
        session_id: UUID,
        content: str,
    ) -> ConversationMessage:
        """
        Add a user message.
        """

        return await self.add_message(
            session_id=session_id,
            role="user",
            content=content,
        )

    async def add_assistant_message(
        self,
        *,
        session_id: UUID,
        content: str,
    ) -> ConversationMessage:
        """
        Add an assistant message.
        """

        return await self.add_message(
            session_id=session_id,
            role="assistant",
            content=content,
        )

    async def add_system_message(
        self,
        *,
        session_id: UUID,
        content: str,
    ) -> ConversationMessage:
        """
        Add a system message.
        """

        return await self.add_message(
            session_id=session_id,
            role="system",
            content=content,
        )

    # ==================================================================
    # SESSION DELETION
    # ==================================================================

    async def delete_session(
        self,
        session_id: UUID,
    ) -> bool:
        """
        Delete an assistant session and its conversation data.
        """

        self._validate_session_id(
            session_id
        )

        repository = self.repository

        if not hasattr(
            repository,
            "delete_session",
        ):
            raise RuntimeError(
                "AssistantRepository does not implement "
                "delete_session()."
            )

        result = repository.delete_session(
            session_id=session_id,
        )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        return bool(result)

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @staticmethod
    def _validate_session_id(
        session_id: UUID,
    ) -> None:
        """
        Validate a session UUID.
        """

        if not isinstance(
            session_id,
            UUID,
        ):
            raise TypeError(
                "session_id must be a UUID."
            )

    @staticmethod
    def _validate_session_owner_id(
        user_id: UUID,
    ) -> None:
        """
        Validate a user UUID.
        """

        if not isinstance(
            user_id,
            UUID,
        ):
            raise TypeError(
                "user_id must be a UUID."
            )

    @classmethod
    def _validate_role(
        cls,
        role: str,
    ) -> str:
        """
        Validate and normalize a message role.
        """

        if not isinstance(
            role,
            str,
        ):
            raise TypeError(
                "Message role must be a string."
            )

        normalized = role.strip().lower()

        if normalized not in cls.VALID_ROLES:
            raise ValueError(
                f"Invalid message role '{role}'. "
                f"Expected one of: "
                f"{', '.join(sorted(cls.VALID_ROLES))}."
            )

        return normalized

    @staticmethod
    def _validate_content(
        content: str,
    ) -> str:
        """
        Validate and normalize message content.
        """

        if not isinstance(
            content,
            str,
        ):
            raise TypeError(
                "Message content must be a string."
            )

        normalized = content.strip()

        if not normalized:
            raise ValueError(
                "Message content cannot be empty."
            )

        return normalized

    # ==================================================================
    # NORMALIZATION HELPERS
    # ==================================================================

    @staticmethod
    def _normalize_session(
        result: Any,
        *,
        fallback_session_id: UUID,
        fallback_created_at: datetime,
        fallback_metadata: Dict[str, Any],
    ) -> ConversationSession:
        """
        Convert repository output into ConversationSession.
        """

        if isinstance(
            result,
            ConversationSession,
        ):
            return result

        if isinstance(
            result,
            dict,
        ):
            raw_id = (
                result.get("session_id")
                or result.get("id")
                or fallback_session_id
            )

            raw_created_at = (
                result.get("created_at")
                or fallback_created_at
            )

            raw_metadata = (
                result.get("metadata")
                or result.get("metadata_json")
                or fallback_metadata
            )

        else:
            raw_id = (
                getattr(
                    result,
                    "session_id",
                    None,
                )
                or getattr(
                    result,
                    "id",
                    None,
                )
                or fallback_session_id
            )

            raw_created_at = (
                getattr(
                    result,
                    "created_at",
                    None,
                )
                or fallback_created_at
            )

            raw_metadata = (
                getattr(
                    result,
                    "metadata",
                    None,
                )
                or getattr(
                    result,
                    "metadata_json",
                    None,
                )
                or fallback_metadata
            )

        try:
            normalized_id = UUID(
                str(raw_id)
            )
        except (
            ValueError,
            TypeError,
        ):
            normalized_id = (
                fallback_session_id
            )

        if not isinstance(
            raw_created_at,
            datetime,
        ):
            raw_created_at = (
                fallback_created_at
            )

        if not isinstance(
            raw_metadata,
            dict,
        ):
            raw_metadata = (
                fallback_metadata
            )

        return ConversationSession(
            session_id=normalized_id,
            created_at=raw_created_at,
            metadata=dict(raw_metadata),
        )

    @staticmethod
    def _normalize_messages(
        messages: Any,
    ) -> List[Dict[str, Any]]:
        """
        Normalize repository messages into dictionaries.
        """

        if not messages:
            return []

        normalized: List[
            Dict[str, Any]
        ] = []

        for item in messages:
            message = (
                ConversationManager
                ._normalize_message(item)
            )

            if (
                message.role
                and message.content
            ):
                normalized.append(
                    {
                        "role": message.role,
                        "content": message.content,
                    }
                )

        return normalized

    @staticmethod
    def _normalize_message(
        result: Any,
        *,
        fallback_role: Optional[str] = None,
        fallback_content: Optional[str] = None,
    ) -> ConversationMessage:
        """
        Convert repository message output into
        ConversationMessage.
        """

        if isinstance(
            result,
            ConversationMessage,
        ):
            return result

        if result is None:
            return ConversationMessage(
                role=(
                    fallback_role
                    or "assistant"
                ),
                content=(
                    fallback_content
                    or ""
                ),
                created_at=(
                    datetime.now(
                        timezone.utc
                    )
                ),
            )

        if isinstance(
            result,
            dict,
        ):
            role = (
                result.get("role")
                or fallback_role
            )

            content = (
                result.get("content")
                or fallback_content
            )

            created_at = result.get(
                "created_at"
            )

            message_id = (
                result.get("message_id")
                or result.get("id")
            )

        else:
            role = (
                getattr(
                    result,
                    "role",
                    None,
                )
                or fallback_role
            )

            content = (
                getattr(
                    result,
                    "content",
                    None,
                )
                or fallback_content
            )

            created_at = getattr(
                result,
                "created_at",
                None,
            )

            message_id = (
                getattr(
                    result,
                    "message_id",
                    None,
                )
                or getattr(
                    result,
                    "id",
                    None,
                )
            )

        try:
            normalized_id = (
                UUID(
                    str(message_id)
                )
                if message_id is not None
                else None
            )
        except (
            ValueError,
            TypeError,
        ):
            normalized_id = None

        if not isinstance(
            created_at,
            datetime,
        ):
            created_at = None

        return ConversationMessage(
            role=str(
                role or "assistant"
            ),
            content=str(
                content or ""
            ),
            created_at=created_at,
            message_id=normalized_id,
        )


__all__ = [
    "ConversationManager",
    "ConversationMessage",
    "ConversationSession",
]