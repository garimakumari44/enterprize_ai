# app/knowledge/chunking/recursive_chunker.py


from typing import List, Dict, Any

from .base import BaseChunker



class RecursiveChunker(BaseChunker):
    """
    Hierarchical recursive text splitter.

    Similar approach used in
    modern RAG frameworks.
    """


    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
        separators=None
    ):

        super().__init__(
            chunk_size,
            overlap
        )


        self.separators = separators or [

            "\n\n",   # paragraphs

            "\n",     # lines

            ".",      # sentences

            " ",      # words

        ]



    def chunk(
        self,
        text: str,
        metadata: Dict[str, Any] | None = None
    ):


        metadata = metadata or {}


        raw_chunks = self._split_recursive(
            text,
            self.separators
        )


        chunks = []


        for index, content in enumerate(raw_chunks):

            chunks.append(

                {
                    "id": index,

                    "content": content.strip(),

                    "metadata":
                    {
                        **metadata,

                        "chunk_index": index,

                        "strategy":
                        "recursive"
                    }
                }

            )


        return chunks



    def _split_recursive(
        self,
        text: str,
        separators: List[str]
    ):


        if len(text.split()) <= self.chunk_size:

            return [
                text
            ]



        if not separators:

            return self._hard_split(text)



        separator = separators[0]


        parts = text.split(separator)



        chunks = []

        current = ""



        for part in parts:


            candidate = (
                current +
                separator +
                part
            )



            if len(candidate.split()) <= self.chunk_size:


                current = candidate



            else:


                if current:

                    chunks.append(
                        current
                    )


                current = part



        if current:

            chunks.append(current)



        final_chunks = []



        for chunk in chunks:


            if len(chunk.split()) > self.chunk_size:


                final_chunks.extend(

                    self._split_recursive(
                        chunk,
                        separators[1:]
                    )

                )

            else:

                final_chunks.append(chunk)



        return final_chunks



    def _hard_split(
        self,
        text
    ):


        words = text.split()


        result=[]


        for i in range(
            0,
            len(words),
            self.chunk_size
        ):


            result.append(

                " ".join(
                    words[
                        i:i+self.chunk_size
                    ]
                )

            )


        return result