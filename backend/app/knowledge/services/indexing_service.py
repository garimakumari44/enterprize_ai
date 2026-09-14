"""
app/processing/indexing/service.py

Document indexing application service.

Responsibilities
----------------
- Generate embeddings for document chunks.
- Build VectorDocument objects.
- Store document/chunk identity in vector metadata.
- Ensure the vector collection exists.
- Send vectors to IndexManager.
"""

from __future__ import annotations

from typing import Any

from app.knowledge.embeddings.embedding_manager import (
    EmbeddingManager,
)
from app.knowledge.indexing.index_manager import (
    IndexManager,
)
from app.knowledge.vector_store.base import (
    VectorDocument,
)


DEFAULT_COLLECTION = "document_chunks"


class IndexingService:
    """
    Handles document embedding and vector indexing.
    """

    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        index_manager: IndexManager,
    ) -> None:
        self.embedding_manager = embedding_manager
        self.index_manager = index_manager

    # ========================================================================
    # INDEX DOCUMENT
    # ========================================================================

    async def index_document(
        self,
        document: dict[str, Any],
    ) -> None:
        """
        Generate embeddings and index all document chunks.

        Expected document structure:

            {
                "id": "...",
                "collection_id": "...",
                "chunks": [
                    {
                        "id": "...",
                        "text": "...",
                        "metadata": {...}
                    }
                ]
            }

        If a chunk does not have an explicit ID, a deterministic fallback
        ID is generated:

            <document_id>:<chunk_index>
        """

        if not document:
            return

        # --------------------------------------------------------------------
        # Document identity
        # --------------------------------------------------------------------

        if "id" not in document:
            raise ValueError(
                "Cannot index document without an 'id'."
            )

        document_id = str(
            document["id"]
        )

        collection_id = document.get(
            "collection_id"
        )

        if collection_id is not None:
            collection_id = str(
                collection_id
            )

        chunks = document.get(
            "chunks",
            [],
        )

        if not chunks:
            return

        vector_documents: list[
            VectorDocument
        ] = []

        # ====================================================================
        # PROCESS CHUNKS
        # ====================================================================

        for index, chunk in enumerate(
            chunks
        ):

            # ----------------------------------------------------------------
            # Extract chunk information
            # ----------------------------------------------------------------

            if isinstance(
                chunk,
                dict,
            ):

                text = str(
                    chunk.get(
                        "text",
                        chunk.get(
                            "content",
                            "",
                        ),
                    )
                )

                metadata = dict(
                    chunk.get(
                        "metadata",
                        {},
                    )
                    or {}
                )

                # Prefer an actual chunk ID if available.
                chunk_id = (
                    chunk.get("id")
                    or chunk.get("chunk_id")
                    or metadata.get("chunk_id")
                )

            else:

                text = str(
                    chunk
                )

                metadata = {}

                chunk_id = None

            # ----------------------------------------------------------------
            # Skip empty chunks
            # ----------------------------------------------------------------

            if not text.strip():
                continue

            # ----------------------------------------------------------------
            # Generate fallback chunk ID
            # ----------------------------------------------------------------

            if chunk_id is None:
                chunk_id = (
                    f"{document_id}:{index}"
                )

            chunk_id = str(
                chunk_id
            )

            # ----------------------------------------------------------------
            # Generate embedding
            # ----------------------------------------------------------------

            embedding = (
                await self.embedding_manager.embed_text(
                    text
                )
            )

            if not embedding:
                continue

            # ----------------------------------------------------------------
            # Build metadata
            #
            # These fields are required later by the Retriever so that
            # the API can construct:
            #
            #   chunk_id
            #   document_id
            #   collection_id
            # ----------------------------------------------------------------

            vector_metadata: dict[str, Any] = {
                **metadata,
                "chunk_id": chunk_id,
                "document_id": document_id,
                "chunk_index": index,
            }

            if collection_id is not None:
                vector_metadata[
                    "collection_id"
                ] = collection_id

            # ----------------------------------------------------------------
            # Create vector document
            # ----------------------------------------------------------------

            vector_documents.append(
                VectorDocument(
                    id=chunk_id,
                    content=text,
                    vector=embedding,
                    metadata=vector_metadata,
                )
            )

        # ====================================================================
        # NOTHING TO INDEX
        # ====================================================================

        if not vector_documents:
            return

        # ====================================================================
        # ENSURE VECTOR COLLECTION
        # ====================================================================

        dimension = len(
            vector_documents[0].vector
        )

        if dimension <= 0:
            raise ValueError(
                "Generated embedding has an invalid dimension."
            )

        await self.index_manager.create_index(
            name=DEFAULT_COLLECTION,
            dimension=dimension,
        )

        # ====================================================================
        # INSERT / UPDATE VECTORS
        # ====================================================================

        await self.index_manager.update_index(
            name=DEFAULT_COLLECTION,
            chunks=vector_documents,
        )

    # ========================================================================
    # REMOVE DOCUMENT
    # ========================================================================

    async def remove_document(
        self,
        document_id: str,
    ) -> bool:
        """
        Remove all vector chunks belonging to a document.

        This requires IndexManager to expose a metadata-aware deletion
        operation. Until that operation exists, return False instead of
        pretending the document was removed.
        """

        delete_by_metadata = getattr(
            self.index_manager,
            "delete_by_metadata",
            None,
        )

        if delete_by_metadata is None:
            return False

        await delete_by_metadata(
            name=DEFAULT_COLLECTION,
            filters={
                "document_id": str(
                    document_id
                )
            },
        )

        return True

    # ========================================================================
    # REINDEX
    # ========================================================================

    async def reindex_document(
        self,
        document_id: str,
    ) -> bool:
        """
        Reindexing requires loading the document and its chunks from the
        document service/repository.

        That lifecycle is not owned by IndexingService yet.
        """

        return False


__all__ = [
    "IndexingService",
]