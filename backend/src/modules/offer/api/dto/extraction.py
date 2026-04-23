"""Extraction DTOs."""

from pydantic import BaseModel, ConfigDict, Field


class ExtractFullOfferResponse(BaseModel):
    """Response DTO for full offer extraction job dispatch (202 Accepted)."""

    job_id: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class OfferExtractionStatusResponse(BaseModel):
    """Response DTO for polling offer extraction job status.

    Enriched per FLOW-SPEC §3.3 — new fields are optional so existing
    callers that don't send them (old workers) keep working.
    """

    status: str
    progress: int | None = None
    stage: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    # Enriched fields (Phase 1 BE — FLOW-SPEC §3.3)
    filled_fields: list[str] = Field(default_factory=list)
    filled_fields_by_section: dict[str, list[str]] = Field(default_factory=dict)
    sections_touched: list[str] = Field(default_factory=list)
    sections_completed: list[str] = Field(default_factory=list)
    newly_completed_section: str | None = None

    model_config = ConfigDict(from_attributes=True, extra="allow")
