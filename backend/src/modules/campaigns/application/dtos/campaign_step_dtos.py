"""CampaignStep DTOs — request/response shapes for step API endpoints."""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from luana_core_campaigns.domain.enums import StepType
from pydantic import BaseModel, ConfigDict, Field


class CampaignStepCreate(BaseModel):
    """POST /api/v1/campaigns/{id}/steps/ request body."""

    model_config = ConfigDict(extra="forbid")

    step_type: StepType
    step_index: int = Field(..., ge=0)
    label: str | None = Field(default=None, max_length=128)
    next_step_ids: list[UUID] = Field(default_factory=list)
    step_config: dict[str, Any] = Field(default_factory=dict)


class CampaignStepUpdate(BaseModel):
    """PATCH /api/v1/campaigns/{id}/steps/{step_id} request body."""

    model_config = ConfigDict(extra="forbid")

    step_index: int | None = Field(default=None, ge=0)
    label: str | None = Field(default=None, max_length=128)
    next_step_ids: list[UUID] | None = None
    step_config: dict[str, Any] | None = None


class CampaignStepResponse(BaseModel):
    """Full campaign step read shape."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    step_type: StepType
    step_index: int
    label: str | None
    next_step_ids: list[UUID]
    step_config: dict[str, Any]
    created_at: dt.datetime
    updated_at: dt.datetime
