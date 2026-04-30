"""LLM eval gate audit + per-role threshold tables.

PI-2 S5 PR-1 eval-gate-admin-wiring.

Idempotent raw SQL (IF NOT EXISTS) per backend-migrations.md rules.
Seeds default per-role thresholds per CONTRACT specification.

Revision ID: 119_llm_eval_gate
Revises: 118_llm_role_binding_seed_from_env
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op

revision: str = "119_llm_eval_gate"
down_revision: str | None = "118_llm_role_binding_seed_from_env"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create llm_eval_gate_runs (audit) + llm_eval_gate_threshold (config)."""
    # ── 1. llm_eval_gate_runs (immutable audit) ────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS llm_eval_gate_runs (
            id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            role            VARCHAR(32)     NOT NULL,
            candidate_model VARCHAR(128)    NOT NULL,
            candidate_provider VARCHAR(64)  NOT NULL,
            baseline_model  VARCHAR(128)    NULL,
            score           NUMERIC(5,4)    NOT NULL,
            threshold       NUMERIC(5,4)    NOT NULL,
            passed          BOOLEAN         NOT NULL,
            details         JSONB           NULL,
            ran_by          VARCHAR(128)    NOT NULL,
            ran_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_llm_eval_gate_role CHECK (
                role IN ('NANO','FAST','REASONING','AGENT','VISION','EMBEDDING')
            )
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_llm_eval_gate_runs_role_ran_at
            ON llm_eval_gate_runs (role, ran_at DESC)
    """)

    # ── 2. llm_eval_gate_threshold (per-role config) ────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS llm_eval_gate_threshold (
            role            VARCHAR(32)     PRIMARY KEY,
            threshold       NUMERIC(5,4)    NOT NULL,
            updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_by      VARCHAR(128)    NULL,
            CONSTRAINT ck_llm_eval_gate_threshold_role CHECK (
                role IN ('NANO','FAST','REASONING','AGENT','VISION','EMBEDDING')
            ),
            CONSTRAINT ck_llm_eval_gate_threshold_range CHECK (
                threshold >= 0 AND threshold <= 1
            )
        )
    """)

    # Seed per-role thresholds (D-CONTRACT §5):
    # NANO=0.95, FAST=0.95, REASONING=0.93, AGENT=0.95, VISION=0.90, EMBEDDING=0.95
    seeds = [
        ("NANO", "0.95"),
        ("FAST", "0.95"),
        ("REASONING", "0.93"),
        ("AGENT", "0.95"),
        ("VISION", "0.90"),
        ("EMBEDDING", "0.95"),
    ]
    for role, threshold in seeds:
        op.execute(f"""
            INSERT INTO llm_eval_gate_threshold (role, threshold, updated_by)
            VALUES ('{role}', {threshold}, 'system-migration-119')
            ON CONFLICT (role) DO NOTHING
        """)


def downgrade() -> None:
    """No-op. Drop would lose audit trail."""
