"""Segment DTOs — request/response shapes for segment API endpoints."""

from __future__ import annotations

import datetime as dt
from typing import Self
from uuid import UUID

from luana_core_campaigns.domain.enums import SegmentType
from luana_core_campaigns.domain.segment_filter import PredefinedSegmentFilter
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SegmentCreate(BaseModel):
    """POST /api/v1/segments/ request body.

    Supports two mutually-exclusive modes:
    - DYNAMIC: filter_dsl required, lead_ids must be None.
    - STATIC: lead_ids required (non-empty, max 10 000), filter_dsl must be None.

    The model_validator enforces the XOR invariant at parse time.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    segment_type: SegmentType = SegmentType.DYNAMIC
    filter_dsl: PredefinedSegmentFilter | None = Field(
        default=None,
        description="Required when segment_type=DYNAMIC. Must be None for STATIC.",
    )
    lead_ids: list[UUID] | None = Field(
        default=None,
        description="Required when segment_type=STATIC. Snapshot at creation. Max 10 000.",
        max_length=10_000,
    )

    @model_validator(mode="after")
    def _validate_dsl_xor_lead_ids(self) -> Self:
        """Enforce XOR: STATIC ↔ lead_ids, DYNAMIC ↔ filter_dsl."""
        if self.segment_type == SegmentType.STATIC:
            if not self.lead_ids:
                msg = "El segmento STATIC requiere lead_ids no vacíos."
                raise ValueError(msg)
            if self.filter_dsl is not None:
                msg = "El segmento STATIC no debe incluir filter_dsl."
                raise ValueError(msg)
        else:  # DYNAMIC
            if self.filter_dsl is None:
                msg = "El segmento DYNAMIC requiere filter_dsl."
                raise ValueError(msg)
            if self.lead_ids is not None:
                msg = "El segmento DYNAMIC no debe incluir lead_ids."
                raise ValueError(msg)
        return self


class SegmentUpdate(BaseModel):
    """PATCH /api/v1/segments/{id} request body."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    filter_dsl: PredefinedSegmentFilter | None = None


class SegmentResponse(BaseModel):
    """Full segment read shape. No PII intrinsically.

    filter_dsl is None for STATIC segments (lead_ids stored internally in JSONB).
    static_lead_ids is populated for STATIC segments.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    segment_type: SegmentType
    filter_dsl: PredefinedSegmentFilter | None
    static_lead_ids: list[UUID] | None = None
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
