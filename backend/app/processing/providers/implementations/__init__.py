
"""
app.processing.providers.implementations

Concrete provider implementations.

This module intentionally exposes implementations explicitly instead
of performing automatic module discovery. Explicit registration makes
startup behavior deterministic and easier to diagnose.
"""

from .azure_ocr import AzureOCRProvider
from .basic_layout import BasicLayoutProvider
from .document_enricher import DocumentEnricher
from .local_embedding import LocalEmbeddingProvider
from .paddle_ocr import PaddleOCRProvider
from .pdf_extractor import PDFExtractor
from .pgvector_indexer import PGVectorIndexer
from .rule_based_classifier import RuleBasedClassifier
from .rule_based_structure import RuleBasedStructureProvider
from .semantic_chunker import SemanticChunker
from .tesseract_ocr import TesseractOCRProvider


__all__ = [
    "AzureOCRProvider",
    "BasicLayoutProvider",
    "DocumentEnricher",
    "LocalEmbeddingProvider",
    "PaddleOCRProvider",
    "PDFExtractor",
    "PGVectorIndexer",
    "RuleBasedClassifier",
    "RuleBasedStructureProvider",
    "SemanticChunker",
    "TesseractOCRProvider",
]

