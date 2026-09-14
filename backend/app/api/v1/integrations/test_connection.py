from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(
    prefix="/connections",
    tags=["Connection Testing"]
)



class ConnectionTestRequest(BaseModel):

    provider:str
    credentials:dict



@router.post("/test")
async def test_connection(
    request:ConnectionTestRequest
):


    provider=request.provider


    # Later:
    # call actual clients
    #
    # OpenAIClient()
    # SlackClient()
    # S3Client()


    supported=[
        "openai",
        "anthropic",
        "slack",
        "postgres",
        "s3"
    ]


    if provider not in supported:

        return {

            "success":False,
            "message":"Unsupported provider"
        }



    return {

        "success":True,
        "provider":provider,
        "message":"Connection successful"
    }