"""
app/processing/embeddings/factory.py

Embedding provider construction and resolution.

Provider selection policy:

    1. Explicit local
       -> BGE-small loaded locally

    2. Explicit cohere
       -> Cohere remote API

    3. Explicit huggingface
       -> Hugging Face remote inference

    4. auto
       -> Cohere if API key exists
       -> Hugging Face if API key exists
       -> otherwise local BGE-small
"""

from __future__ import annotations

from dataclasses import dataclass

from app.processing.embeddings.base import EmbeddingProvider
from app.processing.embeddings.service import EmbeddingService


@dataclass(frozen=True, slots=True)
class EmbeddingConfig:
    """
    Immutable embedding configuration.
    """

    provider: str = "auto"

    # Local BGE-small
    local_model: str = (
        "BAAI/bge-small-en-v1.5"
    )

    local_device: str = "cpu"

    local_batch_size: int = 32

    # Cohere
    cohere_api_key: str | None = None

    cohere_model: str = "embed-v4.0"

    cohere_input_type: str = (
        "search_document"
    )

    cohere_batch_size: int = 96

    # Hugging Face remote inference
    huggingface_api_key: str | None = None

    huggingface_model: str = (
        "BAAI/bge-small-en-v1.5"
    )

    huggingface_dimension: int = 384

    huggingface_batch_size: int = 32

    huggingface_provider: str = "hf-inference"


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

    if provider == "huggingface":
        return _create_huggingface(config)

    if provider == "auto":
        return _create_auto(config)

    raise ValueError(
        f"Unsupported embedding provider: '{provider}'. "
        "Supported values: auto, local, cohere, huggingface."
    )


def _create_local(config: EmbeddingConfig):
    """
    Import the local provider only when it is actually selected.

    This prevents sentence-transformers/PyTorch from being imported
    when a remote embedding provider is being used.
    """

    from app.processing.embeddings.local_provider import (
        LocalEmbeddingProvider,
    )

    return LocalEmbeddingProvider(
        model_name=config.local_model,
        device=config.local_device,
        batch_size=config.local_batch_size,
    )


def _create_cohere(config: EmbeddingConfig):
    """
    Import Cohere provider only when it is actually selected.
    """

    from app.processing.embeddings.cohere_provider import (
        CohereEmbeddingProvider,
    )

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


def _create_huggingface(config: EmbeddingConfig):
    """
    Create the remote Hugging Face embedding provider.

    The model is NOT downloaded or loaded locally.
    """

    from app.processing.embeddings.huggingface_provider import (
        HuggingFaceEmbeddingProvider,
    )

    if not config.huggingface_api_key:
        raise ValueError(
            "Hugging Face provider selected but "
            "HUGGINGFACE_API_KEY is not configured."
        )

    return HuggingFaceEmbeddingProvider(
        api_key=config.huggingface_api_key,
        model=config.huggingface_model,
        dimension=config.huggingface_dimension,
        batch_size=config.huggingface_batch_size,
        provider=config.huggingface_provider,
    )


def _create_auto(
    config: EmbeddingConfig,
) -> EmbeddingProvider:
    """
    Automatically select a configured provider.

    Priority:

        1. Cohere
        2. Hugging Face
        3. Local BGE-small
    """

    if config.cohere_api_key:
        return _create_cohere(config)

    if config.huggingface_api_key:
        return _create_huggingface(config)

    return _create_local(config)


def create_embedding_service(
    config: EmbeddingConfig,
) -> EmbeddingService:
    provider = create_embedding_provider(config)

    return EmbeddingService(provider)