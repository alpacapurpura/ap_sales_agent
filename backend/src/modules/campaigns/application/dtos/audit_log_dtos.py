"""Pydantic v2 DTOs for campaign audit log.

PII allowlist: payload is sanitized at write time (AuditLogService).
Response DTO exposes pre-sanitized payload only.

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from luana_core_campaigns.domain.audit_log import AuditEventType
from pydantic import BaseModel, ConfigDict, Field


class AuditLogEntryDTO(BaseModel):
    """Read shape for campaign audit log entries.

    PII allowlist: payload contains no raw PII (sanitized at write time).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID | None
    campaign_task_id: UUID | None
    event_type: AuditEventType
    actor: str = Field(..., max_length=50)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: dt.datetime
