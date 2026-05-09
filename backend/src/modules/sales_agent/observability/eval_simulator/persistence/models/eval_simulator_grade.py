"""SQLAlchemy model for ``eval_simulator_grade`` (Story E grader runtime).

Mirror of Alembic migration 127. Pydantic ``MajEvalScore`` v1 schema cement.

Pattern parity: ``eval_simulator_llm_call.py`` (Story B). R5 schema-mirror exception
(.claude/rules/backend-ddd.md): builder-backend MAY touch persistence/models/ for schema
mirror from migration. Cero domain/application/api/ touches.

Decisions applicable: D-BE-1 (schema_version=1 cement), D-BE-3 (schema-mirror R5),
D-BE-4 (MajEvalScore v1 cement).
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.shared.domain.base_entity import Base


class EvalSimulatorGradeModel(Base):
    """ORM mapping for ``eval_simulator_grade``.

    PK composite ``(simulation_id, turn_n, rubric_id)`` — one row per (turn x rubric).
    judges JSONB stores 3 or 6 ``JudgeOpinion`` Pydantic dicts verbatim (audit trail).
    metadata_ is the Python attribute name; SQL column name is ``metadata``.

    Cost-bucket invariant H7: judge LLM calls write to ``eval_simulator_llm_call`` ONLY.
    This table stores aggregated grade scores, NOT individual LLM call records.
    """

    __tablename__ = "eval_simulator_grade"

    schema_version = Column(SmallInteger, nullable=False, default=1)
    simulation_id = Column(UUID(as_uuid=True), nullable=False)
    turn_n = Column(Integer, nullable=False)
    rubric_id = Column(String(64), nullable=False)
    rubric_version = Column(SmallInteger, nullable=False)
    tenant_slug = Column(String(64), nullable=False)
    persona_kind = Column(String(32), nullable=False)
    actor_profile_id = Column(String(128), nullable=False)
    judges = Column(JSONB, nullable=False)
    round_1_score = Column(Numeric(4, 3), nullable=False)
    round_2_score = Column(Numeric(4, 3), nullable=True)
    final_score = Column(Numeric(4, 3), nullable=False)
    round_1_variance = Column(Numeric(4, 3), nullable=False)
    round_2_variance = Column(Numeric(4, 3), nullable=True)
    debate_triggered = Column(Boolean, nullable=False, default=False)
    unconverged = Column(Boolean, nullable=False, default=False)
    r2_partial = Column(Boolean, nullable=False, default=False)
    suspicious = Column(Boolean, nullable=False, default=False)
    injection_attempt_detected = Column(Boolean, nullable=False, default=False)
    cost_usd_total = Column(Numeric(10, 6), nullable=False, default=0)
    latency_ms_total = Column(Integer, nullable=False)
    cache_hit_count = Column(SmallInteger, nullable=False, default=0)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("simulation_id", "turn_n", "rubric_id", name="pk_eval_simulator_grade"),)

    def __repr__(self) -> str:
        """Return a debug-friendly summary of the eval grade row."""
        return (
            f"<EvalSimulatorGrade simulation_id={self.simulation_id} "
            f"turn_n={self.turn_n} rubric_id={self.rubric_id} "
            f"final_score={self.final_score}>"
        )
