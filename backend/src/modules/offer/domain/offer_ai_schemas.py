from uuid import UUID

from pydantic import BaseModel, Field


class PsychologyGenerationRequest(BaseModel):
    avatar_id: UUID = Field(..., description="ID of the Avatar to analyze")
    offer_name: str = Field(..., description="Name of the offer/product")
    offer_description: str | None = Field(
        None, description="Description or Promise of the offer"
    )
    current_pains: list[str] = Field(
        default_factory=list, description="Current list of pain points drafted by user"
    )
    current_desires: list[str] = Field(
        default_factory=list, description="Current list of desires drafted by user"
    )


class PsychologyGenerationResponse(BaseModel):
    pains: list[str] = Field(..., description="List of 5 refined pain points")
    desires: list[str] = Field(..., description="List of 5 refined desires")
