"""
Repository for lifecycle transition audit records.

All queries enforce tenant_id filtering for multitenant isolation.
Uses SQLAlchemy 2.0 syntax (select(Model)).
"""
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import LifecycleStage
from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)


class LifecycleRepository:
    """CRUD for lifecycle_transitions table."""

    def __init__(self, db: Session):
        self.db = db

    def create_transition(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        from_stage: Optional[LifecycleStage],
        to_stage: LifecycleStage,
        reason: str,
        triggered_by: str,
        score_at_transition: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LifecycleTransitionModel:
        """Create a new lifecycle transition audit record."""
        transition = LifecycleTransitionModel(
            profile_id=profile_id,
            tenant_id=tenant_id,
            from_stage=from_stage,
            to_stage=to_stage,
            reason=reason,
            triggered_by=triggered_by,
            score_at_transition=score_at_transition,
            transition_metadata=metadata or {},
        )
        self.db.add(transition)
        self.db.flush()
        return transition

    def get_transitions_by_profile(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        limit: int = 50,
    ) -> List[LifecycleTransitionModel]:
        """Get lifecycle transitions for a profile, most recent first.

        Always filters by tenant_id for multitenant isolation.
        """
        stmt = (
            select(LifecycleTransitionModel)
            .where(
                LifecycleTransitionModel.profile_id == profile_id,
                LifecycleTransitionModel.tenant_id == tenant_id,
            )
            .order_by(LifecycleTransitionModel.occurred_at.desc())
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())
