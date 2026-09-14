"""
app/repositories/documents/document_repository.py

Repository for logical Document entities.

DocumentRepository is responsible only for database operations
on the logical Document model.

Transaction ownership belongs to DocumentService.
This repository never commits transactions.
"""

from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document


class DocumentRepository:
    """
    Repository for logical Document records.

    Responsibilities:
        - Create documents
        - Retrieve documents
        - Find duplicate documents
        - List documents
        - Update documents
        - Delete documents

    Not responsible for:
        - File uploads
        - MinIO
        - DocumentVersion creation
        - Processing
        - OCR
        - Parsing
        - Embeddings
        - Transaction commits
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # CREATE
    # =========================================================================

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        document_type: str | None = None,
        status: str = "active",
        current_version_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Document:
        """
        Create a logical Document.

        This method does NOT commit.

        DocumentService owns the complete transaction:

            Document
                ↓
            DocumentVersion
                ↓
            current_version_id
                ↓
            COMMIT
        """

        document = Document(
            name=name,
            description=description,
            document_type=document_type,
            status=status,
            current_version_id=current_version_id,
            metadata_=dict(metadata or {}),
        )

        self.session.add(document)

        # Persist enough to generate document.id.
        await self.session.flush()

        return document

    # =========================================================================
    # GET BY ID
    # =========================================================================

    async def get_by_id(
        self,
        document_id: UUID,
    ) -> Document | None:
        """Retrieve a document by UUID."""

        result = await self.session.execute(
            select(Document).where(
                Document.id == document_id
            )
        )

        return result.scalar_one_or_none()

    # =========================================================================
    # GET BY CHECKSUM
    # =========================================================================

    async def get_by_checksum(
        self,
        *,
        checksum: str,
        project_id: UUID | None = None,
    ) -> Document | None:
        """
        Find an existing document using the checksum stored
        inside Document.metadata_.
        """

        query = select(Document).where(
            Document.metadata_["checksum"].as_string() == checksum
        )

        if project_id is not None:
            query = query.where(
                Document.metadata_["project_id"].as_string()
                == str(project_id)
            )

        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    # =========================================================================
    # LIST
    # =========================================================================

    async def list(
        self,
        *,
        project_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Document]:
        """Return documents ordered newest first."""

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if offset < 0:
            raise ValueError(
                "offset cannot be negative."
            )

        query = select(Document)

        if project_id is not None:
            query = query.where(
                Document.metadata_["project_id"].as_string()
                == str(project_id)
            )

        query = (
            query
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    # =========================================================================
    # UPDATE
    # =========================================================================

    async def update(
        self,
        document: Document,
        **fields: Any,
    ) -> Document:
        """
        Update supported Document fields.

        This method does NOT commit.
        """

        allowed_fields = {
            "name",
            "description",
            "document_type",
            "status",
            "current_version_id",
            "metadata_",
        }

        unknown_fields = set(fields) - allowed_fields

        if unknown_fields:
            raise ValueError(
                "Unsupported Document field(s): "
                + ", ".join(sorted(unknown_fields))
            )

        for field, value in fields.items():
            setattr(document, field, value)

        await self.session.flush()

        return document

    # =========================================================================
    # DELETE
    # =========================================================================

    async def delete(
        self,
        document: Document,
    ) -> None:
        """
        Delete a document.

        Related DocumentVersion records are handled by
        the database relationship/cascade.
        """

        await self.session.delete(document)

        await self.session.flush()

    # =========================================================================
    # EXISTS
    # =========================================================================

    async def exists(
        self,
        document_id: UUID,
    ) -> bool:
        """Check whether a document exists."""

        result = await self.session.execute(
            select(Document.id).where(
                Document.id == document_id
            )
        )

        return result.scalar_one_or_none() is not None


__all__ = [
    "DocumentRepository",
]