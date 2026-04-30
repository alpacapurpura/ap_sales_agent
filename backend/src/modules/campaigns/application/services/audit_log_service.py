"""AuditLogService — sanitize and persist campaign audit rows.

Best-effort: NEVER raises. If DB write fails → log warning + swallow.
Pattern mirrors copilot observability callback handler.

PR-5 PI-1 S2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from src.modules.campaigns.domain.audit_log import AuditEventType, AuditLogEvent
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.domain.audit_log import AuditLogRepository

logger = structlog.get_logger(__name__)


class AuditLogService:
    """Sanitize + persist audit rows for campaign execution events.

    Every write is best-effort: callers MUST NOT rely on this raising.
    """

    def __init__(self, repo: AuditLogRepository) -> None:
        """Initialize with repository implementation."""
        self._repo = repo

    async def record(
        self,
        *,
        tenant_id: UUID,
        event_type: AuditEventType,
        actor: str,
        campaign_id: UUID | None = None,
        campaign_task_id: UUID | None = None,
        payload: dict | None = None,
        session: AsyncSession,
    ) -> None:
        """INSERT audit row. Sanitizes PII via sanitize_payload.

        NEVER raises: DB error → log warning + swallow.
        Caller is responsible for session.commit() (respects caller UoW).
        """
        try:
            from src.shared.agent_observability.recording.sanitization import sanitize_payload

            safe_payload = sanitize_payload(payload or {})
            evt = AuditLogEvent(
                id=uuid4(),
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                campaign_task_id=campaign_task_id,
                event_type=event_type,
                actor=actor,
                payload=safe_payload,
                created_at=utc_now(),
            )
            await self._repo.append(evt, session=session)
        except Exception:  # noqa: BLE001 — best-effort, never break caller
            logger.warning(
                "audit_log_write_failed",
                tenant_id=str(tenant_id),
                event_type=str(event_type),
                actor=actor,
                exc_info=True,
            )
