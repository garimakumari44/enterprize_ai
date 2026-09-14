from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.knowledge.vector_store.vector_manager import VectorStoreManager


class VectorRepository:
    """
    Repository for Vector Store operations.

    This abstracts away the underlying vector database.
    """

    def __init__(
        self,
        vector_manager: VectorStoreManager,
    ):
        self.vector_manager = vector_manager

    async def upsert_vector(
        self,
        *,
        vector_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        await self.vector_manager.upsert(
            vector_id=vector_id,
            embedding=embedding,
            metadata=metadata,
        )

    async def delete_vector(
        self,
        vector_id: str,
    ) -> None:
        await self.vector_manager.delete(
            vector_id
        )

    async def get_vector(
        self,
        vector_id: str,
    ) -> Optional[Dict[str, Any]]:
        return await self.vector_manager.get(
            vector_id
        )

    async def similarity_search(
        self,
        embedding: List[float],
        *,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ):
        return await self.vector_manager.search(
            embedding=embedding,
            top_k=top_k,
            filters=filters,
        )