from typing import List


class RankingEvaluator:
    """
    Evaluates search ranking quality.
    """


    def __init__(self):
        pass



    def reciprocal_rank(
        self,
        ranked_ids: List[str],
        relevant_ids: List[str]
    ) -> float:
        """
        Mean Reciprocal Rank calculation.
        """


        relevant = set(relevant_ids)


        for index, doc_id in enumerate(ranked_ids):

            if doc_id in relevant:

                rank = index + 1

                return 1 / rank


        return 0.0



    def dcg(
        self,
        relevance_scores: List[int]
    ) -> float:

        score = 0.0


        for i, rel in enumerate(relevance_scores):

            position = i + 1


            score += (
                rel /
                __import__("math").log2(
                    position + 1
                )
            )


        return score



    def ndcg(
        self,
        relevance_scores: List[int]
    ) -> float:
        """
        Normalized Discounted Cumulative Gain
        """


        actual = self.dcg(
            relevance_scores
        )


        ideal = self.dcg(
            sorted(
                relevance_scores,
                reverse=True
            )
        )


        if ideal == 0:
            return 0.0


        return actual / ideal



    def evaluate(
        self,
        ranked_ids: List[str],
        relevant_ids: List[str],
        relevance_scores: List[int]
    ):


        return {


            "mrr":
                self.reciprocal_rank(
                    ranked_ids,
                    relevant_ids
                ),


            "ndcg":
                self.ndcg(
                    relevance_scores
                )

        }