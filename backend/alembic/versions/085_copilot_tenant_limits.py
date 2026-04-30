"""copilot_tenant_limits — per-tenant rate limit and media cap overrides.

PI-2 S1 PR-1 voice-media-hardening.

Idempotent raw SQL (IF NOT EXISTS) per backend-migrations.md.

Revision ID: 085_copilot_tenant_limits
Revises: 084_merge_outbox_and_buyer_persona_heads
Create Date: 2026-04-29
"""

from alembic import op

revision = "085_copilot_tenant_limits"
down_revision = "084_merge_outbox_and_buyer_persona_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create copilot_tenant_limits and copilot_tenant_limits_audit tables."""
    # ── Main table ──────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS copilot_tenant_limits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            voice_rpm_override INTEGER,
            media_max_bytes_override BIGINT,
            updated_by_user_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_copilot_tenant_limits_voice_rpm_positive
                CHECK (voice_rpm_override IS NULL OR voice_rpm_override > 0),
            CONSTRAINT chk_copilot_tenant_limits_voice_rpm_cap
                CHECK (voice_rpm_override IS NULL OR voice_rpm_override <= 1000),
            CONSTRAINT chk_copilot_tenant_limits_media_bytes_positive
                CHECK (media_max_bytes_override IS NULL OR media_max_bytes_override > 0),
            CONSTRAINT chk_copilot_tenant_limits_media_bytes_upper
                CHECK (media_max_bytes_override IS NULL OR media_max_bytes_override <= 104857600)
        );
    """)

    # Partial unique index: one active row per tenant (allows multiple soft-deleted rows)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_copilot_tenant_limits_tenant_alive
        ON copilot_tenant_limits (tenant_id)
        WHERE deleted_at IS NULL;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_tenant_limits_tenant_id
        ON copilot_tenant_limits (tenant_id);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_tenant_limits_updated_at
        ON copilot_tenant_limits (updated_at);
    """)

    # ── Audit table (append-only, Q2) ───────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS copilot_tenant_limits_audit (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            action VARCHAR(16) NOT NULL,
            voice_rpm_before INTEGER,
            voice_rpm_after INTEGER,
            media_max_bytes_before BIGINT,
            media_max_bytes_after BIGINT,
            changed_by_user_id UUID,
            changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT chk_copilot_tenant_limits_audit_action
                CHECK (action IN ('upsert', 'soft_delete'))
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_tenant_limits_audit_tenant_id
        ON copilot_tenant_limits_audit (tenant_id);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_tenant_limits_audit_changed_at
        ON copilot_tenant_limits_audit (changed_at);
    """)


def downgrade() -> None:
    """Drop copilot_tenant_limits tables."""
    op.execute("DROP TABLE IF EXISTS copilot_tenant_limits_audit;")
    op.execute("DROP TABLE IF EXISTS copilot_tenant_limits;")
