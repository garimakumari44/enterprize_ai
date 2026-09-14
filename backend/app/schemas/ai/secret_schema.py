from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field



class SecretCreate(BaseModel):

    name: str = Field(
        ...,
        description="Secret identifier"
    )


    provider: str


    secret_value: str = Field(
        ...,
        description="API key or credential"
    )



class SecretUpdate(BaseModel):

    secret_value: Optional[str] = None



class SecretResponse(BaseModel):

    id: int

    name: str

    provider: str


    masked_value: str


    created_at: datetime


    class Config:
        from_attributes = True