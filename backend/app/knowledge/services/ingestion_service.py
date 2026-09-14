from __future__ import annotations

from typing import Any, Dict

from app.knowledge.ingestion.document_ingestor import DocumentIngestor
from app.knowledge.processing.document_preprocessor import DocumentPreprocessor
from app.knowledge.chunking.chunk_optimizer import ChunkOptimizer


class IngestionService:
    """
    Handles complete document ingestion.
    """

    def __init__(
        self,
        ingestor: DocumentIngestor,
        preprocessor: DocumentPreprocessor,
        chunker: ChunkOptimizer,
    ) -> None:

        self.ingestor = ingestor
        self.preprocessor = preprocessor
        self.chunker = chunker

    async def ingest_document(
        self,
        file_path: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Complete ingestion process.
        """

        # Parse document
        document = await self.ingestor.ingest(file_path)

        # Clean content
        cleaned = self.preprocessor.process(document.content)

        # Create chunks
        chunks = self.chunker.chunk(cleaned)

        return {
            "id": document.id,
            "title": document.title,
            "metadata": metadata,
            "content": cleaned,
            "chunks": chunks,
        }