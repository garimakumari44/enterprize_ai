# app/knowledge/chunking/chunk_optimizer.py


from typing import List, Dict, Any



class ChunkOptimizer:
    """
    Production chunk quality optimizer.
    """



    def __init__(
        self,
        min_chunk_size: int = 50,
        max_chunk_size: int = 700
    ):

        self.min_chunk_size = (
            min_chunk_size
        )

        self.max_chunk_size = (
            max_chunk_size
        )



    def optimize(
        self,
        chunks: List[Dict[str, Any]]
    ):


        chunks = self.remove_empty(
            chunks
        )


        chunks = self.remove_duplicates(
            chunks
        )


        chunks = self.merge_small_chunks(
            chunks
        )


        chunks = self.add_quality_score(
            chunks
        )


        return chunks



    def remove_empty(
        self,
        chunks
    ):


        return [

            c for c in chunks

            if c["content"].strip()

        ]



    def remove_duplicates(
        self,
        chunks
    ):


        seen=set()

        result=[]


        for chunk in chunks:


            content = chunk["content"]



            if content not in seen:

                seen.add(content)

                result.append(chunk)



        return result




    def merge_small_chunks(
        self,
        chunks
    ):


        optimized=[]


        buffer=""


        for chunk in chunks:


            words=len(
                chunk["content"].split()
            )



            if words < self.min_chunk_size:


                buffer += (
                    " "
                    +
                    chunk["content"]
                )



            else:


                if buffer:

                    chunk["content"] = (
                        buffer
                        +
                        " "
                        +
                        chunk["content"]
                    )

                    buffer=""



                optimized.append(chunk)



        return optimized




    def add_quality_score(
        self,
        chunks
    ):


        for chunk in chunks:


            length=len(
                chunk["content"].split()
            )


            score = min(
                length /
                self.max_chunk_size,
                1
            )


            chunk["metadata"][
                "quality_score"
            ] = round(
                score,
                2
            )


        return chunks