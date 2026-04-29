"""KpiService — Closer Studio KPI aggregation (S11B step 5).

Single read endpoint. Lives in its own service so future KPI variants
(per-channel, per-funnel-stage, per-period) can land here without
touching the conversation services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import case, func, select

from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from src.shared.infrastructure.models.crm import LeadModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class KpiService:
    """Aggregate Closer Studio KPIs."""

    def __init__(self, db: Session) -> None:
        """Bind the service to a SQLAlchemy session."""
        self.db = db

    def get_kpis(self, tenant_id: UUID) -> dict:
        """Return active conversations + AI/human/frozen counts + temperature mix."""
        base = select(
            func.count().label("total"),
            func.sum(
                case((AgentStateCheckpointModel.handler_mode == "ai", 1), else_=0),
            ).label("ai"),
            func.sum(
                case((AgentStateCheckpointModel.handler_mode == "human", 1), else_=0),
            ).label("human"),
            func.sum(
                case((AgentStateCheckpointModel.frozen_at.isnot(None), 1), else_=0),
            ).label("frozen"),
            func.avg(AgentStateCheckpointModel.lead_score).label("avg_score"),
            func.sum(AgentStateCheckpointModel.unread_count).label("unread"),
        ).where(
            AgentStateCheckpointModel.tenant_id == tenant_id,
            AgentStateCheckpointModel.is_active.is_(True),
            AgentStateCheckpointModel.deleted_at.is_(None),
        )
        row = self.db.execute(base).one()

        temp_counts = self.db.execute(
            select(
                func.lower(LeadModel.temperature).label("temp"),
                func.count().label("cnt"),
            )
            .where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.is_blacklisted.is_(False),
            )
            .group_by(func.lower(LeadModel.temperature)),
        ).all()
        temp_map = {t.temp: t.cnt for t in temp_counts if t.temp}

        return {
            "total_active": row.total or 0,
            "handled_by_ai": row.ai or 0,
            "handled_by_human": row.human or 0,
            "frozen_count": row.frozen or 0,
            "hot_count": temp_map.get("hot", 0),
            "warm_count": temp_map.get("warm", 0),
            "cold_count": temp_map.get("cold", 0),
            "avg_lead_score": round(float(row.avg_score or 0), 1),
            "unread_total": row.unread or 0,
        }


__all__ = ["KpiService"]
