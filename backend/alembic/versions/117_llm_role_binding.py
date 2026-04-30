"""llm_role_binding + llm_config_audit tables.

PI-2 S4 PR-1 db-registry-admin-ui.

Idempotent raw SQL (IF NOT EXISTS) per backend-migrations.md rules.
Partial unique index for (role, tenant_id) where is_active=TRUE uses the
COALESCE trick to handle NULL tenant_id uniformly in Postgres.

Revision ID: 117_llm_role_binding
Revises: 116_litellm_db_marker
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op

revision: str = "117_llm_role_binding"
down_revision: str | None = "116_litellm_db_marker"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create llm_role_binding and llm_config_audit tables idempotently."""
    # ── 1. llm_role_binding ──────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS llm_role_binding (
            id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            role            VARCHAR(32)     NOT NULL,
            provider        VARCHAR(64)     NOT NULL,
            model           VARCHAR(128)    NOT NULL,
            is_active       BOOLEAN         NOT NULL DEFAULT FALSE,
            tenant_id       UUID            NULL,
            config          JSONB           NOT NULL DEFAULT '{}',
            eval_score      NUMERIC(5,4)    NULL,
            notes           TEXT            NULL,
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            created_by      VARCHAR(128)    NULL,
            activated_at    TIMESTAMPTZ     NULL,
            deactivated_at  TIMESTAMPTZ     NULL,
            CONSTRAINT ck_llm_role_binding_role CHECK (
                role IN ('nano','fast','reasoning','agent','vision','embedding')
            )
        )
    """)

    # Partial unique index — at most 1 active binding per (role, tenant_id_or_NULL).
    # COALESCE trick: NULL tenant_id → sentinel UUID so Postgres treats global
    # rows as distinct from each other (Postgres NULL != NULL in UNIQUE indexes).
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_role_binding_active_per_role
            ON llm_role_binding (role, COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'))
            WHERE is_active = TRUE
    """)

    # Hot-path resolve index: WHERE role=X AND tenant_id IS NULL AND is_active=TRUE
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_llm_role_binding_role_tenant_active
            ON llm_role_binding (role, tenant_id, is_active)
    """)

    # ── 2. llm_config_audit ──────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS llm_config_audit (
            id          UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            actor       VARCHAR(128)    NOT NULL,
            action      VARCHAR(32)     NOT NULL,
            role        VARCHAR(32)     NOT NULL,
            tenant_id   UUID            NULL,
            before      JSONB           NULL,
            after       JSONB           NULL,
            reason      TEXT            NULL,
            created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_llm_config_audit_action CHECK (
                action IN ('create','activate','deactivate','update_config','test_ping','rollback')
            )
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_llm_config_audit_role_created
            ON llm_config_audit (role, created_at DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_llm_config_audit_tenant_created
            ON llm_config_audit (tenant_id, created_at DESC)
            WHERE tenant_id IS NOT NULL
    """)


def downgrade() -> None:
    """No-op — tables hold audit trail and cannot be safely dropped.

    If manual cleanup is required:
      DROP TABLE llm_config_audit;
      DROP TABLE llm_role_binding;
    """
