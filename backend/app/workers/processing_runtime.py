"""
Worker-only document-processing runtime.

This module owns the heavy processing infrastructure that must not be
loaded by the FastAPI web process.

Embedding provider configuration is read from application settings.
The heavy embedding runtime is initialized only inside the worker process.
"""

from __future__ import annotations

import logging

from app.core.config import settings

from app.processing.stage_registry import StageRegistry

from app.processing.classification.classifier import (
    ClassificationStage,
)

from app.processing.layout.analyzer import (
    LayoutAnalysisStage,
)

from app.processing.extraction.manager import (
    TextExtractionStage,
)

from app.processing.ocr.manager import (
    OCRStage,
)

from app.processing.structure.detector import (
    StructureDetectionStage,
)

from app.processing.normalization.cleaner import (
    CleaningStage,
)

from app.processing.chunking.chunker import (
    ChunkingStage,
)

from app.processing.enrichment.enricher import (
    MetadataEnrichmentStage,
)

from app.processing.embeddings.factory import (
    EmbeddingConfig,
    create_embedding_service,
)

from app.processing.embeddings.stage import (
    EmbeddingStage,
)

from app.processing.indexing.indexer import (
    IndexingStage,
)

from app.processing.indexing.provider import (
    ProcessingIndexProvider,
)


logger = logging.getLogger(__name__)


def create_embedding_stage() -> EmbeddingStage:
    """
    Create the embedding stage used by the document-processing worker.

    Provider and model configuration come from application settings.
    """

    embedding_config = EmbeddingConfig(
        provider=settings.EMBEDDING_PROVIDER,
        local_model=settings.EMBEDDING_MODEL,
        local_device=settings.EMBEDDING_DEVICE,
        local_batch_size=settings.EMBEDDING_BATCH_SIZE,
        huggingface_api_key=settings.HUGGINGFACE_API_KEY,
        huggingface_model=settings.EMBEDDING_MODEL,
        huggingface_dimension=settings.EMBEDDING_DIMENSION,
        huggingface_batch_size=settings.EMBEDDING_BATCH_SIZE,
    )

    embedding_service = create_embedding_service(
        embedding_config,
    )

    return EmbeddingStage(
        embedding_service,
    )


def create_index_provider() -> ProcessingIndexProvider:
    """
    Create the pgvector indexing provider used by the processing pipeline.
    """

    return ProcessingIndexProvider(
        provider="pgvector",
        config={},
        collection_name="document_chunk_vectors",
    )


def create_stage_registry() -> StageRegistry:
    """
    Create the complete document-processing StageRegistry.

    This function must only run inside the worker process because the
    embedding provider may initialize heavy model infrastructure.
    """

    embedding_stage = create_embedding_stage()

    index_provider = create_index_provider()

    registry = StageRegistry(
        stages=[
            ClassificationStage(),
            LayoutAnalysisStage(),
            TextExtractionStage(),
            OCRStage(),
            StructureDetectionStage(),
            CleaningStage(),
            ChunkingStage(),
            MetadataEnrichmentStage(),
            embedding_stage,
            IndexingStage(
                provider=index_provider,
            ),
        ],
    )

    registry.validate()
    registry.validate_pipeline_order()

    logger.info(
        "Registered processing stages: %s",
        registry.registered_stages(),
    )

    logger.info(
        "Canonical processing pipeline: %s",
        registry.pipeline_stages(),
    )

    logger.info(
        "Processing pipeline complete: %s",
        registry.is_complete(),
    )

    return registry


__all__ = [
    "create_embedding_stage",
    "create_index_provider",
    "create_stage_registry",
]