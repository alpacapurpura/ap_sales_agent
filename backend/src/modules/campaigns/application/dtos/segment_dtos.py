"""Segment DTOs — request/response shapes for segment API endpoints."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import SegmentType
from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter


class SegmentCreate(BaseModel):
    """POST /api/v1/segments/ request body."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    segment_type: SegmentType = SegmentType.DYNAMIC
    filter_dsl: PredefinedSegmentFilter


class SegmentUpdate(BaseModel):
    """PATCH /api/v1/segments/{id} request body."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    filter_dsl: PredefinedSegmentFilter | None = None


class SegmentResponse(BaseModel):
    """Full segment read shape. No PII intrinsically."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    segment_type: SegmentType
    filter_dsl: PredefinedSegmentFilter
    estimated_size: int | None
    last_calculated_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime


class SegmentResolveRequest(BaseModel):
    """POST /api/v1/segments/{id}/resolve body."""

    model_config = ConfigDict(extra="forbid")

    at: dt.datetime | None = Field(default=None, description="Punto en tiempo UTC. Default = now.")
    limit: int = Field(default=10_000, ge=1, le=100_000, description="Cap returned lead_ids; 100K hard cap.")


class SegmentResolveResponse(BaseModel):
    """Returned UUIDs (NO PII). emails/phones never returned here."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    segment_id: UUID
    at: dt.datetime
    lead_count: int
    lead_ids: list[UUID]
    truncated: bool = False


class SegmentSnapshotResponse(BaseModel):
    """Segment snapshot response. lead_ids omitted (potentially huge)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    segment_id: UUID
    snapshotted_at: dt.datetime
    lead_count: int
    # lead_ids deliberately omitted from response (potentially huge)


class SegmentEstimateSizeResponse(BaseModel):
    """GET /api/v1/segments/{id}/estimate-size — quick count via cached query."""

    model_config = ConfigDict(extra="forbid")

    segment_id: UUID
    estimated_size: int
    cached_at: dt.datetime
    cache_hit: bool
