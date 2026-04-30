"""Campaign audit log domain value objects and repository interface.

Append-only audit trail for campaign execution events.
Retention 90d via worker (purge_old_campaigns_audit).

PR-5 PI-1 S2 orchestrator-and-workers.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class AuditEventType(StrEnum):
    """Canonical audit event types for campaign execution.

    Values in English per codebase pattern (copilot_trace_event parity).
    """

    CAMPAIGN_LAUNCHED = "campaign_launched"
    TASKS_GENERATED = "tasks_generated"
    TASK_DISPATCHED = "task_dispatched"
    TASK_SENT = "task_sent"
    TASK_FAILED = "task_failed"
    TASK_SKIPPED = "task_skipped"
    CIRCUIT_OPENED = "circuit_opened"
    CIRCUIT_CLOSED = "circuit_closed"
    COMPLIANCE_BLOCKED = "compliance_blocked"
    RATE_LIMITED = "rate_limited"


@dataclass(frozen=True, slots=True)
class AuditLogEvent:
    """Audit log value object. Append-only; never mutated after creation.

    PII contract: payload MUST be sanitized via sanitize_payload before
    constructing this VO. Repo impl enforces at write time.
    """

    id: UUID
    tenant_id: UUID
    campaign_id: UUID | None
    campaign_task_id: UUID | None
    event_type: AuditEventType
    actor: str  # "orchestrator" | "execution_worker" | "scheduler" | "api" | "system"
    payload: dict
    created_at: dt.datetime


class AuditLogRepository(ABC):
    """Abstract repository for campaign audit log. Append-only."""

    @abstractmethod
    async def append(self, evt: AuditLogEvent, *, session: AsyncSession) -> None:
        """Persist a new audit log entry. No updates, no deletes."""

    @abstractmethod
    async def list_by_campaign(
        self,
        campaign_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditLogEvent]:
        """List audit events for a specific campaign, scoped to tenant.

        Ordered created_at DESC. Uses ix_campaign_audit_tenant_campaign_created.
        """

    @abstractmethod
    async def purge_older_than(
        self,
        *,
        cutoff: dt.datetime,
        batch_size: int = 5_000,
        session: AsyncSession,
    ) -> int:
        """Hard delete audit rows older than cutoff. Cross-tenant by design.

        Cross-tenant allowlist: retention worker operates globally — same pattern
        as purge_expired_trace_rows (copilot observability). Documented in
        CROSS_TENANT_ALLOWED_METHODS of test_campaigns_tenant_isolation.py.

        Returns:
            Number of rows deleted in this batch. Caller loops until 0.
        """
