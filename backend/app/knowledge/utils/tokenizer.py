from __future__ import annotations

import re
from typing import List


class Tokenizer:
    """
    Basic tokenizer utility.
    """

    WORD_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Split text into lowercase tokens.
        """
        if not text:
            return []

        return Tokenizer.WORD_PATTERN.findall(text.lower())

    @staticmethod
    def token_count(text: str) -> int:
        """
        Count words.
        """
        return len(Tokenizer.tokenize(text))

    @staticmethod
    def unique_tokens(text: str) -> List[str]:
        """
        Return unique sorted tokens.
        """
        return sorted(set(Tokenizer.tokenize(text)))