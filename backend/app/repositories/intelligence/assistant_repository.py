"""
app/repositories/intelligence/assistant_repository.py

Repository for Assistant sessions and conversation messages.

Responsibilities
----------------
- Create and retrieve assistant sessions.
- List assistant sessions.
- Store conversation messages.
- Retrieve conversation history.
- Update session metadata.
- Keep database access isolated from AssistantService.

Architecture
------------

    AssistantService
           |
           v
    ConversationManager
           |
           v
    AssistantRepository
           |
           v
      AsyncSession
           |
           v
        Database

The repository owns persistence only.
It must not contain orchestration, LLM, prompt, or FastAPI logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assistant import (
    AssistantMessage,
    AssistantSession,
)


class AssistantRepository:
    """
    Database repository for the Assistant subsystem.

    This class contains persistence logic only.

    Business logic belongs in:
        - AssistantService
        - ConversationManager
        - AssistantOrchestrator
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        """
        Initialize the repository with a request-scoped
        SQLAlchemy AsyncSession.
        """

        self.db = db

    # ==================================================================
    # SESSION METHODS
    # ==================================================================

    async def create_session(
        self,
        *,
        user_id: Optional[UUID] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AssistantSession:
        """
        Create a new assistant conversation session.

        Parameters
        ----------
        user_id:
            Optional authenticated user identifier.

        title:
            Optional human-readable session title.

        metadata:
            Optional session metadata.
        """

        session = AssistantSession(
            user_id=user_id,
            title=title,
            metadata_json=dict(metadata or {}),
        )

        self.db.add(session)

        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def get_session(
        self,
        session_id: UUID,
    ) -> Optional[AssistantSession]:
        """
        Retrieve an assistant session by ID.
        """

        result = await self.db.execute(
            select(AssistantSession).where(
                AssistantSession.id == session_id
            )
        )

        return result.scalar_one_or_none()

    async def get_session_for_user(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
    ) -> Optional[AssistantSession]:
        """
        Retrieve a session belonging to a specific user.
        """

        result = await self.db.execute(
            select(AssistantSession).where(
                AssistantSession.id == session_id,
                AssistantSession.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        *,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AssistantSession]:
        """
        List assistant sessions.

        Results are returned newest first.

        If user_id is supplied, only sessions belonging to that
        user are returned.
        """

        if limit <= 0:
            raise ValueError(
                "Session limit must be greater than zero."
            )

        if offset < 0:
            raise ValueError(
                "Session offset cannot be negative."
            )

        query = select(AssistantSession)

        if user_id is not None:
            query = query.where(
                AssistantSession.user_id == user_id
            )

        query = (
            query
            .order_by(
                AssistantSession.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)

        return list(
            result.scalars().all()
        )

    async def update_session(
        self,
        *,
        session_id: UUID,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[AssistantSession]:
        """
        Update session information.
        """

        session = await self.get_session(
            session_id
        )

        if session is None:
            return None

        if title is not None:
            session.title = title

        if metadata is not None:
            session.metadata_json = dict(metadata)

        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def delete_session(
        self,
        session_id: UUID,
    ) -> bool:
        """
        Delete an assistant session.

        Returns
        -------
        bool
            True when a session was deleted.
            False when the session did not exist.
        """

        session = await self.get_session(
            session_id
        )

        if session is None:
            return False

        await self.db.delete(session)
        await self.db.flush()

        return True

    # ==================================================================
    # MESSAGE METHODS
    # ==================================================================

    async def add_message(
        self,
        *,
        session_id: UUID,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AssistantMessage:
        """
        Store a single conversation message.
        """

        message = AssistantMessage(
            session_id=session_id,
            role=role,
            content=content,
            metadata_json=dict(metadata or {}),
        )

        self.db.add(message)

        await self.db.flush()
        await self.db.refresh(message)

        return message

    async def get_message(
        self,
        message_id: UUID,
    ) -> Optional[AssistantMessage]:
        """
        Retrieve a single assistant message.
        """

        result = await self.db.execute(
            select(AssistantMessage).where(
                AssistantMessage.id == message_id
            )
        )

        return result.scalar_one_or_none()

    async def get_messages(
        self,
        session_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AssistantMessage]:
        """
        Retrieve conversation history for a session.

        Messages are returned oldest first so they can be passed
        directly to the conversation manager / LLM.
        """

        if limit <= 0:
            raise ValueError(
                "Message limit must be greater than zero."
            )

        if offset < 0:
            raise ValueError(
                "Message offset cannot be negative."
            )

        result = await self.db.execute(
            select(AssistantMessage)
            .where(
                AssistantMessage.session_id == session_id
            )
            .order_by(
                AssistantMessage.created_at.asc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )

    async def get_recent_messages(
        self,
        session_id: UUID,
        *,
        limit: int = 20,
    ) -> List[AssistantMessage]:
        """
        Retrieve the most recent messages.

        Returned in chronological order.
        """

        if limit <= 0:
            raise ValueError(
                "Message limit must be greater than zero."
            )

        result = await self.db.execute(
            select(AssistantMessage)
            .where(
                AssistantMessage.session_id == session_id
            )
            .order_by(
                AssistantMessage.created_at.desc()
            )
            .limit(limit)
        )

        messages = list(
            result.scalars().all()
        )

        messages.reverse()

        return messages

    async def count_messages(
        self,
        session_id: UUID,
    ) -> int:
        """
        Return the number of messages in a session.
        """

        from sqlalchemy import func

        result = await self.db.execute(
            select(
                func.count(
                    AssistantMessage.id
                )
            ).where(
                AssistantMessage.session_id == session_id
            )
        )

        return int(
            result.scalar_one()
        )

    # ==================================================================
    # TRANSACTION METHODS
    # ==================================================================

    async def commit(self) -> None:
        """
        Commit the current transaction.
        """

        await self.db.commit()

    async def rollback(self) -> None:
        """
        Roll back the current transaction.
        """

        await self.db.rollback()


__all__ = [
    "AssistantRepository",
]