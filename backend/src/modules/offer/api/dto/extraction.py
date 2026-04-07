from pydantic import BaseModel, ConfigDict


class ExtractFullOfferResponse(BaseModel):
    """Response DTO for full offer extraction job dispatch (202 Accepted)."""

    job_id: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class OfferExtractionStatusResponse(BaseModel):
    """Response DTO for polling offer extraction job status."""

    status: str
    progress: int | None = None
    stage: str | None = None
    started_at: str | None = None
    error: str | None = None
    model_config = ConfigDict(from_attributes=True, extra="allow")
