"""CampaignTemplate DTOs — request/response shapes for template API endpoints.

PR-4: templates catalog (globals + tenant-scoped) + clone_to_campaign.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import CampaignType


class CampaignTemplateResponse(BaseModel):
    """Full template read shape. PII allowlist via response_model= enforcement."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID | None  # NULL = global Nicolify-provided
    slug: str
    name: str
    description: str
    campaign_type: CampaignType
    template_body: dict[str, Any]
    recommended_segment_slugs: list[str]
    tags: list[str]
    version: int
    created_at: dt.datetime
    updated_at: dt.datetime


class CampaignCreateFromTemplate(BaseModel):
    """POST /api/v1/templates/{id}/clone request body."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nombre de la nueva campaña instanciada.",
    )
    segment_id: UUID
    offer_id: UUID | None = None
    scheduled_for: dt.datetime | None = Field(
        default=None,
        description=("Si se provee, la campaña queda en SCHEDULED post-clone. Si es None, queda en DRAFT."),
    )
    description: str | None = Field(default=None, max_length=2000)
    config_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Merge sobre template_body.config_defaults.",
    )
