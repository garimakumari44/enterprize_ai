# app/processing/validation_processor.py


from uuid import UUID



class ValidationProcessor:


    def __init__(
        self,
        validator,
        rule_engine,
        confidence_engine,
    ):

        self.validator = validator
        self.rule_engine = rule_engine
        self.confidence_engine = confidence_engine



    async def validate(
        self,
        document_id: UUID,
        extraction_result: dict,
    ):


        fields = extraction_result["fields"]


        # Field validation

        field_errors = await (
            self.validator.validate(
                fields
            )
        )


        # Business rules

        rule_results = await (
            self.rule_engine.evaluate(
                fields
            )
        )


        # Confidence calculation

        confidence = await (
            self.confidence_engine.calculate(
                fields
            )
        )


        status = "approved"


        if field_errors:
            status = "failed"


        if confidence < 0.80:
            status = "review_required"



        return {


            "document_id": document_id,


            "status": status,


            "field_errors": field_errors,


            "rules": rule_results,


            "confidence": confidence

        }