"""CloserStudioService — back-compat facade post-S11B split.

The legacy 8-method god class was split along Query / Command / Kpi axes
(:class:`ConversationQueryService`, :class:`ConversationCommandService`,
:class:`KpiService`). This facade exists so the FastAPI router and the
existing test suite keep working unchanged. **New code should depend on
the dedicated service** instead of this facade.

# [SALES-AGENT-CLOSER-STUDIO-SPLIT-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.sales_agent.application.services.closer_studio import (
    ConversationCommandService,
    ConversationQueryService,
    KpiService,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session


class CloserStudioService:
    """Thin facade composing the three Closer Studio services.

    Each method delegates to the matching service. Constructor builds all
    three so a single instance covers list/detail/stop/resume/send/
    reactivate/diagnose/kpis without leaking the split to callers.
    """

    def __init__(self, db: Session) -> None:
        """Compose the three Closer Studio services on a single session."""
        self.db = db
        self._query = ConversationQueryService(db)
        self._command = ConversationCommandService(db)
        self._kpi = KpiService(db)

    # ── Query side ──────────────────────────────────────────────────────

    def list_conversations(
        self,
        tenant_id: UUID,
        *,
        temperature: str | None = None,
        handler_mode: str | None = None,
        channel: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Delegate to :class:`ConversationQueryService` (S11B)."""
        return self._query.list_conversations(
            tenant_id,
            temperature=temperature,
            handler_mode=handler_mode,
            channel=channel,
            search=search,
            limit=limit,
            offset=offset,
        )

    def get_conversation_detail(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        *,
        message_limit: int = 50,
        before: datetime | None = None,
    ) -> dict | None:
        """Delegate to :class:`ConversationQueryService` (S11B)."""
        return self._query.get_conversation_detail(
            tenant_id,
            lead_id,
            message_limit=message_limit,
            before=before,
        )

    def list_frozen(self, tenant_id: UUID) -> list[dict]:
        """Delegate to :class:`ConversationQueryService` (S11B)."""
        return self._query.list_frozen(tenant_id)

    # ── Command side ────────────────────────────────────────────────────

    def stop_ai(self, tenant_id: UUID, lead_id: UUID, user_id: UUID) -> dict | None:
        """Delegate to :class:`ConversationCommandService` (S11B)."""
        return self._command.stop_ai(tenant_id, lead_id, user_id)

    def resume_ai(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        objective: str | None = None,
    ) -> dict | None:
        """Delegate to :class:`ConversationCommandService` (S11B)."""
        return self._command.resume_ai(tenant_id, lead_id, objective=objective)

    def send_message(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        content: str,
        mode: str = "direct",
    ) -> dict | None:
        """Delegate to :class:`ConversationCommandService` (S11B)."""
        return self._command.send_message(tenant_id, lead_id, content, mode=mode)

    def reactivate(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        objective: str | None = None,
    ) -> dict | None:
        """Delegate to :class:`ConversationCommandService` (S11B)."""
        return self._command.reactivate(tenant_id, lead_id, objective=objective)

    async def diagnose(self, tenant_id: UUID, lead_id: UUID) -> dict | None:
        """Delegate to :class:`ConversationCommandService` (S11B)."""
        return await self._command.diagnose(tenant_id, lead_id)

    # ── KPI side ────────────────────────────────────────────────────────

    def get_kpis(self, tenant_id: UUID) -> dict:
        """Delegate to :class:`KpiService` (S11B)."""
        return self._kpi.get_kpis(tenant_id)


__all__ = ["CloserStudioService"]
