"""Segment and SegmentSnapshot domain entities.

Segment: lazy-resolved or static audience of leads.
SegmentSnapshot: materialized list of lead IDs at a point in time.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import SegmentType
from src.modules.campaigns.domain.segment_filter import SegmentFilter


class Segment(BaseModel):
    """Lazy-resolved or static segment of leads. Filter persisted as JSONB.

    Resolution model (decided D3):
    - DYNAMIC default — service PR-4 SegmentService.resolve(at: datetime) -> set[lead_id]
      computes by querying CRM via shared/links/ports/crm.py at runtime.
    - STATIC — pinned to a SegmentSnapshot (audience locked at create time / launch time).

    Invariants:
    - tenant_id MANDATORY
    - name UNIQUE per tenant (partial unique idx WHERE deleted_at IS NULL)
    - filter_dsl validated by Pydantic SegmentFilter (model_config extra='forbid')
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    segment_type: SegmentType = SegmentType.DYNAMIC
    filter_dsl: SegmentFilter

    # Service PR-4 populates after resolve()
    estimated_size: int | None = Field(default=None, ge=0)
    last_calculated_at: dt.datetime | None = None

    # Master data
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None


class SegmentSnapshot(BaseModel):
    """Materialized list of lead IDs for a Segment at a point in time.

    Created by:
    - SegmentService.snapshot(segment_id) (PR-4) — explicit user action
    - CampaignOrchestrator.launch (S2) — auto-snapshot when campaign transitions to running
      and segment_type=STATIC (audience locking).

    Invariants:
    - tenant_id MANDATORY
    - lead_ids may be empty (zero-resolved segment is valid)
    - snapshotted_at UTC mandatory
    - No soft delete here — snapshots are immutable; if obsolete, hard-delete via retention worker (S2)
      EXCEPT we keep deleted_at for audit per backend-ddd.md soft-delete invariant.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    segment_id: UUID
    snapshotted_at: dt.datetime
    lead_ids: list[UUID]
    lead_count: int = Field(..., ge=0)

    # Master data
    created_at: dt.datetime
    deleted_at: dt.datetime | None = None  # soft delete invariant respected
