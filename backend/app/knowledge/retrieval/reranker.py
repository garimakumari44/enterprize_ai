"""
app/knowledge/retrieval/reranker.py

Reranking component.

Responsibilities
----------------
- Receive retrieved candidates.
- Apply an optional advanced relevance model.
- Fall back to score-based ranking.
- Return the top-k candidates.

This class does NOT:
- retrieve documents
- generate query embeddings
- access PostgreSQL
- perform vector search
- expose FastAPI routes
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any


class Reranker:
    """
    Re-ranks retrieved documents.

    If a model is supplied:

        model.rank(query, documents)

    is used.

    Otherwise:

        document.score

    is used as the fallback ranking signal.
    """

    DEFAULT_TOP_K = 5
    MAX_TOP_K = 100

    def __init__(
        self,
        model: Any | None = None,
    ) -> None:
        """
        Initialize the reranker.

        Parameters
        ----------
        model:
            Optional reranking model.

            Expected API:

                rank(query, documents)

            The method may be synchronous or asynchronous.
        """

        self.model = model

    # ========================================================================
    # RERANK
    # ========================================================================

    async def rerank(
        self,
        query: str,
        documents: Sequence[Mapping[str, Any]],
        top_k: int = DEFAULT_TOP_K,
    ) -> list[dict[str, Any]]:
        """
        Rerank retrieved documents.
        """

        # --------------------------------------------------------------------
        # Validate query
        # --------------------------------------------------------------------

        if not isinstance(
            query,
            str,
        ):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            return []

        # --------------------------------------------------------------------
        # Validate documents
        # --------------------------------------------------------------------

        if not documents:
            return []

        # --------------------------------------------------------------------
        # Validate top_k
        # --------------------------------------------------------------------

        if top_k <= 0:
            return []

        top_k = min(
            int(top_k),
            self.MAX_TOP_K,
        )

        # --------------------------------------------------------------------
        # Normalize documents
        # --------------------------------------------------------------------

        normalized_documents = [
            self._normalize_document(
                document
            )
            for document in documents
            if document is not None
        ]

        if not normalized_documents:
            return []

        # --------------------------------------------------------------------
        # Model-based reranking
        # --------------------------------------------------------------------

        if self.model is not None:

            ranked = await self._model_rerank(
                query=query,
                documents=normalized_documents,
            )

            ranked = self._normalize_ranked_output(
                ranked,
                normalized_documents,
            )

        else:

            # ----------------------------------------------------------------
            # Fallback score ranking
            # ----------------------------------------------------------------

            ranked = sorted(
                normalized_documents,
                key=lambda item: self._safe_score(
                    item.get(
                        "score",
                        0.0,
                    )
                ),
                reverse=True,
            )

        return ranked[
            :top_k
        ]

    # ========================================================================
    # MODEL RERANKING
    # ========================================================================

    async def _model_rerank(
        self,
        *,
        query: str,
        documents: list[dict[str, Any]],
    ) -> Any:
        """
        Execute model.rank().
        """

        rank = getattr(
            self.model,
            "rank",
            None,
        )

        if not callable(rank):
            raise AttributeError(
                "Reranker model must provide rank()."
            )

        result = rank(
            query,
            documents,
        )

        if inspect.isawaitable(
            result
        ):
            result = await result

        return result

    # ========================================================================
    # RANKED OUTPUT NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_ranked_output(
        ranked: Any,
        original_documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Normalize different model-ranking outputs.

        Supported:

            [
                {"id": "...", "score": 0.9}
            ]

        or:

            [
                original_document_1,
                original_document_2
            ]

        or a model returning None.

        If the model returns no usable output, the original score-based
        ranking is used as a safe fallback.
        """

        if ranked is None:
            return sorted(
                original_documents,
                key=lambda item: Reranker._safe_score(
                    item.get(
                        "score",
                        0.0,
                    )
                ),
                reverse=True,
            )

        if not isinstance(
            ranked,
            Sequence,
        ) or isinstance(
            ranked,
            (str, bytes),
        ):
            raise TypeError(
                "Reranker model must return a sequence of documents."
            )

        normalized: list[dict[str, Any]] = []

        for item in ranked:

            if item is None:
                continue

            if isinstance(
                item,
                Mapping,
            ):

                normalized.append(
                    Reranker._normalize_document(
                        item
                    )
                )

            else:

                normalized.append(
                    Reranker._normalize_document(
                        item
                    )
                )

        if not normalized:
            return sorted(
                original_documents,
                key=lambda item: Reranker._safe_score(
                    item.get(
                        "score",
                        0.0,
                    )
                ),
                reverse=True,
            )

        return normalized

    # ========================================================================
    # DOCUMENT NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_document(
        document: Mapping[str, Any] | Any,
    ) -> dict[str, Any]:
        """
        Normalize a document into the standard retrieval format.
        """

        if isinstance(
            document,
            Mapping,
        ):

            result_id = document.get(
                "id"
            )

            chunk_id = document.get(
                "chunk_id"
            )

            document_id = document.get(
                "document_id"
            )

            collection_id = document.get(
                "collection_id"
            )

            content = document.get(
                "content",
                "",
            )

            score = document.get(
                "score",
                0.0,
            )

            metadata = dict(
                document.get(
                    "metadata",
                    {},
                )
                or {}
            )

        else:

            result_id = getattr(
                document,
                "id",
                None,
            )

            chunk_id = getattr(
                document,
                "chunk_id",
                None,
            )

            document_id = getattr(
                document,
                "document_id",
                None,
            )

            collection_id = getattr(
                document,
                "collection_id",
                None,
            )

            content = getattr(
                document,
                "content",
                "",
            )

            score = getattr(
                document,
                "score",
                0.0,
            )

            metadata = dict(
                getattr(
                    document,
                    "metadata",
                    {},
                )
                or {}
            )

        # --------------------------------------------------------------------
        # Metadata fallbacks
        # --------------------------------------------------------------------

        chunk_id = (
            chunk_id
            or metadata.get("chunk_id")
            or metadata.get("chunkId")
            or metadata.get("id")
            or result_id
        )

        document_id = (
            document_id
            or metadata.get("document_id")
            or metadata.get("documentId")
        )

        collection_id = (
            collection_id
            or metadata.get("collection_id")
            or metadata.get("collectionId")
        )

        # --------------------------------------------------------------------
        # Content
        # --------------------------------------------------------------------

        if content is None:
            content = ""

        # --------------------------------------------------------------------
        # Score
        # --------------------------------------------------------------------

        normalized_score = Reranker._safe_score(
            score
        )

        normalized_id = (
            str(result_id)
            if result_id is not None
            else (
                str(chunk_id)
                if chunk_id is not None
                else None
            )
        )

        return {
            "id": normalized_id,
            "chunk_id": chunk_id,
            "document_id": document_id,
            "collection_id": collection_id,
            "content": str(content),
            "score": normalized_score,
            "metadata": metadata,
        }

    # ========================================================================
    # SCORE
    # ========================================================================

    @staticmethod
    def _safe_score(
        score: Any,
    ) -> float:
        """
        Safely convert score to float.
        """

        try:
            return float(
                score
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0


__all__ = [
    "Reranker",
]