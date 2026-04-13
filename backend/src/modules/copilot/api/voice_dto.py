"""DTOs for the voice transcription API."""

from pydantic import BaseModel, ConfigDict


class TranscriptionResponse(BaseModel):
    """Response model for the transcription endpoint."""

    model_config = ConfigDict(from_attributes=True)

    text: str
    language: str
    duration_seconds: float
