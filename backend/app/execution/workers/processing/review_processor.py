# app/processing/review_processor.py


from uuid import UUID



class ReviewProcessor:


    def __init__(
        self,
        review_service,
    ):

        self.review_service = review_service



    async def process(
        self,
        document_id: UUID,
        validation_result: dict,
    ):


        status = validation_result["status"]


        if status == "review_required":


            review = await (
                self.review_service
                .create_review_task(
                    document_id=document_id,
                    reason="Low confidence extraction"
                )
            )


            return {


                "status": "pending_review",

                "review_id": review.id

            }



        return {


            "status": "auto_completed",

            "review_id": None

        }