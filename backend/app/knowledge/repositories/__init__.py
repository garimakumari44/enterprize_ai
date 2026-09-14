"""
Repository Layer

This package contains all database access repositories used by the
Knowledge & Search module.

Repositories are responsible only for persistence and database queries.
Business logic belongs in the service layer.
"""

from .chunk_repository import ChunkRepository
from .embedding_repository import EmbeddingRepository
from .collection_repository import CollectionRepository
# from .relation_repository import RelationRepository
from .search_repository import SearchRepository

__all__ = [
    "ChunkRepository",
    "EmbeddingRepository",
    "CollectionRepository",
    # "RelationRepository",
    "SearchRepository",
]