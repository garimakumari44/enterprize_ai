from typing import List, Dict, Any



class IndexingPipeline:
    """
    Builds searchable indexes
    from document chunks.
    """



    def __init__(
        self,
        embedding_service,
        vector_store,
        keyword_index
    ):

        self.embedding_service = embedding_service

        self.vector_store = vector_store

        self.keyword_index = keyword_index



    def index(
        self,
        chunks: List[Dict[str,Any]]
    ):


        indexed_documents = []


        for chunk in chunks:


            text = chunk["text"]


            # Generate embedding

            embedding = (
                self.embedding_service
                .embed(text)
            )


            record = {

                "id": chunk["id"],

                "text": text,

                "embedding": embedding,

                "metadata":
                    chunk.get(
                        "metadata",
                        {}
                    )
            }



            # Store vector

            self.vector_store.insert(
                record
            )


            # Keyword index

            self.keyword_index.add(
                record
            )


            indexed_documents.append(
                record
            )


        return {

            "indexed": True,

            "documents":
                len(indexed_documents)

        }