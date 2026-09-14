"""
app/knowledge/retrieval/semantic_search.py

Semantic retrieval layer.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class SemanticSearch:
    """
    Semantic search layer.

    Delegates vector retrieval to Retriever.
    """

    def __init__(self, retriever: Any) -> None:
        if retriever is None:
            raise ValueError(
                "retriever cannot be None."
            )

        self.retriever = retriever

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            return []

        try:
            top_k = int(top_k)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "top_k must be an integer."
            ) from exc

        if top_k <= 0:
            return []

        results = await self.retriever.search(
            query=query,
            top_k=top_k,
            filters=dict(filters or {}),
        )

        normalized: list[dict[str, Any]] = []

        for item in results or []:

            candidate = self._normalize_result(
                item
            )

            if candidate is not None:
                normalized.append(candidate)

        return normalized[:top_k]

    @staticmethod
    def _normalize_result(
        item: Any,
    ) -> dict[str, Any] | None:

        if item is None:
            return None

        if isinstance(item, Mapping):

            metadata_value = (
                item.get("metadata")
                or item.get("metadata_")
                or {}
            )

            if isinstance(
                metadata_value,
                Mapping,
            ):
                metadata = dict(metadata_value)
            else:
                try:
                    metadata = dict(metadata_value)
                except (TypeError, ValueError):
                    metadata = {}

            chunk_id = (
                item.get("chunk_id")
                or metadata.get("chunk_id")
                or metadata.get("chunkId")
                or item.get("id")
            )

            document_id = (
                item.get("document_id")
                or metadata.get("document_id")
                or metadata.get("documentId")
            )

            document_version_id = (
                item.get("document_version_id")
                or metadata.get("document_version_id")
                or metadata.get("documentVersionId")
            )

            collection_id = (
                item.get("collection_id")
                or metadata.get("collection_id")
                or metadata.get("collectionId")
            )

            content = (
                item.get("content")
                or item.get("text")
                or ""
            )

            score = SemanticSearch._safe_score(
                item.get(
                    "score",
                    item.get(
                        "relevance_score",
                        0.0,
                    ),
                )
            )

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

            return {
                "id": (
                    str(item.get("id"))
                    if item.get("id") is not None
                    else (
                        str(chunk_id)
                        if chunk_id is not None
                        else None
                    )
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
                "score": score,
                "metadata": metadata,
            }

        metadata_value = (
            getattr(item, "metadata_", None)
            or getattr(item, "metadata", None)
            or {}
        )

        if isinstance(
            metadata_value,
            Mapping,
        ):
            metadata = dict(metadata_value)
        else:
            try:
                metadata = dict(metadata_value)
            except (TypeError, ValueError):
                metadata = {}

        item_id = getattr(
            item,
            "id",
            None,
        )

        chunk_id = (
            getattr(
                item,
                "chunk_id",
                None,
            )
            or metadata.get("chunk_id")
            or item_id
        )

        document_id = (
            getattr(
                item,
                "document_id",
                None,
            )
            or metadata.get("document_id")
        )

        document_version_id = (
            getattr(
                item,
                "document_version_id",
                None,
            )
            or metadata.get("document_version_id")
        )

        collection_id = (
            getattr(
                item,
                "collection_id",
                None,
            )
            or metadata.get("collection_id")
        )

        content = (
            getattr(item, "content", None)
            or getattr(item, "text", None)
            or ""
        )

        score = SemanticSearch._safe_score(
            getattr(item, "score", 0.0)
        )

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

        return {
            "id": (
                str(item_id)
                if item_id is not None
                else (
                    str(chunk_id)
                    if chunk_id is not None
                    else None
                )
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
            "score": score,
            "metadata": metadata,
        }

    @staticmethod
    def _safe_score(
        value: Any,
    ) -> float:

        try:
            score = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        if score != score:
            return 0.0

        if score == float("inf"):
            return 1.0

        if score == float("-inf"):
            return 0.0

        return max(
            0.0,
            min(score, 1.0),
        )


__all__ = ["SemanticSearch"]