from dataclasses import dataclass
from datetime import datetime


from .text_cleaner import TextCleaner
from .normalizer import TextNormalizer



@dataclass
class ProcessedDocument:

    content:str

    characters:int

    words:int

    processed_at:str



class DocumentPreprocessor:
    """
    Enterprise document preprocessing pipeline.
    """


    def __init__(self):

        self.cleaner = TextCleaner()

        self.normalizer = TextNormalizer()



    def process(
        self,
        text:str
    ) -> ProcessedDocument:
        """
        Execute preprocessing pipeline.
        """


        cleaned_text = (
            self.cleaner
            .clean(text)
        )


        normalized_text = (
            self.normalizer
            .normalize(
                cleaned_text
            )
        )


        return ProcessedDocument(

            content=normalized_text,

            characters=len(
                normalized_text
            ),

            words=len(
                normalized_text.split()
            ),

            processed_at=
                datetime.utcnow()
                .isoformat()

        )