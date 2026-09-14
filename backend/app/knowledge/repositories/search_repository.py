"""
app/knowledge/repositories/search_repository.py

Database repository for knowledge/keyword search.

Responsibilities
----------------
- Search indexed document chunks using PostgreSQL.
- Support asynchronous SQLAlchemy sessions.
- Apply safe, explicit filters.
- Retrieve chunks by document version.
- Retrieve individual chunks.
- Count chunks.

Storage layout
--------------
The current indexing pipeline stores searchable content in:

    document_chunk_vectors

Columns currently used:

    id
    content
    embedding
    metadata

The canonical document_chunks table may contain processing-layer chunks,
but keyword retrieval must search the indexed content table because that is
where the currently indexed/searchable content resides.

The repository deliberately does not load the embedding column during
keyword search.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chunk import Chunk


class SearchRepository:
    """
    Repository for database-backed document/chunk search.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ==================================================================
    # KEYWORD SEARCH
    # ==================================================================

    async def keyword_search(
        self,
        query: str,
        limit: int = 20,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search indexed document content using PostgreSQL ILIKE.

        IMPORTANT
        ---------
        Keyword retrieval searches document_chunk_vectors because this is
        currently the populated/indexed table.

        Searchable fields:
            - content
            - metadata

        The embedding itself is never selected.

        Results are returned as dictionaries rather than Chunk ORM objects
        because document_chunk_vectors is the active indexed storage table
        and is not necessarily represented by the Chunk ORM model.
        """

        query = (query or "").strip()

        if not query:
            return []

        limit = max(1, min(int(limit), 100))

        pattern = f"%{query}%"

        # --------------------------------------------------------------
        # Base query
        # --------------------------------------------------------------
        #
        # CAST(metadata AS TEXT) allows keyword searches against metadata
        # without requiring PostgreSQL JSON-specific operators.
        #
        # This is intentionally conservative and compatible with the
        # current schema.
        #

        statement = text(
            """
            SELECT
                id,
                content,
                metadata
            FROM document_chunk_vectors
            WHERE
                content ILIKE :pattern
                OR CAST(metadata AS TEXT) ILIKE :pattern
            ORDER BY
                CASE
                    WHEN content ILIKE :exact_pattern THEN 0
                    WHEN content ILIKE :prefix_pattern THEN 1
                    ELSE 2
                END,
                id
            LIMIT :limit
            """
        )

        result = await self.db.execute(
            statement,
            {
                "pattern": pattern,
                "exact_pattern": f"%{query}%",
                "prefix_pattern": f"{query}%",
                "limit": limit,
            },
        )

        rows = result.mappings().all()

        normalized: list[dict[str, Any]] = []

        for row in rows:
            normalized.append(
                self._normalize_indexed_row(row)
            )

        # Apply filters after retrieval because the indexed table stores
        # several document attributes inside metadata.
        normalized = self._apply_keyword_filters(
            normalized,
            filters,
        )

        return normalized[:limit]

    # ==================================================================
    # DOCUMENT VERSION SEARCH
    # ==================================================================

    async def search_by_document_version(
        self,
        document_version_id: UUID | str,
        limit: int = 100,
    ) -> list[Any]:
        """
        Return chunks belonging to a specific document version.

        This method continues to operate on the canonical Chunk ORM model.
        """

        limit = max(1, min(int(limit), 500))

        statement = (
            select(Chunk)
            .where(
                Chunk.document_version_id == document_version_id,
            )
            .order_by(
                Chunk.chunk_index,
            )
            .limit(limit)
        )

        result = await self.db.execute(statement)

        return list(result.scalars().all())

    # ==================================================================
    # GET CHUNK
    # ==================================================================

    async def get_chunk(
        self,
        chunk_id: UUID | str,
    ) -> Any | None:
        """
        Retrieve one canonical processing chunk by primary key.
        """

        statement = select(Chunk).where(
            Chunk.id == chunk_id,
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()

    # ==================================================================
    # COUNT
    # ==================================================================

    async def count_by_document_version(
        self,
        document_version_id: UUID | str,
    ) -> int:
        """
        Count canonical processing chunks for a document version.
        """

        statement = (
            select(func.count())
            .select_from(Chunk)
            .where(
                Chunk.document_version_id == document_version_id,
            )
        )

        result = await self.db.execute(statement)

        return int(result.scalar_one())

    # ==================================================================
    # INDEXED CHUNK COUNT
    # ==================================================================

    async def count_indexed_chunks(self) -> int:
        """
        Count rows currently available to keyword/vector retrieval.
        """

        statement = text(
            """
            SELECT COUNT(*)
            FROM document_chunk_vectors
            """
        )

        result = await self.db.execute(statement)

        return int(result.scalar_one() or 0)

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_indexed_row(
        row: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize a document_chunk_vectors row.

        The indexed table stores document/chunk information in metadata.
        """

        metadata_value = row.get("metadata")

        if metadata_value is None:
            metadata: dict[str, Any] = {}
        elif isinstance(metadata_value, Mapping):
            metadata = dict(metadata_value)
        else:
            try:
                metadata = dict(metadata_value)
            except (TypeError, ValueError):
                metadata = {}

        row_id = row.get("id")

        chunk_id = (
            metadata.get("chunk_id")
            or metadata.get("chunkId")
            or row_id
        )

        document_id = (
            metadata.get("document_id")
            or metadata.get("documentId")
        )

        document_version_id = (
            metadata.get("document_version_id")
            or metadata.get("documentVersionId")
        )

        collection_id = (
            metadata.get("collection_id")
            or metadata.get("collectionId")
        )

        content = row.get("content") or ""

        if chunk_id is not None:
            metadata.setdefault(
                "chunk_id",
                str(chunk_id),
            )

        if document_id is not None:
            metadata.setdefault(
                "document_id",
                str(document_id),
            )

        if document_version_id is not None:
            metadata.setdefault(
                "document_version_id",
                str(document_version_id),
            )

        if collection_id is not None:
            metadata.setdefault(
                "collection_id",
                str(collection_id),
            )

        return {
            "id": (
                str(row_id)
                if row_id is not None
                else None
            ),
            "chunk_id": (
                str(chunk_id)
                if chunk_id is not None
                else None
            ),
            "document_id": (
                str(document_id)
                if document_id is not None
                else None
            ),
            "document_version_id": (
                str(document_version_id)
                if document_version_id is not None
                else None
            ),
            "collection_id": (
                str(collection_id)
                if collection_id is not None
                else None
            ),
            "content": str(content),
            "metadata": metadata,
        }

    # ==================================================================
    # KEYWORD FILTERS
    # ==================================================================

    @staticmethod
    def _apply_keyword_filters(
        results: list[dict[str, Any]],
        filters: Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """
        Apply filters against normalized indexed results.

        Supported:
            document_id
            document_version_id
            collection_id
            chunk_id
            document_type

        Unknown filters are ignored safely.
        """

        if not filters:
            return results

        allowed = {
            "document_id",
            "document_version_id",
            "collection_id",
            "chunk_id",
            "document_type",
        }

        filtered: list[dict[str, Any]] = []

        for result in results:

            metadata = (
                result.get("metadata")
                or {}
            )

            include = True

            for field_name, expected in filters.items():

                if field_name not in allowed:
                    continue

                if expected is None:
                    continue

                actual = (
                    result.get(field_name)
                    if field_name in result
                    else metadata.get(field_name)
                )

                if isinstance(
                    expected,
                    (list, tuple, set),
                ):
                    expected_values = {
                        str(value)
                        for value in expected
                    }

                    if str(actual) not in expected_values:
                        include = False
                        break

                else:
                    if str(actual) != str(expected):
                        include = False
                        break

            if include:
                filtered.append(result)

        return filtered

    # ==================================================================
    # LEGACY CHUNK FILTERS
    # ==================================================================

    @staticmethod
    def _apply_filters(
        statement,
        filters: Mapping[str, Any] | None,
    ):
        """
        Apply safe filters to the canonical Chunk ORM query.

        Used by future/legacy ORM-based repository methods.
        """

        if not filters:
            return statement

        allowed_filters = {
            "document_version_id": Chunk.document_version_id,
            "chunk_type": Chunk.chunk_type,
            "embedding_status": Chunk.embedding_status,
            "embedding_model": Chunk.embedding_model,
            "embedding_dimensions": Chunk.embedding_dimensions,
            "indexed": Chunk.indexed,
            "page_start": Chunk.page_start,
            "page_end": Chunk.page_end,
            "section_title": Chunk.section_title,
        }

        for field_name, value in filters.items():

            if value is None:
                continue

            column = allowed_filters.get(field_name)

            if column is None:
                continue

            if isinstance(
                value,
                (list, tuple, set),
            ):
                statement = statement.where(
                    column.in_(list(value))
                )
            else:
                statement = statement.where(
                    column == value
                )

        return statement


__all__ = ["SearchRepository"]