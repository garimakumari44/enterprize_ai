from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field



class EmbeddingRequest(BaseModel):

    provider: str = "openai"


    model: str = Field(
        ...,
        description="Embedding model"
    )


    texts: List[str]


    metadata: Optional[Dict[str, Any]] = None



class EmbeddingVector(BaseModel):

    index: int

    embedding: List[float]



class EmbeddingResponse(BaseModel):

    model: str

    vectors: List[EmbeddingVector]

    dimensions: int

    usage: Optional[Dict[str, int]] = None