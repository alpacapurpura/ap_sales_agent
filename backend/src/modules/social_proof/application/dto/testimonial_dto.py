"""Request / Response DTOs for the Testimonial API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from luana_core_social_proof.domain.enums import TestimonialMediaType
from pydantic import BaseModel, ConfigDict, Field


class TestimonialCreateDTO(BaseModel):
    """POST body — minimal shell; the rest is filled later via PATCH."""

    author_name: str = Field(min_length=1, max_length=255)
    author_role: str | None = Field(default=None, max_length=255)
    author_avatar_url: str | None = None
    content: str | None = None
    media_type: TestimonialMediaType = TestimonialMediaType.TEXT
    media_url: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    source_url: str | None = None
    captured_at: datetime | None = None
    language: str = Field(default="es", min_length=2, max_length=8)
    tags: list[str] = Field(default_factory=list)


class TestimonialUpdateDTO(BaseModel):
    """PATCH body — every field optional; only provided ones are written."""

    author_name: str | None = Field(default=None, min_length=1, max_length=255)
    author_role: str | None = Field(default=None, max_length=255)
    author_avatar_url: str | None = None
    content: str | None = None
    media_type: TestimonialMediaType | None = None
    media_url: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    source_url: str | None = None
    captured_at: datetime | None = None
    language: str | None = Field(default=None, min_length=2, max_length=8)
    tags: list[str] | None = None
    is_active: bool | None = None


class TestimonialResponseDTO(BaseModel):
    """Full response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    author_name: str
    # PII fields below are required by the UI for author attribution; they are
    # tenant-scoped and only returned to authenticated members of the tenant.
    author_role: str | None
    author_avatar_url: str | None
    content: str | None
    media_type: TestimonialMediaType
    media_url: str | None
    rating: int | None
    source_url: str | None
    captured_at: datetime | None
    language: str
    tags: list[str]
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
