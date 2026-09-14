from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class IndexProvider(Protocol):
    async def index(
        self,
        *,
        document_id: str,
        chunks: list[Any],
        embeddings: list[Any],
        session: AsyncSession,
    ) -> Any:
        ...


class IndexingStage(DocumentProcessingStage):
    """
    Persist enriched chunks and embeddings into the search/vector index.

    The actual PostgreSQL/pgvector implementation is injected.

    The database session is supplied for the current processing
    execution and is never stored on the stage instance.
    """

    def __init__(
        self,
        provider: IndexProvider | None = None,
    ) -> None:
        self.provider = provider

    @property
    def name(self) -> str:
        return ProcessingStage.INDEXING.value

    async def process(
        self,
        data: ProcessingContext,
        *,
        session: AsyncSession,
    ) -> ProcessingContext:

        if not data.enriched_chunks:
            data.set_indexing_result(
                {
                    "status": "skipped",
                    "indexed": 0,
                }
            )

            return data

        if self.provider is None:
            raise RuntimeError(
                "Index provider is not configured."
            )

        if session is None:
            raise RuntimeError(
                "AsyncSession is required for the indexing stage."
            )

        result = await self.provider.index(
            document_id=data.document_id,
            chunks=data.enriched_chunks,
            embeddings=data.embeddings,
            session=session,
        )

        data.set_indexing_result(
            result
        )

        data.stage_results[
            self.name
        ] = {
            "status": "completed",
            "result": result,
        }

        return data


__all__ = [
    "IndexProvider",
    "IndexingStage",
]