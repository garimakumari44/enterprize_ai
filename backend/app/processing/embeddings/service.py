"""
app/processing/embeddings/service.py

Application-facing embedding service.

Architecture
------------

    Processing / EmbeddingStage
                |
                v
        EmbeddingService
                |
                v
        EmbeddingProvider
                |
        +-------+-------+
        |               |
        v               v
    Local Provider   Remote Provider

Responsibilities
----------------

    - Provide a stable application-facing embedding API
    - Hide provider-specific implementation details
    - Validate embedding inputs
    - Validate provider output
    - Expose provider metadata
    - Manage provider lifecycle

This service does NOT:

    - Know about ProcessingContext
    - Know about document chunks
    - Execute processing stages
    - Access the database
    - Resolve providers
"""

from __future__ import annotations

from collections.abc import Sequence
from math import isfinite

from app.processing.embeddings.base import EmbeddingProvider


class EmbeddingService:
    """
    Provider-independent application-facing embedding service.

    The service depends only on the EmbeddingProvider contract.

    This allows the application to switch between providers without
    changing the rest of the processing architecture.
    """

    def __init__(
        self,
        provider: EmbeddingProvider,
    ) -> None:

        if provider is None:
            raise ValueError(
                "provider must not be None."
            )

        self._provider = provider

        self._validate_provider_metadata()

    # ========================================================================
    # PROVIDER INFORMATION
    # ========================================================================

    @property
    def provider(self) -> EmbeddingProvider:
        """
        Return the configured embedding provider.
        """

        return self._provider

    @property
    def provider_name(self) -> str:
        """
        Return the canonical provider name.
        """

        return self._provider.name

    @property
    def model(self) -> str:
        """
        Return the configured model identifier.
        """

        return self._provider.model

    @property
    def dimension(self) -> int:
        """
        Return the expected embedding dimension.
        """

        return self._provider.dimension

    # ========================================================================
    # EMBEDDING
    # ========================================================================

    async def embed(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for a sequence of texts.

        Contract:

            len(result) == len(texts)

        Empty input returns an empty list.

        Provider-specific implementation details remain hidden behind
        EmbeddingProvider.
        """

        self._validate_texts(texts)

        if not texts:
            return []

        embeddings = await self._provider.embed(
            texts,
        )

        self._validate_embeddings(
            embeddings,
            expected_count=len(texts),
        )

        return embeddings

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    async def close(self) -> None:
        """
        Release provider resources.
        """

        await self._provider.close()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate_provider_metadata(self) -> None:
        """
        Validate provider metadata.

        This catches configuration errors early rather than allowing
        invalid provider state to reach the processing pipeline.
        """

        name = self._provider.name

        if not isinstance(name, str):
            raise TypeError(
                "Embedding provider name must be a string."
            )

        if not name.strip():
            raise ValueError(
                "Embedding provider name cannot be empty."
            )

        model = self._provider.model

        if not isinstance(model, str):
            raise TypeError(
                "Embedding provider model must be a string."
            )

        if not model.strip():
            raise ValueError(
                "Embedding provider model cannot be empty."
            )

        dimension = self._provider.dimension

        if not isinstance(dimension, int):
            raise TypeError(
                "Embedding provider dimension must be an integer."
            )

        if dimension <= 0:
            raise ValueError(
                "Embedding provider dimension must be greater than zero."
            )

    @staticmethod
    def _validate_texts(
        texts: Sequence[str],
    ) -> None:
        """
        Validate embedding input texts.
        """

        if texts is None:
            raise ValueError(
                "texts must not be None."
            )

        if isinstance(texts, (str, bytes)):
            raise TypeError(
                "texts must be a sequence of strings, "
                "not a single string."
            )

        for index, text in enumerate(texts):

            if not isinstance(text, str):
                raise TypeError(
                    f"Text at index {index} must be a string."
                )

    def _validate_embeddings(
        self,
        embeddings: Sequence[Sequence[float]],
        *,
        expected_count: int,
    ) -> None:
        """
        Validate provider output.

        Checks:

            - result is a sequence
            - vector count matches input count
            - every vector is non-empty
            - every value is numeric
            - values are finite
            - every vector has the configured dimension
        """

        if embeddings is None:
            raise RuntimeError(
                "Embedding provider returned None."
            )

        if isinstance(embeddings, (str, bytes)):
            raise RuntimeError(
                "Embedding provider returned an invalid "
                "embedding collection."
            )

        if len(embeddings) != expected_count:
            raise RuntimeError(
                "Embedding provider returned an "
                "unexpected number of vectors. "
                f"Expected {expected_count}, "
                f"got {len(embeddings)}."
            )

        for index, embedding in enumerate(embeddings):

            if isinstance(embedding, (str, bytes)):
                raise RuntimeError(
                    f"Embedding vector at index {index} "
                    "must be a numeric sequence."
                )

            if not embedding:
                raise RuntimeError(
                    f"Embedding vector at index {index} "
                    "cannot be empty."
                )

            if len(embedding) != self.dimension:
                raise RuntimeError(
                    f"Embedding vector at index {index} "
                    f"has dimension {len(embedding)}, "
                    f"expected {self.dimension}."
                )

            for value_index, value in enumerate(embedding):

                if not isinstance(value, (int, float)):
                    raise RuntimeError(
                        f"Embedding vector at index {index} "
                        f"contains a non-numeric value at "
                        f"position {value_index}."
                    )

                if not isfinite(float(value)):
                    raise RuntimeError(
                        f"Embedding vector at index {index} "
                        f"contains a non-finite value at "
                        f"position {value_index}."
                    )


__all__ = [
    "EmbeddingService",
]