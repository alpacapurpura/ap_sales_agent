"""SQLAlchemy model for ``eval_simulator_grade_cache`` (Story E grader cache).

Mirror of Alembic migration 127 (cache table section). Separate lifecycle from
``eval_simulator_grade`` — independent TTL=null invalidation (D9 / DQ7 cement).

R5 schema-mirror exception (.claude/rules/backend-ddd.md): builder-backend MAY touch
persistence/models/ for schema mirror from migration.

Decisions applicable: D-BE-2 (cache table separate), D8 (cache key sha256 64-char),
D9 (independent lifecycle TTL=null).
"""

from __future__ import annotations

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Column, DateTime, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB


class EvalSimulatorGradeCacheModel(Base):
    """ORM mapping for ``eval_simulator_grade_cache``.

    cache_key = sha256 hex(64 chars) of canonical 5-field composition (D8 cement):
        hash(transcript_hash + rubric_id + tenant_voice_hash + judge_set_hash + rubric_version).

    TTL=null — immutable until D8/D16 trigger invalidates by recomputing key.
    Cache invalidation is automatic: key changes on rubric MD bump (rubric_version),
    weight change (judge_set_hash), voice change (tenant_voice_hash),
    or transcript change (transcript_hash).
    """

    __tablename__ = "eval_simulator_grade_cache"

    cache_key = Column(String(64), primary_key=True)
    schema_version = Column(SmallInteger, nullable=False, default=1)
    transcript_hash = Column(String(64), nullable=False)
    rubric_id = Column(String(64), nullable=False)
    rubric_version = Column(SmallInteger, nullable=False)
    tenant_voice_hash = Column(String(64), nullable=False)
    judge_set_hash = Column(String(64), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_hit_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        """Return a debug-friendly summary of the cache row."""
        return f"<EvalSimulatorGradeCache cache_key={self.cache_key[:16]}... rubric_id={self.rubric_id}>"
