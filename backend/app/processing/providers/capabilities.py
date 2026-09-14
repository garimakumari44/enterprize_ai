
"""
app.processing.providers.capabilities

Canonical capability definitions for document-processing providers.

Capabilities are represented as strings so the provider system remains
easy to extend and serialize.

Example:

    provider.supports(
        ProviderCapability.TEXT_EXTRACTION
    )
"""

from __future__ import annotations

from enum import Enum


class ProviderCapability(str, Enum):
    """Capabilities that processing providers may implement."""

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    TEXT_EXTRACTION = "text_extraction"

    PDF_EXTRACTION = "pdf_extraction"

    IMAGE_EXTRACTION = "image_extraction"

    TABLE_EXTRACTION = "table_extraction"

    METADATA_EXTRACTION = "metadata_extraction"

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    OCR = "ocr"

    MULTI_LANGUAGE_OCR = "multi_language_ocr"

    TABLE_OCR = "table_ocr"

    HANDWRITING_OCR = "handwriting_ocr"

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    DOCUMENT_CLASSIFICATION = "document_classification"

    MULTI_LABEL_CLASSIFICATION = "multi_label_classification"

    CONFIDENCE_SCORING = "confidence_scoring"

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    LAYOUT_ANALYSIS = "layout_analysis"

    BLOCK_DETECTION = "block_detection"

    TABLE_DETECTION = "table_detection"

    IMAGE_DETECTION = "image_detection"

    # ------------------------------------------------------------------
    # Structure
    # ------------------------------------------------------------------

    STRUCTURE_DETECTION = "structure_detection"

    HEADING_DETECTION = "heading_detection"

    SECTION_DETECTION = "section_detection"

    LIST_DETECTION = "list_detection"

    # ------------------------------------------------------------------
    # Text processing
    # ------------------------------------------------------------------

    TEXT_CLEANING = "text_cleaning"

    CHUNKING = "chunking"

    SEMANTIC_CHUNKING = "semantic_chunking"

    TOKEN_AWARE_CHUNKING = "token_aware_chunking"

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    METADATA_ENRICHMENT = "metadata_enrichment"

    ENTITY_EXTRACTION = "entity_extraction"

    LANGUAGE_DETECTION = "language_detection"

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    EMBEDDING = "embedding"

    BATCH_EMBEDDING = "batch_embedding"

    NORMALIZED_EMBEDDINGS = "normalized_embeddings"

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    INDEXING = "indexing"

    VECTOR_INDEXING = "vector_indexing"

    KEYWORD_INDEXING = "keyword_indexing"

    HYBRID_INDEXING = "hybrid_indexing"

    # ------------------------------------------------------------------
    # Operational capabilities
    # ------------------------------------------------------------------

    ASYNC = "async"

    BATCH_PROCESSING = "batch_processing"

    STREAMING = "streaming"

    LOCAL_EXECUTION = "local_execution"

    REMOTE_EXECUTION = "remote_execution"

    GPU_ACCELERATION = "gpu_acceleration"


# Convenient aliases for code that prefers constants over enum members.

TEXT_EXTRACTION = ProviderCapability.TEXT_EXTRACTION
PDF_EXTRACTION = ProviderCapability.PDF_EXTRACTION
OCR = ProviderCapability.OCR
DOCUMENT_CLASSIFICATION = (
    ProviderCapability.DOCUMENT_CLASSIFICATION
)
LAYOUT_ANALYSIS = ProviderCapability.LAYOUT_ANALYSIS
STRUCTURE_DETECTION = (
    ProviderCapability.STRUCTURE_DETECTION
)
CHUNKING = ProviderCapability.CHUNKING
METADATA_ENRICHMENT = (
    ProviderCapability.METADATA_ENRICHMENT
)
EMBEDDING = ProviderCapability.EMBEDDING
INDEXING = ProviderCapability.INDEXING


def normalize_capability(
    capability: str | ProviderCapability,
) -> str:
    """
    Normalize a capability to its canonical string value.

    Examples:

        normalize_capability(
            ProviderCapability.OCR
        )

        normalize_capability("ocr")
    """

    if isinstance(
        capability,
        ProviderCapability,
    ):
        return capability.value

    if not isinstance(
        capability,
        str,
    ):
        raise TypeError(
            "capability must be a string or "
            "ProviderCapability."
        )

    normalized = capability.strip().lower()

    if not normalized:
        raise ValueError(
            "capability cannot be empty."
        )

    return normalized


def capabilities_to_strings(
    capabilities: set[
        str | ProviderCapability
    ],
) -> set[str]:
    """Convert a capability collection to normalized strings."""

    return {
        normalize_capability(capability)
        for capability in capabilities
    }


def has_capability(
    capabilities: set[
        str | ProviderCapability
    ],
    capability: str | ProviderCapability,
) -> bool:
    """Check whether a capability collection contains a capability."""

    normalized = normalize_capability(
        capability
    )

    return normalized in capabilities_to_strings(
        capabilities
    )

