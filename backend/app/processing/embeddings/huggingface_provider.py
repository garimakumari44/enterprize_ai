"""
app/processing/embeddings/huggingface_provider.py

Remote Hugging Face embedding provider.

Uses Hugging Face Inference Providers instead of loading
the embedding model locally.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingProvider:
    """
    Remote Hugging Face embedding provider.

    The model runs remotely on Hugging Face.

    No SentenceTransformer or PyTorch model is loaded
    into the application process.
    """

    PROVIDER_NAME = "huggingface"

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "BAAI/bge-small-en-v1.5",
        dimension: int = 384,
        batch_size: int = 32,
        provider: str = "hf-inference",
    ) -> None:

        if not api_key or not api_key.strip():
            raise ValueError(
                "Hugging Face API key must not be empty."
            )

        if not model or not model.strip():
            raise ValueError(
                "Hugging Face model must not be empty."
            )

        if dimension <= 0:
            raise ValueError(
                "Embedding dimension must be greater than zero."
            )

        if batch_size <= 0:
            raise ValueError(
                "Batch size must be greater than zero."
            )

        self._model = model.strip()
        self._dimension = dimension
        self._batch_size = batch_size
        self._provider = provider

        self._client = InferenceClient(
            provider=self._provider,
            api_key=api_key.strip(),
        )

    @property
    def name(self) -> str:
        return self.PROVIDER_NAME

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        validated = self._validate_texts(texts)

        results: list[list[float]] = []

        for start in range(
            0,
            len(validated),
            self._batch_size,
        ):
            batch = validated[
                start : start + self._batch_size
            ]

            embeddings = await self._embed_batch(
                batch
            )

            results.extend(embeddings)

        return results

    async def _embed_batch(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:

        try:
            embeddings = await asyncio.to_thread(
                self._client.feature_extraction,
                list(texts),
                model=self._model,
            )

        except Exception as exc:

            logger.exception(
                "Hugging Face embedding request failed."
            )

            raise RuntimeError(
                "Hugging Face embedding request failed."
            ) from exc

        result = self._normalize_response(
            embeddings
        )

        if len(result) != len(texts):
            raise RuntimeError(
                "Hugging Face returned an unexpected "
                "number of embeddings."
            )

        for index, vector in enumerate(result):

            if len(vector) != self._dimension:
                raise RuntimeError(
                    "Hugging Face returned an embedding "
                    f"with dimension {len(vector)} at "
                    f"index {index}; expected "
                    f"{self._dimension}."
                )

        return result

    @staticmethod
    def _normalize_response(
        embeddings,
    ) -> list[list[float]]:

        if hasattr(embeddings, "tolist"):
            embeddings = embeddings.tolist()

        if not isinstance(embeddings, list):
            raise RuntimeError(
                "Unexpected Hugging Face embedding response."
            )

        return [
            [float(value) for value in embedding]
            for embedding in embeddings
        ]

    @staticmethod
    def _validate_texts(
        texts: Sequence[str],
    ) -> list[str]:

        validated: list[str] = []

        for index, text in enumerate(texts):

            if not isinstance(text, str):
                raise ValueError(
                    f"Embedding input at index {index} "
                    "must be a string."
                )

            cleaned = text.strip()

            if not cleaned:
                raise ValueError(
                    f"Embedding input at index {index} "
                    "is empty."
                )

            validated.append(cleaned)

        return validated

    async def close(self) -> None:
        return


__all__ = [
    "HuggingFaceEmbeddingProvider",
]