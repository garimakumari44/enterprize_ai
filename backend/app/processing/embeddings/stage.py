
"""
app/processing/embeddings/stage.py

Embedding processing stage.

Architecture
------------

    ProcessingContext
           |
           v
    EmbeddingStage
           |
           v
    EmbeddingService
           |
           v
    EmbeddingProvider
           |
      +----+----+
      |         |
      v         v
    Local     Remote

Responsibilities
----------------

    - Read embedding-source chunks from ProcessingContext
    - Extract text from those chunks
    - Generate embeddings through EmbeddingService
    - Store embeddings back into ProcessingContext

This stage does not:

    - Know how providers are constructed
    - Access databases
    - Access vector stores
    - Know provider-specific implementation details
"""

from __future__ import annotations

import logging
from typing import Any

from app.processing.embeddings.service import EmbeddingService
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


logger = logging.getLogger(__name__)


class EmbeddingStage(DocumentProcessingStage):
    """
    Processing pipeline stage responsible for generating embeddings.

    The stage depends on EmbeddingService rather than directly on an
    embedding provider.

    This keeps provider selection and provider implementation details
    outside the processing pipeline.
    """

    @property
    def name(self) -> str:
        """
        Return the canonical processing-stage name.
        """

        return "embedding"

    def __init__(
        self,
        service: EmbeddingService,
    ) -> None:

        if service is None:
            raise ValueError(
                "EmbeddingService must not be None."
            )

        self._service = service

    @property
    def service(self) -> EmbeddingService:
        """
        Return the configured embedding service.
        """

        return self._service

    async def process(
        self,
        context: ProcessingContext,
        session: Any = None,
    ) -> ProcessingContext:
        """
        Generate embeddings for the current embedding-source chunks.

        Parameters
        ----------
        context:
            Current document processing context.

        session:
            Optional job-scoped database session supplied by the
            processing pipeline.

            EmbeddingStage does not currently require database access,
            so this argument is intentionally unused. It is accepted
            to maintain the common processing-stage interface used by
            the pipeline.

        Returns
        -------
        ProcessingContext
            The updated processing context containing generated
            embeddings.
        """

        if not isinstance(
            context,
            ProcessingContext,
        ):
            raise TypeError(
                "EmbeddingStage.process() requires a "
                "ProcessingContext."
            )

        chunks = context.embedding_source_chunks

        if not chunks:
            logger.info(
                "Embedding stage skipped: "
                "no embedding-source chunks."
            )

            context.set_embeddings([])

            return context

        texts = [
            self._extract_text(
                chunk,
                index,
            )
            for index, chunk in enumerate(chunks)
        ]

        logger.info(
            "Generating embeddings: "
            "chunks=%d provider=%s model=%s",
            len(texts),
            self._service.provider_name,
            self._service.model,
        )

        embeddings = await self._service.embed(
            texts,
        )

        context.set_embeddings(
            embeddings,
        )

        logger.info(
            "Embedding stage completed: "
            "embeddings=%d dimension=%d",
            len(embeddings),
            self._service.dimension,
        )

        return context

    @staticmethod
    def _extract_text(
        chunk: Any,
        index: int,
    ) -> str:
        """
        Extract textual content from a chunk.

        Supports:

            - object.text
            - mapping["text"]
        """

        if isinstance(
            chunk,
            dict,
        ):
            text = chunk.get("text")
        else:
            text = getattr(
                chunk,
                "text",
                None,
            )

        if not isinstance(
            text,
            str,
        ):
            raise TypeError(
                f"Embedding source chunk at index {index} "
                "does not contain a valid text value."
            )

        text = text.strip()

        if not text:
            raise ValueError(
                f"Embedding source chunk at index {index} "
                "contains empty text."
            )

        return text

    async def close(self) -> None:
        """
        Release resources owned by the embedding provider.
        """

        await self._service.close()


__all__ = [
    "EmbeddingStage",
]
