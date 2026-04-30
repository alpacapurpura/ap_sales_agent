"""LeadOptIn entity — PM Q2 production-grade per-channel consent tracking.

Replaces implicit heuristic (messages.role='user') with explicit audit trail.
Enables GDPR/LGPD compliance.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

OptInSource = Literal["webhook", "manual", "imported", "inferred_message"]


class LeadOptIn(BaseModel):
    """Per-channel opt-in / opt-out audit trail with explicit timestamps.

    Source semantics:
    - webhook: explicit consent from channel webhook (Meta/IG/Telegram opt-in event).
    - manual: admin tagged via Streamlit / API.
    - imported: CSV upload bulk import.
    - inferred_message: backfill / one-shot heuristic from messages.role='user'.
      Lower trust, marked for audit.

    is_active_opt_in: opted_in_at NOT NULL AND opted_out_at IS NULL.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    tenant_id: UUID
    lead_id: UUID
    channel: str = Field(..., min_length=1, max_length=32)
    opted_in_at: dt.datetime | None = None
    opted_out_at: dt.datetime | None = None
    source: OptInSource
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: dt.datetime
    updated_at: dt.datetime

    @property
    def is_active_opt_in(self) -> bool:
        """Lead is opted-in iff opted_in_at NOT NULL AND opted_out_at IS NULL."""
        return self.opted_in_at is not None and self.opted_out_at is None
