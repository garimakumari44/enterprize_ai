# app/knowledge/chunking/text_chunker.py


from typing import List, Dict, Any

from .base import BaseChunker



class TextChunker(BaseChunker):
    """
    Fixed-size text chunking strategy.
    """


    def chunk(
        self,
        text: str,
        metadata: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:


        metadata = metadata or {}

        words = text.split()

        chunks = []

        start = 0
        chunk_id = 0


        while start < len(words):

            end = start + self.chunk_size

            chunk_words = words[start:end]


            content = " ".join(chunk_words)


            chunks.append(
                {
                    "id": chunk_id,

                    "content": content,

                    "metadata": {
                        **metadata,

                        "chunk_index": chunk_id,

                        "strategy": "text"
                    }
                }
            )


            chunk_id += 1


            start += self.chunk_size - self.overlap



        return chunks