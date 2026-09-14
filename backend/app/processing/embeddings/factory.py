"""
app/processing/embeddings/factory.py

Embedding provider construction and resolution.

Provider selection policy:

    1. Explicit local
       -> BGE-small

    2. Explicit cohere
       -> Cohere
       -> fail if unavailable

    3. auto
       -> Cohere if API key exists
       -> otherwise local BGE-small
"""

from __future__ import annotations

from dataclasses import dataclass

from app.processing.embeddings.base import EmbeddingProvider
from app.processing.embeddings.cohere_provider import (
    CohereEmbeddingProvider,
)
from app.processing.embeddings.local_provider import (
    LocalEmbeddingProvider,
)
from app.processing.embeddings.service import (
    EmbeddingService,
)


@dataclass(frozen=True, slots=True)
class EmbeddingConfig:
    """
    Immutable embedding configuration.
    """

    provider: str = "auto"

    local_model: str = (
        "BAAI/bge-small-en-v1.5"
    )

    local_device: str = "cpu"

    local_batch_size: int = 32

    cohere_api_key: str | None = None

    cohere_model: str = "embed-v4.0"

    cohere_input_type: str = (
        "search_document"
    )

    cohere_batch_size: int = 96


def create_embedding_provider(
    config: EmbeddingConfig,
) -> EmbeddingProvider:
    """
    Resolve and construct the appropriate provider.
    """

    provider = config.provider.strip().lower()

    if provider == "local":
        return _create_local(config)

    if provider == "cohere":
        return _create_cohere(config)

    if provider == "auto":
        return _create_auto(config)

    raise ValueError(
        f"Unsupported embedding provider: '{provider}'. "
        "Supported values: auto, local, cohere."
    )


def _create_local(
    config: EmbeddingConfig,
) -> LocalEmbeddingProvider:
    return LocalEmbeddingProvider(
        model_name=config.local_model,
        device=config.local_device,
        batch_size=config.local_batch_size,
    )


def _create_cohere(
    config: EmbeddingConfig,
) -> CohereEmbeddingProvider:
    if not config.cohere_api_key:
        raise ValueError(
            "Cohere provider selected but "
            "COHERE_API_KEY is not configured."
        )

    return CohereEmbeddingProvider(
        api_key=config.cohere_api_key,
        model=config.cohere_model,
        input_type=config.cohere_input_type,
        batch_size=config.cohere_batch_size,
    )


def _create_auto(
    config: EmbeddingConfig,
) -> EmbeddingProvider:
    """
    Automatically select the best configured provider.

    Cohere is preferred when credentials are available.

    Otherwise fall back to local BGE-small.
    """

    if config.cohere_api_key:
        return _create_cohere(config)

    return _create_local(config)


def create_embedding_service(
    config: EmbeddingConfig,
) -> EmbeddingService:
    provider = create_embedding_provider(config)

    return EmbeddingService(provider)