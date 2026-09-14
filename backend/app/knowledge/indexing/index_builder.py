from typing import List, Dict, Any
from datetime import datetime
import uuid


class IndexBuilder:
    """
    Builds searchable indexes from document chunks.

    Responsibilities:
    - Prepare documents
    - Validate embeddings
    - Insert vectors
    - Attach metadata
    """


    def __init__(self, vector_store):
        """
        vector_store:
            pgvector/qdrant/pinecone/weaviate implementation
        """

        self.vector_store = vector_store



    async def build_index(
        self,
        chunks: List[Dict[str, Any]],
        collection_name: str
    ):
        """
        Build index from document chunks.


        Example chunk:

        {
            "text": "invoice total amount",
            "embedding": [0.123,0.456],
            "metadata": {
                "document_id":123,
                "page":4
            }
        }

        """

        vectors = []


        for chunk in chunks:

            vector = {
                "id": str(uuid.uuid4()),

                "text": chunk["text"],

                "embedding": chunk["embedding"],

                "metadata": {
                    **chunk.get("metadata", {}),

                    "indexed_at":
                        datetime.utcnow().isoformat()
                }
            }


            vectors.append(vector)



        result = await self.vector_store.upsert(
            collection_name=collection_name,
            vectors=vectors
        )


        return {
            "collection": collection_name,
            "vectors_indexed": len(vectors),
            "result": result
        }




    async def rebuild_index(
        self,
        collection_name: str,
        chunks: List[Dict[str,Any]]
    ):

        """
        Full rebuild.
        Used when embeddings/model changes.
        """


        await self.vector_store.delete_collection(
            collection_name
        )


        return await self.build_index(
            chunks,
            collection_name
        )