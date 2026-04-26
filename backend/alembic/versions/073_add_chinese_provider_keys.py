"""iam: +tenants.{deepseek,kimi,dashscope}_api_key (multi-provider Sprint 0)

Revision ID: 073_add_chinese_provider_keys
Revises: 072_copilot_workflow_metric
Create Date: 2026-04-26

Adds three new per-tenant API key columns so each tenant can override the
platform credentials for the Chinese-provider tier (DeepSeek, Kimi /
Moonshot, Qwen / DashScope). Mirrors the existing
``openai_api_key`` / ``gemini_api_key`` columns. All nullable — empty key
falls back to the platform-level env var.

Idempotent (``ADD COLUMN IF NOT EXISTS`` per
.claude/rules/backend-migrations.md).

refs:
- backend/src/modules/iam/infrastructure/models/tenant_model.py
- backend/src/shared/infrastructure/llm/router.py
"""

from collections.abc import Sequence

from alembic import op

revision: str = "073_add_chinese_provider_keys"
down_revision: str | None = "072_copilot_workflow_metric"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add per-tenant API keys for DeepSeek, Kimi, DashScope (idempotent)."""
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deepseek_api_key VARCHAR",
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS kimi_api_key VARCHAR",
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS dashscope_api_key VARCHAR",
    )


def downgrade() -> None:
    """Explicit NO-OP — credentials columns are not destructively dropped."""
