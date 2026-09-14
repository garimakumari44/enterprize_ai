"""
app/processing/embeddings/base.py

Provider abstraction for document embeddings.

Architecture
------------

    EmbeddingStage / EmbeddingService
                |
                v
        EmbeddingProvider
                |
        +-------+-------+
        |               |
        v               v
    Local Provider   Remote Provider
        |               |
        v               v
    local model      API/model
                |
                v
        list[list[float]]

The provider abstraction does not know about:

    - ProcessingContext
    - ProcessingPipeline
    - document chunks
    - databases
    - indexing
    - workflow execution

It only converts text into embedding vectors.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """
    Contract implemented by every embedding provider.

    A provider is responsible only for generating embeddings.

    Implementations may be:

        - local Sentence Transformers models
        - other local embedding models
        - remote embedding APIs
        - future custom providers

    The rest of the processing system depends only on this contract.
    """

    # ========================================================================
    # PROVIDER IDENTITY
    # ========================================================================

    @property
    def name(self) -> str:
        """
        Return the canonical provider name.

        Examples:

            "local"
            "sentence_transformers"
            "remote"
        """

        ...

    @property
    def model(self) -> str:
        """
        Return the configured model identifier.

        Examples:

            "all-MiniLM-L6-v2"
            "BAAI/bge-small-en-v1.5"
        """

        ...

    @property
    def dimension(self) -> int:
        """
        Return the expected embedding vector dimension.

        The value must be positive.
        """

        ...

    # ========================================================================
    # EMBEDDING
    # ========================================================================

    async def embed(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate one embedding vector per input text.

        Contract:

            len(result) == len(texts)

        Every returned vector must:

            - contain numeric values
            - have the same dimension
            - match the provider's dimension property

        Empty input should return an empty list.
        """

        ...

    # ========================================================================
    # RESOURCE MANAGEMENT
    # ========================================================================

    async def close(self) -> None:
        """
        Release provider resources.

        Local providers may use this to release model/runtime resources.

        Providers that do not require explicit cleanup may implement this
        as a no-op.
        """

        ...