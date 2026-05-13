"""SalesAgentObservabilityAdapter — concrete port impl for cross-module suggestions.

Read-only access over ``messages`` and ``enrollments`` tables.
§3 protected surfaces (Closer Studio, BufferService, OutputManager,
FollowUp, PromptVersionModel, agent_state_checkpoint) are NOT touched here.

[COPILOT-SUGGESTIONS-ENGINE] -> docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

from luana_core_platform.links.ports.sales_agent import (
    EnrollmentSummaryDTO,
    SalesAgentObservabilityPort,
)
from luana_core_sales_agent.infrastructure.models.enrollment_model import (
    EnrollmentModel,
)
from luana_core_sales_agent.infrastructure.models.message_model import MessageModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SalesAgentObservabilityAdapter(SalesAgentObservabilityPort):
    """Concrete adapter — read-only over enrollments + messages tables.

    Tenant isolation: every query filters ``tenant_id == X``.
    Best-effort: callers (providers) wrap in try/except and return ``[]`` on failure.
    """

    def __init__(self, db: Session) -> None:
        """Initialize with a DB session."""
        self._db = db

    def count_leads_since(self, tenant_id: UUID, since: datetime) -> int:
        """Distinct contacts (user_id) with at least one message since ``since``."""
        stmt = select(func.count(func.distinct(MessageModel.user_id))).where(
            MessageModel.tenant_id == tenant_id,
            MessageModel.created_at >= since,
        )
        result = self._db.execute(stmt).scalar_one()
        return int(result or 0)

    def count_active_conversations_since(self, tenant_id: UUID, since: datetime) -> int:
        """Distinct conversations approximated by distinct user_ids since ``since``.

        The ``conversations`` table is a sales_agent-internal concept (§3-protected).
        A richer notion of "conversation" can be added to this port later without
        breaking callers.
        """
        return self.count_leads_since(tenant_id, since)

    def list_enrollments_by_status(
        self,
        tenant_id: UUID,
        statuses: tuple[str, ...],
    ) -> list[EnrollmentSummaryDTO]:
        """Lightweight enrollments filtered by status values.

        Caps at 100 rows defensively — callers only need the count or first few.
        """
        if not statuses:
            return []
        stmt = (
            select(EnrollmentModel)
            .where(
                EnrollmentModel.tenant_id == tenant_id,
                EnrollmentModel.status.in_(statuses),
            )
            .order_by(EnrollmentModel.created_at.desc())
            .limit(100)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [
            EnrollmentSummaryDTO(
                id=str(r.id),
                offer_id=str(r.offer_id),
                status=str(r.status),
                created_at_iso=r.created_at.isoformat() if r.created_at else "",
                edition_id=str(r.edition_id) if r.edition_id else None,
            )
            for r in rows
        ]

    def has_active_edition_for_offer(self, tenant_id: UUID, offer_id: UUID) -> bool:
        """True if the offer has at least one active (non-cancelled, non-draft) edition."""
        from luana_core_platform.links.ports.offer import get_launch_edition_repository

        try:
            repo = get_launch_edition_repository(self._db)
            editions = repo.list_by_offer(offer_id, tenant_id=tenant_id)  # type: ignore[attr-defined]
            return any(getattr(e, "status", "") not in ("cancelled", "draft") for e in editions)
        except (AttributeError, TypeError):
            # If list_by_offer doesn't accept tenant_id kwarg, fall back gracefully
            try:
                repo2 = get_launch_edition_repository(self._db)
                editions2 = repo2.list_by_offer(offer_id)  # type: ignore[attr-defined]
                return any(
                    getattr(e, "status", "") not in ("cancelled", "draft")
                    and str(getattr(e, "tenant_id", "")) == str(tenant_id)
                    for e in editions2
                )
            except Exception:  # noqa: BLE001
                return False


__all__ = ["SalesAgentObservabilityAdapter"]
