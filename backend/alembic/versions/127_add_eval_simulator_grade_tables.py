"""Eval simulator grade + grade cache tables (Story E sales-agent-voice-fidelity-grader-runtime).

Idempotente raw SQL IF NOT EXISTS (regla backend-migrations.md).

Creates 2 new tables + 6 indexes for the MAJ-EVAL grader infra:
  - eval_simulator_grade        : MajEvalScore rows per (simulation_id, turn_n, rubric_id)
  - eval_simulator_grade_cache  : hash-keyed deterministic cache (TTL=null until invalidation)

Pattern parity: eval_simulator (Alembic 125). Cost-bucket invariant H7 — judge LLM calls
write to eval_simulator_llm_call (existing Story B); rubric scores aggregated into eval_simulator_grade.

Decision D-BE-1: schema_version column = 1 cement; future bumps via SCHEMA_MIGRATIONS registry (H1 reuse).
Decision D-BE-2: cache table separate (D9/DQ7) — independent invalidation lifecycle vs grade rows.
Decision D-BE-3: judges JSONB stored verbatim (audit trail) — no per-judge column explosion.

Revision ID: 127_add_eval_simulator_grade_tables
Revises: 125_add_eval_simulator_observability_tables
Create Date: 2026-05-08
"""

from alembic import op

revision = "127_add_eval_simulator_grade_tables"
down_revision = "125_add_eval_simulator_observability_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create eval_simulator_grade + eval_simulator_grade_cache tables."""
    # ── eval_simulator_grade ────────────────────────────────────────────
    # MajEvalScore row per (simulation_id, turn_n, rubric_id). PK composite.
    # judges JSONB carries 3 (or 6 if debate) JudgeOpinion entries verbatim.
    op.execute("""
        CREATE TABLE IF NOT EXISTS eval_simulator_grade (
            schema_version SMALLINT NOT NULL DEFAULT 1,
            simulation_id UUID NOT NULL,
            turn_n INTEGER NOT NULL,
            rubric_id VARCHAR(64) NOT NULL,
            rubric_version SMALLINT NOT NULL,
            tenant_slug VARCHAR(64) NOT NULL,
            persona_kind VARCHAR(32) NOT NULL,
            actor_profile_id VARCHAR(128) NOT NULL,
            judges JSONB NOT NULL,
            round_1_score NUMERIC(4,3) NOT NULL,
            round_2_score NUMERIC(4,3),
            final_score NUMERIC(4,3) NOT NULL,
            round_1_variance NUMERIC(4,3) NOT NULL,
            round_2_variance NUMERIC(4,3),
            debate_triggered BOOLEAN NOT NULL DEFAULT FALSE,
            unconverged BOOLEAN NOT NULL DEFAULT FALSE,
            r2_partial BOOLEAN NOT NULL DEFAULT FALSE,
            suspicious BOOLEAN NOT NULL DEFAULT FALSE,
            injection_attempt_detected BOOLEAN NOT NULL DEFAULT FALSE,
            cost_usd_total NUMERIC(10,6) NOT NULL DEFAULT 0,
            latency_ms_total INTEGER NOT NULL,
            cache_hit_count SMALLINT NOT NULL DEFAULT 0,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_eval_simulator_grade PRIMARY KEY (simulation_id, turn_n, rubric_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_grade_tenant_persona
        ON eval_simulator_grade (tenant_slug, persona_kind)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_grade_rubric
        ON eval_simulator_grade (rubric_id, rubric_version)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_grade_unconverged
        ON eval_simulator_grade (unconverged) WHERE unconverged = TRUE
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_grade_actor_profile
        ON eval_simulator_grade (actor_profile_id)
    """)

    # ── eval_simulator_grade_cache ──────────────────────────────────────
    # Hash-keyed cache (D8 cement). cache_key = sha256 hex(64 chars).
    # Composition: hash(transcript_hash + rubric_id + tenant_voice_hash + judge_set_hash + rubric_version).
    # TTL=null — immutable until D8/D16 trigger invalidates by recomputing key.
    op.execute("""
        CREATE TABLE IF NOT EXISTS eval_simulator_grade_cache (
            cache_key VARCHAR(64) PRIMARY KEY,
            schema_version SMALLINT NOT NULL DEFAULT 1,
            transcript_hash VARCHAR(64) NOT NULL,
            rubric_id VARCHAR(64) NOT NULL,
            rubric_version SMALLINT NOT NULL,
            tenant_voice_hash VARCHAR(64) NOT NULL,
            judge_set_hash VARCHAR(64) NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_hit_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_grade_cache_rubric
        ON eval_simulator_grade_cache (rubric_id, rubric_version)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_grade_cache_transcript
        ON eval_simulator_grade_cache (transcript_hash)
    """)


def downgrade() -> None:
    """Drop grader tables (eval-only, no production data)."""
    op.execute("DROP TABLE IF EXISTS eval_simulator_grade_cache CASCADE")
    op.execute("DROP TABLE IF EXISTS eval_simulator_grade CASCADE")
