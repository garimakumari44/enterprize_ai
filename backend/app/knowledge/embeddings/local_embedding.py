# knowledge/embeddings/local_embedding.py

from typing import List

from sentence_transformers import SentenceTransformer

from .base import BaseEmbedding



class LocalEmbedding(BaseEmbedding):
    """
    Local embedding provider.

    Runs embedding models inside your infrastructure.
    """


    def __init__(
        self,
        model_name: str,
        device: str = "cpu"
    ):

        self.model_name = model_name

        self.model = SentenceTransformer(
            model_name,
            device=device
        )


    async def embed_text(
        self,
        text: str
    ) -> List[float]:

        vector = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return vector.tolist()



    async def embed_documents(
        self,
        texts: List[str]
    ) -> List[List[float]]:


        vectors = self.model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True
        )


        return [
            vector.tolist()
            for vector in vectors
        ]



    @property
    def dimension(self) -> int:

        return (
            self.model
            .get_sentence_embedding_dimension()
        )