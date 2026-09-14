# knowledge/embeddings/base.py

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """
    Abstract embedding provider.
    Any embedding backend must implement this interface.
    """

    @abstractmethod
    async def embed_text(
        self,
        text: str
    ) -> List[float]:
        """
        Generate embedding for a single text.
        """
        pass


    @abstractmethod
    async def embed_documents(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        """
        pass


    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Vector dimension size.
        """
        pass