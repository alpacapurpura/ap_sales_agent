"""Repository for ``sales_agent_routing_log``.

One row per supervisor decision per turn. Tenant-scoped reads. The
``node_sales_supervisor`` (``application/agents/sales/nodes.py``)
writes the row when it decides which specialist handles the turn.

Powers the S4 ``sales-routing`` admin page — currently just stores
data so when S4 lands the historical signal is already there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from luana_core_sales_agent.observability.persistence.models.routing_log_model import (
    SalesAgentRoutingLogModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class SalesAgentRoutingLogRepository:
    """Persist and query ``sales_agent_routing_log`` rows."""

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def add(self, **kwargs: Any) -> SalesAgentRoutingLogModel:  # noqa: ANN401 — column kwargs
        """Insert one row. Returns the persisted model."""
        row = SalesAgentRoutingLogModel(**kwargs)
        self.db.add(row)
        return row

    def find_by_turn(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
    ) -> list[SalesAgentRoutingLogModel]:
        """Return routing rows of ``turn_id`` for ``tenant_id``."""
        stmt = (
            select(SalesAgentRoutingLogModel)
            .where(
                SalesAgentRoutingLogModel.tenant_id == tenant_id,
                SalesAgentRoutingLogModel.turn_id == turn_id,
            )
            .order_by(SalesAgentRoutingLogModel.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
