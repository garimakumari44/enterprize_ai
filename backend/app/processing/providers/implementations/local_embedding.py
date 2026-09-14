
"""
app.processing.providers.implementations.local_embedding

Local embedding provider backed by SentenceTransformers.

Default model
-------------

    BAAI/bge-small-en-v1.5

Default device
--------------

    cpu

The implementation deliberately imports SentenceTransformers lazily.
This prevents the whole backend from failing during startup when the
embedding dependency has not yet been installed.

The model is loaded lazily on first embedding request or startup.
"""

from __future__ import annotations

import logging
from typing import Any

from ..base import (
    ProviderConfigurationError,
    ProviderUnavailableError,
)
from ..embedding import (
    BaseEmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingVector,
)


logger = logging.getLogger(__name__)


class LocalEmbeddingProvider(
    BaseEmbeddingProvider
):
    """
    SentenceTransformers-based local embedding provider.

    Default configuration:

        provider:
            local

        local_model:
            BAAI/bge-small-en-v1.5

        local_device:
            cpu

        local_batch_size:
            32

        normalize:
            True
    """

    PROVIDER_NAME = "local_embedding"

    PROVIDER_TYPE = "embedding"

    VERSION = "1.0"

    DEFAULT_MODEL = (
        "BAAI/bge-small-en-v1.5"
    )

    DEFAULT_DEVICE = "cpu"

    DEFAULT_BATCH_SIZE = 32

    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            config=config
        )

        self._model = None
        self._loaded_model_name: str | None = None

    def _load_sentence_transformers(
        self,
    ):
        try:
            from sentence_transformers import (
                SentenceTransformer,
            )
        except ImportError as exc:
            raise ProviderUnavailableError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        return SentenceTransformer

    @property
    def configured_model(
        self,
    ) -> str:
        return str(
            self.get_config(
                "local_model",
                self.get_config(
                    "model",
                    self.DEFAULT_MODEL,
                ),
            )
        )

    @property
    def configured_device(
        self,
    ) -> str:
        return str(
            self.get_config(
                "local_device",
                self.get_config(
                    "device",
                    self.DEFAULT_DEVICE,
                ),
            )
        )

    @property
    def configured_batch_size(
        self,
    ) -> int:
        value = self.get_config(
            "local_batch_size",
            self.get_config(
                "batch_size",
                self.DEFAULT_BATCH_SIZE,
            ),
        )

        try:
            value = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ProviderConfigurationError(
                "local_batch_size must be an integer."
            ) from exc

        if value < 1:
            raise ProviderConfigurationError(
                "local_batch_size must be >= 1."
            )

        return value

    def validate_config(self) -> None:
        model = self.configured_model

        if not model.strip():
            raise ProviderConfigurationError(
                "Embedding model cannot be empty."
            )

        self.configured_batch_size

        normalize = self.get_config(
            "normalize",
            True,
        )

        if not isinstance(
            normalize,
            bool,
        ):
            raise ProviderConfigurationError(
                "normalize must be a boolean."
            )

    async def health_check(self) -> bool:
        """
        Check whether SentenceTransformers can be imported.

        We intentionally do not download/load the model here.
        """

        try:
            self._load_sentence_transformers()
            return True
        except ProviderUnavailableError:
            return False

    async def startup(self) -> None:
        """
        Validate configuration and optionally preload the model.

        preload_model defaults to False to avoid downloading a model
        during backend startup unexpectedly.
        """

        self.validate_config()

        preload = bool(
            self.get_config(
                "preload_model",
                False,
            )
        )

        if preload:
            self._ensure_model()

    def _ensure_model(self):
        """
        Lazily load the configured SentenceTransformer model.
        """

        model_name = (
            self.configured_model
        )

        if (
            self._model is not None
            and self._loaded_model_name
            == model_name
        ):
            return self._model

        SentenceTransformer = (
            self._load_sentence_transformers()
        )

        device = (
            self.configured_device
        )

        logger.info(
            "Loading local embedding model | "
            "model=%s | device=%s",
            model_name,
            device,
        )

        try:
            model = SentenceTransformer(
                model_name,
                device=device,
            )
        except Exception as exc:
            logger.exception(
                "Failed to load local embedding model '%s'",
                model_name,
            )

            raise ProviderUnavailableError(
                f"Unable to load embedding model "
                f"'{model_name}': {exc}"
            ) from exc

        self._model = model
        self._loaded_model_name = (
            model_name
        )

        return model

    @staticmethod
    def _to_float_list(
        vector: Any,
    ) -> list[float]:
        """
        Convert NumPy/tensor/list output into plain Python floats.
        """

        if hasattr(
            vector,
            "tolist",
        ):
            vector = vector.tolist()

        if not isinstance(
            vector,
            (list, tuple),
        ):
            vector = list(vector)

        return [
            float(value)
            for value in vector
        ]

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """
        Generate local embeddings.
        """

        request.validate()

        model = self._ensure_model()

        batch_size = (
            request.batch_size
            or self.configured_batch_size
        )

        normalize = bool(
            request.normalize
        )

        # Allow request-level override.
        if "normalize" in request.options:
            normalize = bool(
                request.options[
                    "normalize"
                ]
            )

        texts = [
            text.strip()
            for text in request.texts
        ]

        logger.debug(
            "Generating embeddings | "
            "count=%d | model=%s | batch_size=%d | normalize=%s",
            len(texts),
            self.configured_model,
            batch_size,
            normalize,
        )

        try:
            encoded = model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except TypeError:
            # Compatibility fallback for older SentenceTransformers
            # versions that may not accept one of the keyword arguments.
            try:
                encoded = model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
            except Exception as exc:
                raise ProviderUnavailableError(
                    f"Local embedding generation failed: {exc}"
                ) from exc

        except Exception as exc:
            logger.exception(
                "Local embedding generation failed."
            )

            raise ProviderUnavailableError(
                f"Local embedding generation failed: {exc}"
            ) from exc

        if len(texts) == 1:
            # SentenceTransformers normally returns shape:
            #
            #     (1, dimension)
            #
            # but protect against implementations returning a
            # one-dimensional vector.
            if getattr(
                encoded,
                "ndim",
                None,
            ) == 1:
                vectors = [
                    encoded
                ]
            else:
                vectors = list(
                    encoded
                )
        else:
            vectors = list(
                encoded
            )

        if len(vectors) != len(
            texts
        ):
            raise ProviderUnavailableError(
                "Embedding provider returned an unexpected "
                "number of vectors."
            )

        embeddings: list[
            EmbeddingVector
        ] = []

        for index, vector in enumerate(
            vectors
        ):
            chunk_id = None

            if request.chunk_ids:
                chunk_id = str(
                    request.chunk_ids[
                        index
                    ]
                )

            vector_values = (
                self._to_float_list(
                    vector
                )
            )

            embeddings.append(
                EmbeddingVector(
                    vector=vector_values,
                    index=index,
                    chunk_id=chunk_id,
                )
            )

        result = EmbeddingResult(
            embeddings=embeddings,
            model=self.configured_model,
            provider=self.name,
            document_id=request.document_id,
            normalized=normalize,
            metadata={
                "device": self.configured_device,
                "batch_size": batch_size,
            },
        )

        result.validate_dimensions()

        return result

    async def shutdown(self) -> None:
        """
        Release the in-process model reference.

        PyTorch/SentenceTransformers manages the underlying resources.
        Clearing the reference allows Python to reclaim them.
        """

        self._model = None
        self._loaded_model_name = None

