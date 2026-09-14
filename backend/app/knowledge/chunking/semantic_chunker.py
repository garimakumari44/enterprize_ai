# app/knowledge/chunking/semantic_chunker.py


from typing import List, Dict, Any

from .base import BaseChunker



class SemanticChunker(BaseChunker):
    """
    Semantic meaning based chunking.

    Uses sentence embeddings
    to detect topic boundaries.
    """


    def __init__(
        self,
        embedding_service,
        similarity_threshold: float = 0.75,
        max_chunk_size: int = 500
    ):

        self.embedding_service = embedding_service

        self.similarity_threshold = (
            similarity_threshold
        )

        self.max_chunk_size = max_chunk_size



    def chunk(
        self,
        text: str,
        metadata: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:


        metadata = metadata or {}


        sentences = self._split_sentences(text)


        embeddings = (
            self.embedding_service.embed(
                sentences
            )
        )


        chunks = []

        current_chunk = []

        chunk_id = 0



        for i, sentence in enumerate(sentences):


            if not current_chunk:

                current_chunk.append(sentence)

                continue



            similarity = (
                self._similarity(
                    embeddings[i-1],
                    embeddings[i]
                )
            )


            if similarity >= self.similarity_threshold:


                current_chunk.append(sentence)


            else:


                chunks.append(
                    self._create_chunk(
                        chunk_id,
                        current_chunk,
                        metadata
                    )
                )


                chunk_id += 1


                current_chunk = [
                    sentence
                ]



        if current_chunk:

            chunks.append(
                self._create_chunk(
                    chunk_id,
                    current_chunk,
                    metadata
                )
            )


        return chunks



    def _split_sentences(
        self,
        text: str
    ) -> List[str]:

        return [
            s.strip()
            for s in text.split(".")
            if s.strip()
        ]



    def _similarity(
        self,
        a,
        b
    ):

        """
        Placeholder cosine similarity.
        Replace with numpy/sklearn.
        """

        return sum(
            x*y
            for x,y in zip(a,b)
        )



    def _create_chunk(
        self,
        chunk_id,
        sentences,
        metadata
    ):


        return {

            "id": chunk_id,

            "content":
                ". ".join(sentences),

            "metadata":
            {
                **metadata,

                "chunk_index": chunk_id,

                "strategy":"semantic"
            }
        }