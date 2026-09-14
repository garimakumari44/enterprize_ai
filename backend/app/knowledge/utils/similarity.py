from __future__ import annotations

from math import sqrt
from typing import List


class Similarity:
    """
    Similarity helper methods.
    """

    @staticmethod
    def cosine_similarity(
        vector1: List[float],
        vector2: List[float],
    ) -> float:

        if len(vector1) != len(vector2):
            raise ValueError("Vector dimensions do not match.")

        dot = sum(a * b for a, b in zip(vector1, vector2))

        norm1 = sqrt(sum(x * x for x in vector1))
        norm2 = sqrt(sum(x * x for x in vector2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    @staticmethod
    def euclidean_distance(
        vector1: List[float],
        vector2: List[float],
    ) -> float:

        if len(vector1) != len(vector2):
            raise ValueError("Vector dimensions do not match.")

        return sqrt(
            sum(
                (a - b) ** 2
                for a, b in zip(vector1, vector2)
            )
        )