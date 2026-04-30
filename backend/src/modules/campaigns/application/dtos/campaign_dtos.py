"""Campaign DTOs — request/response shapes for API endpoints.

All DTOs use Pydantic v2. response_model= enforcement per pii-sanitisation.md.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import CampaignStatus, CampaignType


class CampaignCreate(BaseModel):
    """POST /api/v1/campaigns/ request body."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    campaign_type: CampaignType
    segment_id: UUID | None = None
    channel_priority: list[str] = Field(default_factory=list, max_length=10)
    offer_id: UUID | None = None
    brand_summary_id: UUID | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    created_by_source: Literal["api", "copilot", "manual", "scheduler"] = "api"


class CampaignUpdate(BaseModel):
    """PATCH /api/v1/campaigns/{id} request body. Only DRAFT campaigns updatable."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    segment_id: UUID | None = None
    channel_priority: list[str] | None = Field(default=None, max_length=10)
    offer_id: UUID | None = None
    brand_summary_id: UUID | None = None
    config: dict[str, Any] | None = None


class CampaignScheduleRequest(BaseModel):
    """POST /api/v1/campaigns/{id}/schedule body."""

    model_config = ConfigDict(extra="forbid")

    scheduled_for: dt.datetime  # UTC; service validates timezone-aware


class CampaignCancelRequest(BaseModel):
    """POST /api/v1/campaigns/{id}/cancel body (optional reason)."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=500)


class CampaignResponse(BaseModel):
    """Full campaign read shape. PII allowlist via response_model= enforcement."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    campaign_type: CampaignType
    status: CampaignStatus
    segment_id: UUID | None
    segment_snapshot_id: UUID | None
    channel_priority: list[str]
    offer_id: UUID | None
    brand_summary_id: UUID | None
    config: dict[str, Any]
    scheduled_at: dt.datetime | None
    launched_at: dt.datetime | None
    completed_at: dt.datetime | None
    created_by_user_id: UUID | None
    created_by_source: str
    created_at: dt.datetime
    updated_at: dt.datetime


class CampaignLaunchResponse(BaseModel):
    """Launch response — PR-5 real orchestrator."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    campaign: CampaignResponse
    tasks_generated: int = Field(default=0, ge=0, description="Cantidad de CampaignTask creadas para roots del DAG.")
    notice: str = Field(
        default=(
            "Lanzamiento ejecutado. Tasks raíz creadas y dispatch en cola via "
            "ChannelRouterRegistry. Audit log: GET /campaigns/{id}/audit (futuro post-PI-1)."
        ),
        description="Aviso al integrador sobre el resultado del lanzamiento.",
    )


CampaignStatusFilter = Annotated[
    list[CampaignStatus] | None,
    Field(default=None, description="Filtra por status. Multi-select."),
]
CampaignTypeFilter = Annotated[
    list[CampaignType] | None,
    Field(default=None, description="Filtra por type. Multi-select."),
]
CampaignSortBy = Literal[
    "created_at_desc",
    "created_at_asc",
    "scheduled_at_desc",
    "scheduled_at_asc",
    "name_asc",
]
