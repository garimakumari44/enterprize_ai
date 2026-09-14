import re
from typing import List


class TextCleaner:
    """
    Cleans raw extracted document text.

    Used after OCR/text extraction
    before chunking and embeddings.
    """

    def __init__(self):
        pass


    def clean(self, text: str) -> str:
        """
        Main cleaning pipeline.
        """

        text = self.remove_control_characters(text)

        text = self.remove_extra_spaces(text)

        text = self.remove_empty_lines(text)

        text = self.normalize_quotes(text)

        return text.strip()


    def remove_control_characters(
        self,
        text: str
    ) -> str:
        """
        Removes invisible characters.
        """

        return re.sub(
            r"[\x00-\x1f\x7f-\x9f]",
            "",
            text
        )


    def remove_extra_spaces(
        self,
        text: str
    ) -> str:
        """
        Collapse multiple spaces.
        """

        return re.sub(
            r"\s+",
            " ",
            text
        )


    def remove_empty_lines(
        self,
        text: str
    ) -> str:
        """
        Removes unnecessary blank lines.
        """

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        return "\n".join(lines)



    def normalize_quotes(
        self,
        text: str
    ) -> str:
        """
        Normalize different quote characters.
        """

        replacements = {
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'"
        }


        for old,new in replacements.items():
            text = text.replace(
                old,
                new
            )

        return text