"""PI-5 PR-1 — Copilot Telegram foundation.

Tables:
- ``copilot_channel_links`` (NEW) — chat_id ↔ tenant + user + role
- ``copilot_link_tokens`` (NEW) — single-use HMAC magic links

Extends ``copilot_conversations``:
- ``channel_type`` (NULLABLE) — 'telegram' | NULL = web
- ``channel_chat_id`` (NULLABLE)
- index ``(channel_type, channel_chat_id)``

All operations idempotent (rule ``backend-migrations.md``).
Cero FK cruzada hacia ``sales_agent_*`` (D-PI5-005 + arch fitness test).

Revision ID: 120_pi5_copilot_telegram
Revises: 119_llm_eval_gate
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "120_pi5_copilot_telegram"
down_revision = "119_llm_eval_gate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """All operations idempotent (raw SQL IF NOT EXISTS)."""
    # 1. copilot_channel_links — chat_id ↔ tenant + user + role
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_channel_links (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            channel_type VARCHAR(32) NOT NULL,
            channel_user_id VARCHAR(64) NOT NULL,
            channel_username VARCHAR(64),
            role VARCHAR(32) NOT NULL DEFAULT 'owner',
            linked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_seen_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            CONSTRAINT uq_copilot_channel_link_chat
                UNIQUE (tenant_id, channel_type, channel_user_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_channel_links_lookup "
        "ON copilot_channel_links(channel_type, channel_user_id) "
        "WHERE revoked_at IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_channel_links_tenant "
        "ON copilot_channel_links(tenant_id) WHERE revoked_at IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_channel_links_user "
        "ON copilot_channel_links(user_id) WHERE revoked_at IS NULL"
    )

    # 2. copilot_link_tokens — single-use HMAC magic link
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_link_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            token_hash VARCHAR(128) NOT NULL,
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_copilot_link_token_hash UNIQUE (token_hash)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_link_tokens_lookup "
        "ON copilot_link_tokens(token_hash, expires_at) WHERE used_at IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_link_tokens_tenant "
        "ON copilot_link_tokens(tenant_id, user_id, expires_at) "
        "WHERE used_at IS NULL"
    )

    # 3. copilot_conversations — extend with channel_type + channel_chat_id
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS channel_type VARCHAR(32)")
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS channel_chat_id VARCHAR(64)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_conversations_channel "
        "ON copilot_conversations(channel_type, channel_chat_id) "
        "WHERE channel_type IS NOT NULL"
    )


def downgrade() -> None:
    """Reverse upgrade — best effort. Cols remain (avoid data loss)."""
    op.execute("DROP INDEX IF EXISTS ix_copilot_conversations_channel")
    op.execute("DROP TABLE IF EXISTS copilot_link_tokens")
    op.execute("DROP TABLE IF EXISTS copilot_channel_links")
    # NOTE: cols channel_type/channel_chat_id NOT dropped (avoid data loss)
