# app/knowledge/chunking/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseChunker(ABC):
    """
    Abstract interface for document chunking strategies.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap


    @abstractmethod
    def chunk(
        self,
        text: str,
        metadata: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Split document into chunks.

        Returns:
            [
                {
                    "content": "...",
                    "metadata": {}
                }
            ]
        """

        pass