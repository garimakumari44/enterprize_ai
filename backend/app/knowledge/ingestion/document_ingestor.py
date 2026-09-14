from .content_parser import ContentParser
from .metadata_extractor import MetadataExtractor



class DocumentIngestor:
    """
    Converts documents into
    knowledge objects.
    """


    def __init__(self):

        self.parser = ContentParser()

        self.metadata = MetadataExtractor()



    def ingest(
        self,
        file_path: str,
        metadata: dict | None = None
    ) -> dict:


        content = self.parser.parse(
            file_path
        )


        document_metadata = (
            self.metadata.extract(
                file_path,
                metadata
            )
        )


        return {

            "content":
                content["text"],


            "metadata":
                document_metadata,


            "status":
                "READY_FOR_CHUNKING"

        }