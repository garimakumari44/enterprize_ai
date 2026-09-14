from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.vector.models import (
    VectorRecord,
    VectorSearchRequest,
    VectorSearchResult,
)


class VectorRepository(ABC):
    """
    Abstract vector repository.

    Keeps the service layer independent from the underlying
    vector database implementation.
    """

    @abstractmethod
    async def upsert(
        self,
        records: Sequence[VectorRecord],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        request: VectorSearchRequest,
    ) -> list[VectorSearchResult]:
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        ids: Sequence[str],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_document(
        self,
        document_id: str,
    ) -> None:
        raise NotImplementedError


class PgVectorRepository(VectorRepository):
    """
    PostgreSQL / pgvector implementation.

    The repository expects a SQLAlchemy model containing:

        id
        document_id
        chunk_id
        embedding
        content
        metadata
    """

    def __init__(
        self,
        session: AsyncSession,
        vector_model: Any,
    ) -> None:
        self.session = session
        self.vector_model = vector_model

    async def upsert(
        self,
        records: Sequence[VectorRecord],
    ) -> None:
        for record in records:
            existing = await self.session.get(
                self.vector_model,
                record.id,
            )

            if existing:
                existing.document_id = record.document_id
                existing.chunk_id = record.chunk_id
                existing.embedding = record.embedding
                existing.content = record.content
                existing.metadata = record.metadata

            else:
                entity = self.vector_model(
                    id=record.id,
                    document_id=record.document_id,
                    chunk_id=record.chunk_id,
                    embedding=record.embedding,
                    content=record.content,
                    metadata=record.metadata,
                )

                self.session.add(entity)

        await self.session.flush()

    async def search(
        self,
        request: VectorSearchRequest,
    ) -> list[VectorSearchResult]:

        model = self.vector_model

        distance = model.embedding.cosine_distance(
            request.embedding
        )

        query = (
            select(
                model,
                distance.label("distance"),
            )
            .order_by(distance)
            .limit(request.top_k)
        )

        if request.document_id:
            query = query.where(
                model.document_id == request.document_id
            )

        result = await self.session.execute(query)

        rows = result.all()

        results: list[VectorSearchResult] = []

        for row in rows:
            entity = row[0]
            distance_value = float(row[1])

            # pgvector cosine distance:
            #   0 = identical
            #   1 = maximally distant
            #
            # Convert to similarity score.
            score = 1.0 - distance_value

            if (
                request.score_threshold is not None
                and score < request.score_threshold
            ):
                continue

            results.append(
                VectorSearchResult(
                    id=str(entity.id),
                    document_id=entity.document_id,
                    chunk_id=entity.chunk_id,
                    score=score,
                    content=entity.content,
                    metadata=entity.metadata or {},
                )
            )

        return results

    async def delete(
        self,
        ids: Sequence[str],
    ) -> None:

        stmt = delete(self.vector_model).where(
            self.vector_model.id.in_(ids)
        )

        await self.session.execute(stmt)
        await self.session.flush()

    async def delete_by_document(
        self,
        document_id: str,
    ) -> None:

        stmt = delete(self.vector_model).where(
            self.vector_model.document_id == document_id
        )

        await self.session.execute(stmt)
        await self.session.flush()