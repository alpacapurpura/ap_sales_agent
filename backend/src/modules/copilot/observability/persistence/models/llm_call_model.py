"""SQLAlchemy model for ``copilot_llm_call``.

Each row represents one LLM invocation captured by
:class:`observability.recording.callback_handler.ObservabilityCallbackHandler`.
Pricing is denormalised at write time (snapshot) so historical cost
reconstruction stays stable even if the upstream LiteLLM JSON changes.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CHAR, Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from src.shared.domain.base_entity import Base


class CopilotLlmCallModel(Base):
    """ORM mapping for ``copilot_llm_call``.

    Generated columns (``occurred_on``, ``occurred_year_month``) live in
    Postgres only — see migration 075 — and are read via raw SQL in
    Phase 3 reporting / MV refresh.
    """

    __tablename__ = "copilot_llm_call"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
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
    # T-1 (PI-12 S1, X2): cost_usd is NULL when LiteLLM didn't provide a
    # response_cost (unknown model, non-LiteLLM call, cache miss past TTL).
    # Callers MUST distinguish NULL ("unknown") from Decimal("0") ("valid 0").
    cost_usd = Column(Numeric(16, 10), nullable=True)

    tenant_currency = Column(CHAR(3), nullable=True)
    fx_rate_to_tenant = Column(Numeric(16, 8), nullable=True)
    fx_rate_source = Column(String(32), nullable=True)
    cost_tenant_currency = Column(Numeric(16, 8), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    status = Column(String(16), nullable=False, default="ok")
    error_type = Column(String(64), nullable=True)

    def __repr__(self) -> str:
        """Return a debug-friendly summary of the call."""
        return (
            f"<CopilotLlmCall id={self.id} provider={self.provider} model={self.model_responded} status={self.status}>"
        )
