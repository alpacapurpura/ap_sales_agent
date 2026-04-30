"""SQLAlchemy model for ``campaign_llm_call``.

Mirror structural of
:class:`~src.modules.sales_agent.observability.persistence.models.llm_call_model.SalesAgentLlmCallModel`
with identical schema — only the table name changes.

PR-1: placeholder model so ``register_agent_observability`` can reference
the class. No writes until S2 wires up ``CampaignCallbackHandler``.

Generated columns (``occurred_on``, ``occurred_year_month``) live in
Postgres only — see migration 083 — and are read via raw SQL in
S2 reporting / MV refresh.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CHAR, Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from src.shared.domain.base_entity import Base


class CampaignLlmCallModel(Base):
    """ORM mapping for ``campaign_llm_call``.

    Schema mirrors ``sales_agent_llm_call`` exactly — same columns,
    same types. lead_id references the CRM lead driving the campaign task.
    """

    __tablename__ = "campaign_llm_call"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    lead_id = Column(UUID(as_uuid=True), nullable=False)
    channel_type = Column(String(32), nullable=False)
    turn_id = Column(UUID(as_uuid=True), nullable=False)
    span_id = Column(UUID(as_uuid=True), nullable=False)
    parent_span_id = Column(UUID(as_uuid=True), nullable=True)

    role = Column(String(32), nullable=False)
    provider = Column(String(32), nullable=False)
    model_requested = Column(String(128), nullable=False)
    model_responded = Column(String(128), nullable=False)

    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cached_read_tokens = Column(Integer, nullable=False, default=0)
    cached_write_tokens = Column(Integer, nullable=False, default=0)
    reasoning_tokens = Column(Integer, nullable=False, default=0)

    pricing_version_id = Column(UUID(as_uuid=True), nullable=False)
    input_unit_cost_usd = Column(Numeric(14, 12), nullable=False)
    output_unit_cost_usd = Column(Numeric(14, 12), nullable=False)
    cached_read_unit_cost_usd = Column(Numeric(14, 12), nullable=False, default=0)
    cost_usd = Column(Numeric(16, 10), nullable=False)

    tenant_currency = Column(CHAR(3), nullable=True)
    fx_rate_to_tenant = Column(Numeric(16, 8), nullable=True)
    fx_rate_source = Column(String(32), nullable=True)
    cost_tenant_currency = Column(Numeric(16, 8), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    status = Column(String(16), nullable=False, default="ok")
    error_type = Column(String(64), nullable=True)

    def __repr__(self) -> str:
        """Return a debug-friendly summary of the LLM call."""
        return (
            f"<CampaignLlmCall id={self.id} provider={self.provider} "
            f"model={self.model_responded} lead_id={self.lead_id} status={self.status}>"
        )
