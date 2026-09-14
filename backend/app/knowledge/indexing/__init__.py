"""
Knowledge Indexing Layer

Responsible for:
- Building document indexes
- Managing index lifecycle
- Optimizing retrieval performance
"""

from .index_builder import IndexBuilder
from .index_manager import IndexManager
from .index_optimizer import IndexOptimizer


__all__ = [
    "IndexBuilder",
    "IndexManager",
    "IndexOptimizer",
]