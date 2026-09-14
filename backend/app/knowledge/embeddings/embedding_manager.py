# knowledge/embeddings/embedding_manager.py


from typing import List, Dict

from .base import BaseEmbedding



class EmbeddingManager:
    """
    Central embedding orchestration service.
    """


    def __init__(
        self,
        provider: BaseEmbedding
    ):

        self.provider = provider



    async def embed(
        self,
        text: str
    ) -> List[float]:

        """
        Generate embedding for one text.
        """

        return await (
            self.provider
            .embed_text(text)
        )



    async def embed_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:

        """
        Generate embeddings for multiple chunks.
        """

        if not texts:
            return []


        return await (
            self.provider
            .embed_documents(texts)
        )



    def get_dimension(self) -> int:

        return self.provider.dimension