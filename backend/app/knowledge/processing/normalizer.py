import re


class TextNormalizer:
    """
    Normalizes document content
    before knowledge indexing.
    """

    def __init__(self):
        pass


    def normalize(
        self,
        text: str
    ) -> str:


        text = self.lowercase(text)

        text = self.normalize_numbers(text)

        text = self.normalize_whitespace(text)

        return text.strip()



    def lowercase(
        self,
        text:str
    ) -> str:
        """
        Convert text to lowercase.
        """

        return text.lower()



    def normalize_whitespace(
        self,
        text:str
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            text
        )



    def normalize_numbers(
        self,
        text:str
    ) -> str:
        """
        Standardize numeric formats.
        
        Example:
        1,000 -> 1000
        """

        return re.sub(
            r"(\d),(\d)",
            r"\1\2",
            text
        )