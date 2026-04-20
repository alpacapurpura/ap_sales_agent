"""Request / Response DTOs for the TeamMember API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamMemberCreateDTO(BaseModel):
    """POST body for TeamMember."""

    name: str = Field(min_length=1, max_length=255)
    role: str | None = Field(default=None, max_length=255)
    bio: str | None = None
    headshot_url: str | None = None
    is_primary_voice: bool = False
    gender: str | None = Field(default=None, max_length=20)
    communication_style: str | None = Field(default=None, max_length=40)
    personal_website: str | None = None
    personal_linkedin: str | None = None
    personal_instagram: str | None = None
    personal_tiktok: str | None = None
    personal_facebook: str | None = None
    work_whatsapp: str | None = Field(default=None, max_length=40)
    gallery: list[str] = Field(default_factory=list)
    sort_order: int = 0


class TeamMemberUpdateDTO(BaseModel):
    """PATCH body — all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    role: str | None = Field(default=None, max_length=255)
    bio: str | None = None
    headshot_url: str | None = None
    is_primary_voice: bool | None = None
    gender: str | None = Field(default=None, max_length=20)
    communication_style: str | None = Field(default=None, max_length=40)
    personal_website: str | None = None
    personal_linkedin: str | None = None
    personal_instagram: str | None = None
    personal_tiktok: str | None = None
    personal_facebook: str | None = None
    # PII: work_whatsapp is user-provided contact info for tenant-facing team
    # pages. Only returned to authenticated tenant members.
    work_whatsapp: str | None = Field(default=None, max_length=40)
    gallery: list[str] | None = None
    sort_order: int | None = None


class TeamMemberResponseDTO(BaseModel):
    """Full response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    role: str | None
    bio: str | None
    headshot_url: str | None
    is_primary_voice: bool
    gender: str | None
    communication_style: str | None
    personal_website: str | None
    personal_linkedin: str | None
    personal_instagram: str | None
    personal_tiktok: str | None
    personal_facebook: str | None
    work_whatsapp: str | None
    gallery: list[str]
    sort_order: int
    created_at: datetime | None
    updated_at: datetime | None
