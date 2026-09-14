from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class PromptBase(BaseModel):

    name: str

    description: Optional[str] = None

    template: str = Field(
        ...,
        description="Prompt template text"
    )


    variables: Optional[list[str]] = []


class PromptCreate(PromptBase):
    pass



class PromptUpdate(BaseModel):

    name: Optional[str] = None

    description: Optional[str] = None

    template: Optional[str] = None

    variables: Optional[list[str]] = None



class PromptResponse(PromptBase):

    id: int

    version: int

    created_at: datetime

    updated_at: datetime


    class Config:
        from_attributes = True