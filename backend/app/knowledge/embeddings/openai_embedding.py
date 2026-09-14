# knowledge/embeddings/openai_embedding.py

from typing import List

from openai import AsyncOpenAI

from .base import BaseEmbedding


class OpenAIEmbedding(BaseEmbedding):

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small"
    ):

        self.client = AsyncOpenAI(
            api_key=api_key
        )

        self.model = model


    async def embed_text(
        self,
        text: str
    ) -> List[float]:

        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding



    async def embed_documents(
        self,
        texts: List[str]
    ) -> List[List[float]]:

        response = await self.client.embeddings.create(
            model=self.model,
            input=texts
        )


        return [
            item.embedding
            for item in response.data
        ]



    @property
    def dimension(self) -> int:

        if self.model == "text-embedding-3-small":
            return 1536

        if self.model == "text-embedding-3-large":
            return 3072

        raise ValueError(
            "Unknown embedding dimension"
        )