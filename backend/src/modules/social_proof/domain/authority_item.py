"""AuthorityItem domain entity — credibility / authority proof."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luana_core_platform.domain.base_entity import BaseEntity
from pydantic import Field

if TYPE_CHECKING:
    from datetime import date, datetime
    from uuid import UUID

    from luana_core_social_proof.domain.enums import AuthorityType


class AuthorityItem(BaseEntity):
    """A credential, media mention, award or other trust signal.

    Tenant-scoped. Where it gets shown lives in ``social_proof_placements``.
    """

    id: UUID
    tenant_id: UUID
    user_id: UUID
    entity_name: str = Field(min_length=1, max_length=255)
    authority_type: AuthorityType
    context: str | None = None
    proof_url: str | None = None
    logo_url: str | None = None
    obtained_at: date | None = None
    expires_at: date | None = None

    is_active: bool = True
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
