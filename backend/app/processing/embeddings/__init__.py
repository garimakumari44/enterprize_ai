"""
app.processing.embeddings

Embedding infrastructure for document processing.
"""

from app.processing.embeddings.base import EmbeddingProvider
from app.processing.embeddings.cohere_provider import (
    CohereEmbeddingProvider,
)
from app.processing.embeddings.factory import (
    EmbeddingConfig,
    create_embedding_provider,
    create_embedding_service,
)
from app.processing.embeddings.local_provider import (
    LocalEmbeddingProvider,
)
from app.processing.embeddings.service import EmbeddingService

__all__ = [
    "CohereEmbeddingProvider",
    "EmbeddingConfig",
    "EmbeddingProvider",
    "EmbeddingService",
    "LocalEmbeddingProvider",
    "create_embedding_provider",
    "create_embedding_service",
]