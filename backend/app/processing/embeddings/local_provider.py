"""
app/processing/embeddings/local_provider.py

Local embedding provider backed by Sentence Transformers.

Default:
    BAAI/bge-small-en-v1.5

Runs on CPU by default.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


class LocalEmbeddingProvider:
    """
    Local Sentence Transformers embedding provider.
    """

    PROVIDER_NAME = "local"

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        *,
        device: str = "cpu",
        batch_size: int = 32,
        normalize_embeddings: bool = True,
    ) -> None:

        if not isinstance(
            model_name,
            str,
        ) or not model_name.strip():
            raise ValueError(
                "model_name must not be empty."
            )

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        self._model_name = model_name.strip()
        self._device = device
        self._batch_size = batch_size
        self._normalize_embeddings = normalize_embeddings

        self._model: SentenceTransformer | None = None
        self._dimension: int | None = None

        self._load_lock = asyncio.Lock()

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def name(self) -> str:
        """
        Return provider name.
        """

        return self.PROVIDER_NAME

    @property
    def model(self) -> str:
        """
        Return configured model name.
        """

        return self._model_name

    @property
    def device(self) -> str:
        """
        Return configured device.
        """

        return self._device

    @property
    def batch_size(self) -> int:
        """
        Return configured batch size.
        """

        return self._batch_size

    @property
    def dimension(self) -> int:
        """
        Return embedding vector dimension.

        Loads the model synchronously when dimension information
        is requested before asynchronous initialization.
        """

        if self._dimension is None:
            self._load_model_sync()

        assert self._dimension is not None

        return self._dimension

    # ========================================================================
    # MODEL INITIALIZATION
    # ========================================================================

    async def _ensure_model(
        self,
    ) -> SentenceTransformer:
        """
        Ensure the SentenceTransformer model is loaded.
        """

        if self._model is not None:
            return self._model

        async with self._load_lock:

            if self._model is None:
                await asyncio.to_thread(
                    self._load_model_sync
                )

        assert self._model is not None

        return self._model

    def _load_model_sync(self) -> None:
        """
        Load the embedding model synchronously.
        """

        if self._model is not None:
            return

        logger.info(
            "Loading embedding model '%s' on '%s'.",
            self._model_name,
            self._device,
        )

        try:
            model = SentenceTransformer(
                self._model_name,
                device=self._device,
            )
        except Exception as exc:
            logger.exception(
                "Failed to load local embedding model '%s'.",
                self._model_name,
            )

            raise RuntimeError(
                "Failed to load local embedding model "
                f"'{self._model_name}'."
            ) from exc

        # Sentence Transformers renamed this method.
        #
        # New versions:
        #     get_embedding_dimension()
        #
        # Older versions:
        #     get_sentence_embedding_dimension()
        #
        # Supporting both keeps the provider compatible across
        # Sentence Transformers versions.

        if hasattr(
            model,
            "get_embedding_dimension",
        ):
            dimension = model.get_embedding_dimension()
        else:
            dimension = (
                model.get_sentence_embedding_dimension()
            )

        if dimension is None or dimension <= 0:
            raise RuntimeError(
                "Unable to determine embedding dimension "
                f"for '{self._model_name}'."
            )

        self._model = model
        self._dimension = int(dimension)

        logger.info(
            "Local embedding provider ready: "
            "model=%s dimension=%d device=%s",
            self._model_name,
            self._dimension,
            self._device,
        )

    # ========================================================================
    # EMBEDDING
    # ========================================================================

    async def embed(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for a sequence of texts.
        """

        if not texts:
            return []

        validated = self._validate_texts(
            texts,
        )

        model = await self._ensure_model()

        try:
            embeddings = await asyncio.to_thread(
                model.encode,
                validated,
                batch_size=self._batch_size,
                normalize_embeddings=self._normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

        except Exception as exc:

            logger.exception(
                "Local embedding generation failed."
            )

            raise RuntimeError(
                "Local embedding generation failed."
            ) from exc

        result = embeddings.tolist()

        if not isinstance(
            result,
            list,
        ):
            raise RuntimeError(
                "Embedding provider returned an invalid "
                "result."
            )

        return result

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_texts(
        texts: Sequence[str],
    ) -> list[str]:
        """
        Validate embedding input texts.
        """

        validated: list[str] = []

        for index, text in enumerate(texts):

            if not isinstance(
                text,
                str,
            ):
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

            validated.append(
                cleaned
            )

        return validated

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    async def close(self) -> None:
        """
        Release provider resources.
        """

        self._model = None
        self._dimension = None


__all__ = [
    "LocalEmbeddingProvider",
]