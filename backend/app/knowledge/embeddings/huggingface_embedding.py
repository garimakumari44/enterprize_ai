# knowledge/embeddings/huggingface_embedding.py


from typing import List

from sentence_transformers import SentenceTransformer

from .base import BaseEmbedding



class HuggingFaceEmbedding(BaseEmbedding):


    def __init__(
        self,
        model_name: str = 
        "sentence-transformers/all-MiniLM-L6-v2"
    ):

        self.model = SentenceTransformer(
            model_name
        )



    async def embed_text(
        self,
        text: str
    ) -> List[float]:


        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )


        return embedding.tolist()



    async def embed_documents(
        self,
        texts: List[str]
    ) -> List[List[float]]:


        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )


        return [
            vector.tolist()
            for vector in embeddings
        ]



    @property
    def dimension(self) -> int:

        return self.model.get_sentence_embedding_dimension()