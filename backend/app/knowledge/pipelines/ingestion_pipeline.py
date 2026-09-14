from typing import Dict, Any, List


class IngestionPipeline:
    """
    Document ingestion orchestration pipeline.

    Converts raw documents into
    searchable knowledge chunks.
    """


    def __init__(
        self,
        parser,
        cleaner,
        metadata_extractor,
        chunker
    ):
        self.parser = parser
        self.cleaner = cleaner
        self.metadata_extractor = metadata_extractor
        self.chunker = chunker



    def ingest(
        self,
        document_path: str
    ) -> Dict[str, Any]:
        """
        Main ingestion workflow.
        """


        # 1. Extract content

        raw_content = self.parser.parse(
            document_path
        )


        # 2. Clean text

        cleaned_content = self.cleaner.clean(
            raw_content
        )


        # 3. Extract metadata

        metadata = self.metadata_extractor.extract(
            document_path
        )


        # 4. Generate chunks

        chunks = self.chunker.split(
            cleaned_content
        )


        return {

            "document": document_path,

            "metadata": metadata,

            "chunks": chunks,

            "chunk_count": len(chunks)

        }