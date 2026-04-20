"""Request / Response DTOs for the AuthorityItem API."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.social_proof.domain.enums import AuthorityType


class AuthorityCreateDTO(BaseModel):
    """POST body for AuthorityItem."""

    entity_name: str = Field(min_length=1, max_length=255)
    authority_type: AuthorityType
    context: str | None = None
    proof_url: str | None = None
    logo_url: str | None = None
    obtained_at: date | None = None
    expires_at: date | None = None


class AuthorityUpdateDTO(BaseModel):
    """PATCH body — all fields optional."""

    entity_name: str | None = Field(default=None, min_length=1, max_length=255)
    authority_type: AuthorityType | None = None
    context: str | None = None
    proof_url: str | None = None
    logo_url: str | None = None
    obtained_at: date | None = None
    expires_at: date | None = None
    is_active: bool | None = None


class AuthorityResponseDTO(BaseModel):
    """Full response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    entity_name: str
    authority_type: AuthorityType
    context: str | None
    proof_url: str | None
    logo_url: str | None
    obtained_at: date | None
    expires_at: date | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
