
from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field



class ProviderBase(BaseModel):

    name: str = Field(
        ...,
        description="Provider name"
    )


    type: str = Field(
        ...,
        description="cloud/local"
    )


    endpoint: Optional[str] = None


    default_model: Optional[str] = None



class ProviderCreate(ProviderBase):

    config: Optional[Dict[str, Any]] = None



class ProviderUpdate(BaseModel):

    name: Optional[str] = None

    endpoint: Optional[str] = None

    default_model: Optional[str] = None

    config: Optional[Dict[str, Any]] = None



class ProviderResponse(ProviderBase):

    id: int

    is_active: bool

    created_at: datetime


    class Config:
        from_attributes = True