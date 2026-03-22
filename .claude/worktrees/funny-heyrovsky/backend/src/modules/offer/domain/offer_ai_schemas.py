from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

class PsychologyGenerationRequest(BaseModel):
    avatar_id: UUID = Field(..., description="ID of the Avatar to analyze")
    offer_name: str = Field(..., description="Name of the offer/product")
    offer_description: Optional[str] = Field(None, description="Description or Promise of the offer")
    current_pains: List[str] = Field(default_factory=list, description="Current list of pain points drafted by user")
    current_desires: List[str] = Field(default_factory=list, description="Current list of desires drafted by user")

class PsychologyGenerationResponse(BaseModel):
    pains: List[str] = Field(..., description="List of 5 refined pain points")
    desires: List[str] = Field(..., description="List of 5 refined desires")
