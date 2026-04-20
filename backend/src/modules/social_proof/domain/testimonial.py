"""Testimonial domain entity — customer quote / review."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.modules.social_proof.domain.enums import TestimonialMediaType
from src.shared.domain.base_entity import BaseEntity


class Testimonial(BaseEntity):
    """A single customer testimonial that can be placed on any surface.

    Tenant-scoped. Where it gets shown lives in ``social_proof_placements``.
    """

    id: UUID
    tenant_id: UUID
    user_id: UUID
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

    is_active: bool = True
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
