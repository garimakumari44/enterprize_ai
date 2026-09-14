"""
Vector Store Package

Provides a unified abstraction layer for multiple vector databases.

Supported Providers:
    - PostgreSQL + pgvector
    - Qdrant
    - Pinecone
    - Weaviate

Used by:
    AI Knowledge Pipeline
    RAG System
    Semantic Search
    Document Intelligence
"""


from .base import (
    BaseVectorStore
)


from .pgvector import (
    PGVectorStore,
)


from .qdrant import (
    QdrantVectorStore,
)


from .pinecone import (
    PineconeVectorStore,
)


from .weaviate import (
    WeaviateVectorStore,
)


from .vector_manager import (
    VectorStoreManager,
)


__all__ = [

    # Interfaces
    "BaseVectorStore",


    # Providers
    "PGVectorStore",
    "QdrantVectorStore",
    "PineconeVectorStore",
    "WeaviateVectorStore",


    # Manager
    "VectorStoreManager",
]