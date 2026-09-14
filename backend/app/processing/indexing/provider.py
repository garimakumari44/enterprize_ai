"""
app/processing/indexing/provider.py

Adapter between the document-processing pipeline and
the application vector-store infrastructure.

The processing pipeline knows only about the IndexProvider
contract.

This adapter translates ProcessingContext data into
VectorDocument objects and delegates persistence to the
VectorStoreManager.

Transaction ownership
---------------------

The ProcessingIndexProvider is application-scoped.

A job/request-scoped AsyncSession is supplied to each
index() invocation:

    ProcessingJobRunner
            |
            v
    DocumentProcessor
            |
            v
    ProcessingPipeline
            |
            v
    IndexingStage
            |
            v
    ProcessingIndexProvider.index(session=...)
            |
            v
    VectorStoreManager(session=session)
            |
            v
    PGVectorStore
            |
            v
    PostgreSQL

The session lifecycle is owned by the application.

This provider:
- does NOT create AsyncSession objects
- does NOT close AsyncSession objects
- may commit/rollback the supplied session for the
  indexing transaction
"""

from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.vector_store.base import VectorDocument
from app.knowledge.vector_store.vector_manager import (
    VectorStoreManager,
)


class ProcessingIndexProvider:
    """
    Concrete indexing provider used by IndexingStage.

    The provider itself is application-scoped.

    A job-scoped AsyncSession is supplied to index()
    so that concurrent processing jobs never share the
    same database session.
    """

    def __init__(
        self,
        *,
        provider: str = "pgvector",
        config: dict[str, Any] | None = None,
        collection_name: str = "document_chunk_vectors",
    ) -> None:

        self.provider = provider.strip().lower()

        self.config = dict(
            config or {}
        )

        self.collection_name = collection_name

    # ========================================================================
    # INDEX
    # ========================================================================

    async def index(
        self,
        *,
        document_id: str,
        chunks: list[Any],
        embeddings: list[Any],
        session: AsyncSession,
    ) -> dict[str, Any]:
        """
        Convert chunks + embeddings into VectorDocuments
        and persist them.

        Parameters
        ----------
        document_id:
            Canonical document identifier.

        chunks:
            Enriched document chunks.

        embeddings:
            Embeddings corresponding one-to-one with chunks.

        session:
            Job/request-scoped AsyncSession owned by the caller.

        The supplied session is reused for the complete
        indexing operation.

        This method does not create or close the session.
        """

        if session is None:
            raise ValueError(
                "AsyncSession is required for indexing."
            )

        # --------------------------------------------------------------------
        # Validate input.
        # --------------------------------------------------------------------

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks does not match "
                "number of embeddings. "
                f"chunks={len(chunks)}, "
                f"embeddings={len(embeddings)}"
            )

        if not chunks:
            return {
                "status": "skipped",
                "indexed": 0,
                "document_id": document_id,
                "collection": self.collection_name,
                "provider": self.provider,
            }

        # --------------------------------------------------------------------
        # Convert chunks into VectorDocuments.
        # --------------------------------------------------------------------

        documents: list[VectorDocument] = []

        dimension: int | None = None

        for index, (
            chunk,
            embedding,
        ) in enumerate(
            zip(
                chunks,
                embeddings,
            )
        ):

            content = self._extract_content(
                chunk
            )

            if not content.strip():
                raise ValueError(
                    f"Chunk {index} contains empty content."
                )

            metadata = self._extract_metadata(
                chunk
            )

            metadata.update(
                {
                    "document_id": document_id,
                    "chunk_index": index,
                }
            )

            vector = self._normalize_embedding(
                embedding
            )

            if not vector:
                raise ValueError(
                    f"Embedding for chunk {index} is empty."
                )

            current_dimension = len(vector)

            if dimension is None:
                dimension = current_dimension

            elif current_dimension != dimension:
                raise ValueError(
                    "Embedding dimensions are inconsistent. "
                    f"Expected={dimension}, "
                    f"found={current_dimension}, "
                    f"chunk_index={index}"
                )

            chunk_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"{document_id}:{index}",
                )
            )

            documents.append(
                VectorDocument(
                    id=chunk_id,
                    content=content,
                    vector=vector,
                    metadata=metadata,
                )
            )

        if dimension is None:
            raise RuntimeError(
                "Could not determine embedding dimension."
            )

        # --------------------------------------------------------------------
        # Create vector-store manager using the job-scoped session.
        # --------------------------------------------------------------------

        vector_manager = VectorStoreManager(
            provider=self.provider,
            session=session,
            config=self.config,
        )

        try:

            # ------------------------------------------------------------
            # Ensure collection.
            # ------------------------------------------------------------

            await vector_manager.create_collection(
                collection_name=self.collection_name,
                dimension=dimension,
            )

            # ------------------------------------------------------------
            # Add/upsert documents.
            # ------------------------------------------------------------

            result = await vector_manager.add_documents(
                collection_name=self.collection_name,
                documents=documents,
            )

            if result is None:
                result = {}

            indexed = int(
                result.get(
                    "indexed",
                    len(documents),
                )
            )

            # ------------------------------------------------------------
            # Commit indexing transaction.
            #
            # IMPORTANT:
            # The session itself is NOT closed here.
            # ------------------------------------------------------------

            await session.commit()

            return {
                "status": "completed",
                "indexed": indexed,
                "document_id": document_id,
                "collection": self.collection_name,
                "provider": self.provider,
                "dimension": dimension,
            }

        except Exception:

            await session.rollback()

            raise

        finally:

            await vector_manager.close()

    # ========================================================================
    # EXTRACTION HELPERS
    # ========================================================================

    @staticmethod
    def _extract_content(
        chunk: Any,
    ) -> str:
        """
        Extract text content from a chunk.
        """

        if isinstance(
            chunk,
            str,
        ):
            return chunk

        if isinstance(
            chunk,
            dict,
        ):

            for key in (
                "content",
                "text",
                "page_content",
            ):

                value = chunk.get(
                    key
                )

                if value is not None:
                    return str(value)

            return str(chunk)

        for attribute in (
            "content",
            "text",
            "page_content",
        ):

            value = getattr(
                chunk,
                attribute,
                None,
            )

            if value is not None:
                return str(value)

        return str(chunk)

    @staticmethod
    def _extract_metadata(
        chunk: Any,
    ) -> dict[str, Any]:
        """
        Extract metadata from a chunk.
        """

        if isinstance(
            chunk,
            dict,
        ):

            metadata = chunk.get(
                "metadata",
                {},
            )

            if isinstance(
                metadata,
                dict,
            ):
                return dict(metadata)

            return {}

        metadata = getattr(
            chunk,
            "metadata",
            None,
        )

        if isinstance(
            metadata,
            dict,
        ):
            return dict(metadata)

        return {}

    @staticmethod
    def _normalize_embedding(
        embedding: Any,
    ) -> list[float]:
        """
        Normalize embedding objects into list[float].
        """

        if embedding is None:
            raise ValueError(
                "Embedding cannot be None."
            )

        # NumPy / tensor-like objects.
        if hasattr(
            embedding,
            "tolist",
        ):
            embedding = embedding.tolist()

        if not isinstance(
            embedding,
            (
                list,
                tuple,
            ),
        ):
            raise TypeError(
                "Embedding must be a list or tuple."
            )

        vector = [
            float(value)
            for value in embedding
        ]

        return vector


__all__ = [
    "ProcessingIndexProvider",
]