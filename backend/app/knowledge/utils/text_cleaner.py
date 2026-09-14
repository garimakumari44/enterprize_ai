from __future__ import annotations

import re


class TextCleaner:
    """
    Text normalization utilities.
    """

    MULTI_SPACE = re.compile(r"\s+")

    @staticmethod
    def clean(text: str) -> str:
        """
        Normalize whitespace.
        """
        if not text:
            return ""

        text = text.strip()
        text = TextCleaner.MULTI_SPACE.sub(" ", text)

        return text

    @staticmethod
    def lowercase(text: str) -> str:
        return text.lower()

    @staticmethod
    def remove_extra_newlines(text: str) -> str:
        return re.sub(r"\n+", "\n", text)

    @staticmethod
    def normalize(text: str) -> str:
        text = TextCleaner.clean(text)
        text = TextCleaner.remove_extra_newlines(text)
        return text