"""SQLAlchemy model for ``eval_simulator_llm_call``.

Mirror of :class:`~src.modules.campaigns.observability.persistence.models.llm_call_model.CampaignLlmCallModel`
with the following differences vs campaigns:

* ``lead_id``        — NULL (eval simulator does not track per-lead audit rows)
* ``eval_metadata``  — JSONB NOT NULL (mandatory H5 tags per 03-arch-be.md §1)
* ``cost_usd``       — NULL allowed (paridad migration 086_llm_call_cost_usd_nullable)
* ``channel_type``   — DEFAULT 'eval_simulator'

Generated columns (``occurred_on``, ``occurred_year_month``) live in Postgres only —
see migration 125 — and are read via raw SQL in reporting / MV refresh.

Origin: PI-12 Story B eval-foundation-simulator-homologation (2026-05-07).
R5 schema-mirror exception (.claude/rules/backend-ddd.md): builder-backend MAY touch
persistence/models/ for schema mirror from migration. Schema paridad campaigns/083.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CHAR, Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.shared.domain.base_entity import Base


class EvalSimulatorLlmCallModel(Base):
    """ORM mapping for ``eval_simulator_llm_call``.

    Mirrors ``campaign_llm_call`` schema for cost bucket separation (H6).
    Eval-specific eval_metadata JSONB carries mandatory tags (H5):
    eval_run_kind, archetype_slug, actor_profile_id, trial_n, simulation_id, run_id.
    """

    __tablename__ = "eval_simulator_llm_call"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    lead_id = Column(UUID(as_uuid=True), nullable=True)  # NULL — eval has no per-lead audit
    channel_type = Column(String(32), nullable=False, default="eval_simulator")
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
    # NULL allowed: paridad 086_llm_call_cost_usd_nullable.
    # NULL = cost unknown (unknown model or cache miss). NOT zero.
    cost_usd = Column(Numeric(16, 10), nullable=True)

    tenant_currency = Column(CHAR(3), nullable=True)
    fx_rate_to_tenant = Column(Numeric(16, 8), nullable=True)
    fx_rate_source = Column(String(32), nullable=True)
    cost_tenant_currency = Column(Numeric(16, 8), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    status = Column(String(16), nullable=False, default="ok")
    error_type = Column(String(64), nullable=True)

    # H5 mandatory eval metadata tags (eval_run_kind, archetype_slug,
    # actor_profile_id, trial_n, simulation_id, run_id).
    # server_default defined in migration 125 raw SQL ('{}'::jsonb).
    eval_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
    )

    def __repr__(self) -> str:
        """Return a debug-friendly summary of the eval LLM call."""
        return (
            f"<EvalSimulatorLlmCall id={self.id} provider={self.provider} "
            f"model={self.model_responded} status={self.status}>"
        )
