"""TeamMember domain entity — person that represents the brand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luana_core_platform.domain.base_entity import BaseEntity
from pydantic import Field

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class TeamMember(BaseEntity):
    """A human that represents the brand — leadership, instructor, advisor.

    Tenant-scoped. Where they appear lives in ``social_proof_placements``.
    """

    id: UUID
    tenant_id: UUID
    user_id: UUID
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

    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
