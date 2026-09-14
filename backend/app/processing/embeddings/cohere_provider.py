"""
app/processing/embeddings/cohere_provider.py

Cohere cloud embedding provider.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from typing import Any

import cohere

logger = logging.getLogger(__name__)


class CohereEmbeddingProvider:
    """
    Cohere embedding provider.
    """

    PROVIDER_NAME = "cohere"

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "embed-v4.0",
        input_type: str = "search_document",
        batch_size: int = 96,
    ) -> None:
        if not api_key.strip():
            raise ValueError(
                "Cohere API key must not be empty."
            )

        if not model.strip():
            raise ValueError(
                "Cohere model must not be empty."
            )

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        self._model = model
        self._input_type = input_type
        self._batch_size = batch_size

        self._client = cohere.ClientV2(
            api_key=api_key,
        )

        self._dimension: int | None = None

    @property
    def name(self) -> str:
        return self.PROVIDER_NAME

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            raise RuntimeError(
                "Cohere embedding dimension is not known yet."
            )

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

            embeddings = await self._embed_batch(batch)

            results.extend(embeddings)

        return results

    async def _embed_batch(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        try:
            response = await asyncio.to_thread(
                self._client.embed,
                model=self._model,
                texts=list(texts),
                input_type=self._input_type,
                embedding_types=["float"],
            )
        except Exception as exc:
            logger.exception(
                "Cohere embedding request failed."
            )

            raise RuntimeError(
                "Cohere embedding request failed."
            ) from exc

        embeddings = self._extract_embeddings(
            response
        )

        if len(embeddings) != len(texts):
            raise RuntimeError(
                "Cohere returned an unexpected number "
                "of embeddings."
            )

        if embeddings:
            dimension = len(embeddings[0])

            if dimension <= 0:
                raise RuntimeError(
                    "Cohere returned an invalid dimension."
                )

            if self._dimension is None:
                self._dimension = dimension
            elif self._dimension != dimension:
                raise RuntimeError(
                    "Cohere embedding dimension changed."
                )

        return embeddings

    @staticmethod
    def _extract_embeddings(
        response: Any,
    ) -> list[list[float]]:
        try:
            values = response.embeddings.float
        except AttributeError as exc:
            raise RuntimeError(
                "Unexpected Cohere response structure."
            ) from exc

        if values is None:
            raise RuntimeError(
                "Cohere response contained no embeddings."
            )

        return [
            [float(value) for value in embedding]
            for embedding in values
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