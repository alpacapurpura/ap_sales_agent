"""ChannelBlacklistEntry entity — compliance domain.

Identifier normalization is caller's responsibility (E.164 for phone,
lowercase for email).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChannelBlacklistEntry(BaseModel):
    """Per-channel blacklist entry for a tenant.

    Soft-deleted via deleted_at (hard delete prohibited per DDD rules).
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    tenant_id: UUID
    channel: str = Field(..., min_length=1, max_length=32)
    identifier: str = Field(..., min_length=1, max_length=255)
    reason: str | None = Field(default=None, max_length=255)
    created_by_user_id: UUID | None = None
    created_at: dt.datetime
    deleted_at: dt.datetime | None = None
