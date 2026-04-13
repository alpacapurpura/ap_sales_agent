from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from src.shared.domain.datetime_utils import utc_now


class StateRepository:
    """
    Persistence gateway for agent state checkpoints.

    Provides upsert-style save (create-or-update) and soft-deactivation
    for session timeout scenarios.  All queries enforce tenant isolation.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_checkpoint(
        self,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> AgentStateCheckpointModel | None:
        """Return the most-recently-updated active checkpoint for a tenant + lead."""
        stmt = (
            select(AgentStateCheckpointModel)
            .where(
                AgentStateCheckpointModel.tenant_id == tenant_id,
                AgentStateCheckpointModel.lead_id == lead_id,
                AgentStateCheckpointModel.is_active.is_(True),
                AgentStateCheckpointModel.deleted_at.is_(None),
            )
            .order_by(AgentStateCheckpointModel.updated_at.desc())
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def save_checkpoint(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        **fields: Any,  # noqa: ANN401 — dynamic checkpoint fields
    ) -> AgentStateCheckpointModel:
        """Create or update the active checkpoint for a tenant + lead."""
        existing = self.get_active_checkpoint(tenant_id, lead_id)
        if existing:
            for key, value in fields.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = utc_now()
            self.db.flush()
            return existing

        checkpoint = AgentStateCheckpointModel(
            tenant_id=tenant_id,
            lead_id=lead_id,
            **fields,
        )
        self.db.add(checkpoint)
        self.db.flush()
        return checkpoint

    def deactivate(self, tenant_id: UUID, lead_id: UUID) -> None:
        """Soft-deactivate all active checkpoints for a tenant + lead (session timeout)."""
        stmt = (
            update(AgentStateCheckpointModel)
            .where(
                AgentStateCheckpointModel.tenant_id == tenant_id,
                AgentStateCheckpointModel.lead_id == lead_id,
                AgentStateCheckpointModel.is_active.is_(True),
            )
            .values(is_active=False, deleted_at=utc_now())
        )
        self.db.execute(stmt)
        self.db.flush()
