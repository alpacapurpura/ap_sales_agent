"""CampaignTemplate domain entity.

Reusable campaign blueprint. Globals (tenant_id NULL) + per-tenant.
PR-3: schema only, table empty. PR-4 seeds 5 globals via service layer.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from luana_core_campaigns.domain.enums import CampaignType
from pydantic import BaseModel, ConfigDict, Field


class CampaignTemplate(BaseModel):
    """Reusable campaign blueprint. Globals (tenant_id NULL) + per-tenant.

    PR-3: schema only, table empty. PR-4 seeds 5 globals (welcome, launch-4day,
    webinar, cold-reactivation, post-purchase) via service layer.

    Invariants:
    - slug MANDATORY (natural key)
    - UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL — supports both tenant-scoped
      and global (NULL tenant_id) via partial unique idx. NULL distinct semantics
      handled at SQL level: idx WHERE tenant_id IS NOT NULL AND deleted_at IS NULL
      + idx WHERE tenant_id IS NULL AND deleted_at IS NULL (two partial unique idx).
    - template_body JSONB validated per template_type by service PR-4
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID | None = None  # NULL = global Nicolify-provided
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(..., min_length=1, max_length=2000)
    campaign_type: CampaignType
    template_body: dict[str, Any] = Field(default_factory=dict)  # populated by PR-4
    recommended_segment_slugs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)

    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None
