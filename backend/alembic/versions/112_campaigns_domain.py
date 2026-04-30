"""campaigns_domain.

PI-1 S1 PR-3 — campaigns module data plane.
Tables: campaign, campaign_step, campaign_task, segment, segment_snapshot, campaign_template.
Idempotente raw SQL (regla backend-migrations.md).
"""

from alembic import op

revision: str = "112_campaigns_domain"
down_revision: str | None = "111_copilot_blocks_backfill_marker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── campaign ─────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            description VARCHAR(2000),
            campaign_type VARCHAR(32) NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'draft',
            segment_id UUID,
            segment_snapshot_id UUID,
            channel_priority JSONB NOT NULL DEFAULT '[]'::jsonb,
            offer_id UUID,
            brand_summary_id UUID,
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            scheduled_at TIMESTAMPTZ,
            launched_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_by_user_id UUID,
            created_by_source VARCHAR(32) NOT NULL DEFAULT 'api',
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_campaign_status_values CHECK (
                status IN ('draft','scheduled','running','paused','completed','canceled')
            ),
            CONSTRAINT chk_campaign_type_values CHECK (
                campaign_type IN ('agent_conversation','email_drip','email_broadcast',
                                  'event_trigger','push_notification','retargeting_export')
            )
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_tenant_status ON campaign (tenant_id, status);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_tenant_scheduled ON campaign (tenant_id, scheduled_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_tenant_created ON campaign (tenant_id, created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_segment ON campaign (segment_id) WHERE segment_id IS NOT NULL;")

    # ── campaign_step ────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_step (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            campaign_id UUID NOT NULL,
            step_type VARCHAR(32) NOT NULL,
            step_index INT NOT NULL,
            label VARCHAR(128),
            next_step_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            step_config JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_step_type_values CHECK (
                step_type IN ('send_message','wait_delay','branch_on_condition',
                              'call_subagent_brief','mark_complete')
            ),
            CONSTRAINT chk_step_index_nonneg CHECK (step_index >= 0)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_step_tenant_campaign ON campaign_step (tenant_id, campaign_id);")

    # ── campaign_task (worker queue performance crítico) ─────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_task (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            campaign_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            step_id UUID,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            scheduled_at TIMESTAMPTZ NOT NULL,
            dispatched_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ,
            executed_at TIMESTAMPTZ,
            channel_used VARCHAR(32),
            external_message_id VARCHAR(255),
            attempt_count INT NOT NULL DEFAULT 0,
            last_error VARCHAR(2000),
            compliance_check JSONB,
            outbox_event_id UUID,
            idempotency_key VARCHAR(256) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_task_status_values CHECK (
                status IN ('pending','scheduled','dispatched','sent','failed','skipped','bounced')
            ),
            CONSTRAINT chk_task_attempt_count_nonneg CHECK (attempt_count >= 0)
        );
    """)
    # Unique constraint idempotente — drop+add para idempotencia (primera apply OK, re-apply OK).
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_campaign_task_tenant_idem'
            ) THEN
                ALTER TABLE campaign_task
                ADD CONSTRAINT uq_campaign_task_tenant_idem UNIQUE (tenant_id, idempotency_key);
            END IF;
        END $$;
    """)
    # Worker queue partial idx — performance crítico 1000 clientes (arch test enforces).
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_task_worker_queue
        ON campaign_task (tenant_id, status, scheduled_at)
        WHERE status IN ('pending','scheduled');
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_task_tenant_campaign_status
        ON campaign_task (tenant_id, campaign_id, status);
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_task_lead ON campaign_task (lead_id);")

    # ── segment ──────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS segment (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            name VARCHAR(128) NOT NULL,
            description VARCHAR(1000),
            segment_type VARCHAR(16) NOT NULL DEFAULT 'dynamic',
            filter_dsl JSONB NOT NULL DEFAULT '{}'::jsonb,
            estimated_size INT,
            last_calculated_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_segment_type_values CHECK (segment_type IN ('dynamic','static')),
            CONSTRAINT chk_segment_estimated_size_nonneg CHECK (estimated_size IS NULL OR estimated_size >= 0)
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_segment_tenant_name_alive
        ON segment (tenant_id, name) WHERE deleted_at IS NULL;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_segment_tenant_created ON segment (tenant_id, created_at);")

    # ── segment_snapshot ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS segment_snapshot (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            segment_id UUID NOT NULL,
            snapshotted_at TIMESTAMPTZ NOT NULL,
            lead_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            lead_count INT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_snapshot_lead_count_nonneg CHECK (lead_count >= 0)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_segment_snapshot_tenant_segment_at
        ON segment_snapshot (tenant_id, segment_id, snapshotted_at DESC);
    """)

    # ── campaign_template (placeholder schema, populated PR-4) ───────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_template (
            id UUID PRIMARY KEY,
            tenant_id UUID,
            slug VARCHAR(64) NOT NULL,
            name VARCHAR(128) NOT NULL,
            description VARCHAR(2000) NOT NULL,
            campaign_type VARCHAR(32) NOT NULL,
            template_body JSONB NOT NULL DEFAULT '{}'::jsonb,
            recommended_segment_slugs JSONB NOT NULL DEFAULT '[]'::jsonb,
            tags JSONB NOT NULL DEFAULT '[]'::jsonb,
            version INT NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_tpl_slug_format CHECK (slug ~ '^[a-z0-9_-]+$'),
            CONSTRAINT chk_tpl_version_pos CHECK (version >= 1),
            CONSTRAINT chk_tpl_type_values CHECK (
                campaign_type IN ('agent_conversation','email_drip','email_broadcast',
                                  'event_trigger','push_notification','retargeting_export')
            )
        );
    """)
    # Two partial unique idx — global vs tenant-scoped (NULL distinct semantics).
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_campaign_template_global_slug_alive
        ON campaign_template (slug) WHERE tenant_id IS NULL AND deleted_at IS NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_campaign_template_tenant_slug_alive
        ON campaign_template (tenant_id, slug) WHERE tenant_id IS NOT NULL AND deleted_at IS NULL;
    """)


def downgrade() -> None:
    # Reverse drop. Idempotente.
    op.execute("DROP TABLE IF EXISTS campaign_template;")
    op.execute("DROP TABLE IF EXISTS segment_snapshot;")
    op.execute("DROP TABLE IF EXISTS segment;")
    op.execute("DROP TABLE IF EXISTS campaign_task;")
    op.execute("DROP TABLE IF EXISTS campaign_step;")
    op.execute("DROP TABLE IF EXISTS campaign;")
