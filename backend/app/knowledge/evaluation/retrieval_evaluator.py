from typing import List, Dict


class RetrievalEvaluator:
    """
    Evaluates document retrieval quality.
    """


    def __init__(self):
        pass


    def precision_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        k: int = 5
    ) -> float:
        """
        Percentage of retrieved documents that are relevant.
        """


        retrieved = retrieved_ids[:k]

        if not retrieved:
            return 0.0


        relevant = set(relevant_ids)


        hits = sum(
            1 for doc_id in retrieved
            if doc_id in relevant
        )


        return hits / len(retrieved)



    def recall_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        k: int = 5
    ) -> float:
        """
        Percentage of relevant documents retrieved.
        """


        if not relevant_ids:
            return 0.0


        retrieved = retrieved_ids[:k]


        relevant = set(relevant_ids)


        hits = sum(
            1 for doc_id in retrieved
            if doc_id in relevant
        )


        return hits / len(relevant)



    def hit_rate(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str]
    ) -> float:
        """
        Checks if at least one relevant document appears.
        """


        relevant = set(relevant_ids)


        for doc_id in retrieved_ids:

            if doc_id in relevant:
                return 1.0


        return 0.0



    def evaluate(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        k: int = 5
    ) -> Dict:


        return {

            "precision@k":
                self.precision_at_k(
                    retrieved_ids,
                    relevant_ids,
                    k
                ),


            "recall@k":
                self.recall_at_k(
                    retrieved_ids,
                    relevant_ids,
                    k
                ),


            "hit_rate":
                self.hit_rate(
                    retrieved_ids,
                    relevant_ids
                )
        }