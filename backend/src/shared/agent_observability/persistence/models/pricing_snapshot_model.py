"""SQLAlchemy model for ``model_pricing_snapshot``.

Point-in-time pricing per (provider, model). The active snapshot has
``valid_to IS NULL``; closed snapshots carry the timestamp at which the
LiteLLM diff detected a change.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.shared.domain.base_entity import Base


class ModelPricingSnapshotModel(Base):
    """ORM mapping for ``model_pricing_snapshot``."""

    __tablename__ = "model_pricing_snapshot"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(32), nullable=False)
    model = Column(String(128), nullable=False)

    input_cost_per_token = Column(Numeric(14, 12), nullable=False)
    output_cost_per_token = Column(Numeric(14, 12), nullable=False)
    cache_read_cost_per_token = Column(Numeric(14, 12), nullable=True, default=0)
    cache_write_cost_per_token = Column(Numeric(14, 12), nullable=True, default=0)
    batch_input_cost_per_token = Column(Numeric(14, 12), nullable=True)

    source = Column(String(32), nullable=False)
    source_etag = Column(String(64), nullable=True)

    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)

    raw_payload = Column(JSONB, nullable=False, default=dict)

    def __repr__(self) -> str:
        """Return a debug-friendly summary of the snapshot."""
        active = "active" if self.valid_to is None else "closed"
        return f"<ModelPricingSnapshot {self.provider}/{self.model} {active} id={self.id}>"
