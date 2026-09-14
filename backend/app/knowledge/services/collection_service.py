from __future__ import annotations

from typing import Any

from app.knowledge.vector_store.vector_manager import VectorStoreManager


class CollectionService:
    """
    Manages vector collections / indexes.
    """

    def __init__(
        self,
        vector_manager: VectorStoreManager,
    ) -> None:
        self.vector_manager = vector_manager

    async def create_collection(
        self,
        name: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Create a new collection.
        """

        await self.vector_manager.create_collection(
            name=name,
            metadata=metadata or {},
        )

        return True

    async def delete_collection(
        self,
        name: str,
    ) -> bool:
        """
        Delete an existing collection.
        """

        await self.vector_manager.delete_collection(name)

        return True

    async def list_collections(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return all available collections.
        """

        return await self.vector_manager.list_collections()

    async def collection_exists(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a collection exists.
        """

        return await self.vector_manager.collection_exists(name)

    async def collection_stats(
        self,
        name: str,
    ) -> dict[str, Any]:
        """
        Return collection statistics.
        """

        return await self.vector_manager.collection_stats(name)