"""SQLA implementation of AuditLogRepository.

Append-only. Tenant-scoped reads. Cross-tenant purge (allowlisted).
Uses sanitize_payload at write time to redact PII from JSONB payload.

PR-5 PI-1 S2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import delete, select

from src.modules.campaigns.domain.audit_log import AuditEventType, AuditLogEvent, AuditLogRepository
from src.modules.campaigns.infrastructure.models.campaign_audit_model import CampaignAuditModel
from src.shared.agent_observability.recording.sanitization import sanitize_payload

if TYPE_CHECKING:
    import datetime as dt
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


def _model_to_event(row: CampaignAuditModel) -> AuditLogEvent:
    """Map SQLA model to domain VO."""
    return AuditLogEvent(
        id=row.id,
        tenant_id=row.tenant_id,
        campaign_id=row.campaign_id,
        campaign_task_id=row.campaign_task_id,
        event_type=AuditEventType(row.event_type),
        actor=row.actor,
        payload=row.payload or {},
        created_at=row.created_at,
    )


class AuditLogRepositoryImpl(AuditLogRepository):
    """SQLAlchemy 2.0 async repository for campaign_audit table."""

    async def append(self, evt: AuditLogEvent, *, session: AsyncSession) -> None:
        """Persist audit log entry. Sanitizes payload before insert.

        Best-effort: caller wraps in try/except (AuditLogService contract).
        """
        safe_payload = sanitize_payload(evt.payload)
        row = CampaignAuditModel(
            id=evt.id,
            tenant_id=evt.tenant_id,
            campaign_id=evt.campaign_id,
            campaign_task_id=evt.campaign_task_id,
            event_type=str(evt.event_type),
            actor=evt.actor,
            payload=safe_payload,
            created_at=evt.created_at,
        )
        session.add(row)

    async def list_by_campaign(
        self,
        campaign_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditLogEvent]:
        """List audit events for a campaign, scoped to tenant. Ordered DESC."""
        stmt = (
            select(CampaignAuditModel)
            .where(
                CampaignAuditModel.tenant_id == tenant_id,
                CampaignAuditModel.campaign_id == campaign_id,
            )
            .order_by(CampaignAuditModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [_model_to_event(r) for r in rows]

    async def purge_older_than(
        self,
        *,
        cutoff: dt.datetime,
        batch_size: int = 5_000,
        session: AsyncSession,
    ) -> int:
        """Hard delete audit rows older than cutoff.

        Cross-tenant by design (retention worker scope).
        CROSS_TENANT_ALLOWED_METHODS allowlist: purge_older_than.
        Mirror pattern: purge_expired_trace_rows (copilot observability).

        Returns rows deleted in this batch.
        """
        # Subquery: pick batch by ix_campaign_audit_created (fast index scan)
        subq = select(CampaignAuditModel.id).where(CampaignAuditModel.created_at < cutoff).limit(batch_size)
        stmt = delete(CampaignAuditModel).where(CampaignAuditModel.id.in_(subq))
        result = await session.execute(stmt)
        deleted: int = result.rowcount or 0
        return deleted
