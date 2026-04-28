"""Repository for ``sales_agent_trace_event``.

Tenant-scoped writes + reads. Lead-scoped reads drive the admin
``sales_audit.py`` dual-read window. Callable signature matches
:class:`~src.shared.agent_observability.persistence.base_trace_event_repo.BaseTraceEventRepoProtocol`
plus the two sales-agent-specific kwargs (``lead_id``, ``channel_type``)
declared on the abstract base via ``**agent_specific``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid4

import structlog
from sqlalchemy import select

from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
    SalesAgentTraceEventModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class SalesAgentTraceEventRepository:
    """Persist and query ``sales_agent_trace_event`` rows."""

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def add(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        span_id: UUID,
        event_type: str,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        status: str = "ok",
        parent_span_id: UUID | None = None,
        # sales-agent specific (declared on the abstract base via **agent_specific):
        lead_id: UUID,
        channel_type: str,
    ) -> SalesAgentTraceEventModel:
        """Insert one trace-event row. Returns the persisted model."""
        row = SalesAgentTraceEventModel(
            id=uuid4(),
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type=channel_type,
            turn_id=turn_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            event_type=event_type,
            name=name,
            data=data or {},
            duration_ms=duration_ms,
            status=status,
        )
        self.db.add(row)
        return row

    def list_by_turn(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
    ) -> list[SalesAgentTraceEventModel]:
        """Return every trace event of ``turn_id`` for ``tenant_id``."""
        stmt = (
            select(SalesAgentTraceEventModel)
            .where(
                SalesAgentTraceEventModel.tenant_id == tenant_id,
                SalesAgentTraceEventModel.turn_id == turn_id,
            )
            .order_by(SalesAgentTraceEventModel.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_lead(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        limit: int = 200,
    ) -> list[SalesAgentTraceEventModel]:
        """Return events for a lead, newest first.

        Drives admin dual-read window. ``limit`` capped at caller's request
        — sales_audit.py uses 200 to match legacy timeline depth.
        """
        stmt = (
            select(SalesAgentTraceEventModel)
            .where(
                SalesAgentTraceEventModel.tenant_id == tenant_id,
                SalesAgentTraceEventModel.lead_id == lead_id,
            )
            .order_by(SalesAgentTraceEventModel.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def find_last_turn_end(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> SalesAgentTraceEventModel | None:
        """Return the most recent ``turn_end`` row for a lead.

        Powers the admin sidebar "Ver Último Estado" — replaces the
        legacy ``AgentTrace.output_state`` last-row query.
        """
        stmt = (
            select(SalesAgentTraceEventModel)
            .where(
                SalesAgentTraceEventModel.tenant_id == tenant_id,
                SalesAgentTraceEventModel.lead_id == lead_id,
                SalesAgentTraceEventModel.event_type == "turn_end",
            )
            .order_by(SalesAgentTraceEventModel.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()
