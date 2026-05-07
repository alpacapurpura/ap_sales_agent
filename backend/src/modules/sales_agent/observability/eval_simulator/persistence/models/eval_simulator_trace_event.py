"""SQLAlchemy model for ``eval_simulator_trace_event``.

Mirror of ``campaign_trace_event`` (migration 083) with the addition of:

* ``eval_metadata`` — JSONB NOT NULL (mandatory H5 tags per 03-arch-be.md §1)
* ``lead_id``       — NULL (eval simulator does not track per-lead audit rows)

Origin: PI-12 Story B eval-foundation-simulator-homologation (2026-05-07).
R5 schema-mirror exception (.claude/rules/backend-ddd.md): builder-backend MAY touch
persistence/models/ for schema mirror from migration. Schema paridad campaigns/083.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.shared.domain.base_entity import Base


class EvalSimulatorTraceEventModel(Base):
    """ORM mapping for ``eval_simulator_trace_event``.

    Each row records a trace event emitted during a simulation turn.
    The eval_metadata JSONB carries mandatory tags (H5):
    eval_run_kind, archetype_slug, actor_profile_id, trial_n, simulation_id, run_id.
    """

    __tablename__ = "eval_simulator_trace_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    lead_id = Column(UUID(as_uuid=True), nullable=True)  # NULL — eval has no per-lead audit
    channel_type = Column(String(32), nullable=False, default="eval_simulator")
    turn_id = Column(UUID(as_uuid=True), nullable=False)
    span_id = Column(UUID(as_uuid=True), nullable=False)
    parent_span_id = Column(UUID(as_uuid=True), nullable=True)

    event_type = Column(String(32), nullable=False)
    name = Column(String(128), nullable=True)
    # server_default for data defined in migration 125 raw SQL ('{}'::jsonb).
    data = Column(
        JSONB,
        nullable=False,
        default=dict,
    )
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(16), nullable=False, default="ok")

    # H5 mandatory eval metadata tags (eval_run_kind, archetype_slug,
    # actor_profile_id, trial_n, simulation_id, run_id).
    # server_default defined in migration 125 raw SQL ('{}'::jsonb).
    eval_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        """Return a debug-friendly summary of the eval trace event."""
        return (
            f"<EvalSimulatorTraceEvent id={self.id} event_type={self.event_type} "
            f"turn_id={self.turn_id} status={self.status}>"
        )
