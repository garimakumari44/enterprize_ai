# app/processing/extraction_processor.py


from uuid import UUID


class ExtractionProcessor:
    """
    Responsible for extracting structured
    information from documents.
    """


    def __init__(
        self,
        ocr_engine,
        classifier,
        extractor,
    ):
        self.ocr_engine = ocr_engine
        self.classifier = classifier
        self.extractor = extractor



    async def process(
        self,
        document_id: UUID,
        template_type: str,
    ):


        # Step 1
        # OCR

        text = await self.ocr_engine.extract(
            document_id
        )


        # Step 2
        # Document classification

        document_type = await self.classifier.classify(
            text
        )


        # Step 3
        # Field extraction

        extracted_data = await self.extractor.extract(
            document_type=document_type,
            text=text
        )


        return {

            "document_id": document_id,

            "document_type": document_type,

            "fields": extracted_data,

            "status": "extracted"
        }