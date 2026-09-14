from .document_ingestor import DocumentIngestor



class KnowledgeIngestionPipeline:
    """
    Main knowledge ingestion workflow.
    """


    def __init__(self):

        self.ingestor = (
            DocumentIngestor()
        )



    async def run(
        self,
        file_path: str,
        metadata: dict | None = None
    ):


        document = (
            self.ingestor.ingest(
                file_path,
                metadata
            )
        )


        #
        # Future phases:
        #
        # chunks = chunk_service.create()
        #
        # embeddings = embedding_service.generate()
        #
        # vector_store.index()
        #


        return {

            "document":
                document,


            "next_step":
                "CHUNKING"

        }