
"""
app.processing.providers

Public API for the document-processing provider layer.

Keep concrete implementations out of this module whenever possible.
The processing pipeline should depend on contracts, not implementation
details.
"""

from .base import (
    BaseProvider,
    BaseProcessingProvider,
    ProviderResult,
)

from .capabilities import (
    ProviderCapability,
    normalize_capability,
)

from .classification import (
    BaseClassificationProvider,
    ClassificationLabel,
    ClassificationRequest,
    ClassificationResult,
)

from .chunking import (
    BaseChunkingProvider,
    ChunkingRequest,
    ChunkingResult,
    DocumentChunk,
)

from .embedding import (
    BaseEmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingVector,
)

from .enrichment import (
    BaseEnrichmentProvider,
    EnrichmentField,
    EnrichmentRequest,
    EnrichmentResult,
    Entity,
)

from .extraction import (
    BaseExtractionProvider,
)

from .indexing import (
    BaseIndexingProvider,
    IndexDocument,
    IndexingRequest,
    IndexingResult,
)

from .layout import (
    BaseLayoutProvider,
    BoundingBox,
    LayoutAnalysisRequest,
    LayoutAnalysisResult,
    LayoutBlock,
    LayoutPage,
)

from .ocr import (
    BaseOCRProvider,
    OCRLine,
    OCRPageResult,
    OCRRequest,
    OCRResult,
    OCRWord,
)

from .registry import (
    ProviderRegistry,
    provider_registry,
)

from .structure import (
    BaseStructureProvider,
    DocumentStructure,
    StructureDetectionRequest,
    StructureNode,
)

from .factory import (
    ProviderDefinition,
    ProviderFactory,
    constructor_from_class,
    provider_factory,
    register_provider_class,
)


__all__ = [
    # Base
    "BaseProvider",
    "BaseProcessingProvider",
    "ProviderResult",

    # Capabilities
    "ProviderCapability",
    "normalize_capability",

    # Classification
    "BaseClassificationProvider",
    "ClassificationLabel",
    "ClassificationRequest",
    "ClassificationResult",

    # Chunking
    "BaseChunkingProvider",
    "ChunkingRequest",
    "ChunkingResult",
    "DocumentChunk",

    # Embedding
    "BaseEmbeddingProvider",
    "EmbeddingRequest",
    "EmbeddingResult",
    "EmbeddingVector",

    # Enrichment
    "BaseEnrichmentProvider",
    "EnrichmentField",
    "EnrichmentRequest",
    "EnrichmentResult",
    "Entity",

    # Extraction
    "BaseExtractionProvider",

    # Indexing
    "BaseIndexingProvider",
    "IndexDocument",
    "IndexingRequest",
    "IndexingResult",

    # Layout
    "BaseLayoutProvider",
    "BoundingBox",
    "LayoutAnalysisRequest",
    "LayoutAnalysisResult",
    "LayoutBlock",
    "LayoutPage",

    # OCR
    "BaseOCRProvider",
    "OCRLine",
    "OCRPageResult",
    "OCRRequest",
    "OCRResult",
    "OCRWord",

    # Registry
    "ProviderRegistry",
    "provider_registry",

    # Structure
    "BaseStructureProvider",
    "DocumentStructure",
    "StructureDetectionRequest",
    "StructureNode",

    # Factory
    "ProviderDefinition",
    "ProviderFactory",
    "constructor_from_class",
    "provider_factory",
    "register_provider_class",
]

