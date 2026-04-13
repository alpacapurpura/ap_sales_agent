"""Lifecycle Transition audit trail model.

Records every lifecycle_stage change with full context:
who triggered it, why, the score at the time, and any extra metadata.

triggered_by uses String (not PG enum) to avoid ALTER TYPE issues on new values.
"""

import uuid

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.modules.crm.domain.enums import LifecycleStage
from src.shared.domain.base_entity import Base


class LifecycleTransitionModel(Base):
    """SQLAlchemy model for lifecycle transition."""

    __tablename__ = "lifecycle_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    from_stage = Column(
        Enum(LifecycleStage, values_callable=lambda enum: [e.value for e in enum]),
        nullable=True,
    )  # null for initial assignment
    to_stage = Column(
        Enum(LifecycleStage, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )

    reason = Column(
        String,
        nullable=False,
    )  # Human-readable: "Score crossed MQL threshold (42.5 >= 40)"
    triggered_by = Column(
        String,
        nullable=False,
    )  # Values: scoring_rule, sale_event, churn_event, manual, decay, reactivation

    score_at_transition = Column(Float, nullable=True)

    transition_metadata = Column(
        "metadata",
        JSONB,
        default=dict,
    )  # Flexible context per trigger type
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
