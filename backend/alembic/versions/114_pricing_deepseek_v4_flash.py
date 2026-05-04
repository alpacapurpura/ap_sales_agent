"""Pricing snapshot DeepSeek V4-Flash for PR-3 PI-2 S2 LLM cost optimization.

Adds initial pricing row to ``model_pricing_snapshot`` for the new
``deepseek-v4-flash`` model used by NANO + MINI tier classifier + summarizer.

Pricing reference: research/2026-04-30-llm-landscape-chinese-models.md
- $0.14 input / $0.28 output per 1M tokens
- 1M context window
- No caching support (cache_*_cost_per_token = 0)
- Non-reasoning model

Idempotente — ON CONFLICT DO NOTHING via natural-key (provider, model)
when valid_to IS NULL.

Revision ID: 114_pricing_deepseek_v4_flash
Revises: 113_campaigns_audit_log
Create Date: 2026-04-30
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "114_pricing_deepseek_v4_flash"
down_revision: str | None = "113_campaigns_audit_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Insert pricing snapshot for deepseek-v4-flash. Idempotent."""
    # input_cost_per_token = 0.14 / 1_000_000 = 1.4e-7
    # output_cost_per_token = 0.28 / 1_000_000 = 2.8e-7
    op.execute(
        """
        INSERT INTO model_pricing_snapshot
            (provider, model, input_cost_per_token, output_cost_per_token,
             cache_read_cost_per_token, cache_write_cost_per_token,
             valid_from, valid_to, source, raw_payload)
        SELECT 'deepseek', 'deepseek-v4-flash',
               0.000000140000, 0.000000280000,
               0, 0,
               CURRENT_TIMESTAMP, NULL, 'manual_pr3_pi2_s2',
               '{"provider":"deepseek","model":"deepseek-v4-flash","input_cost_per_token":0.00000014,"output_cost_per_token":0.00000028,"cache_read_input_token_cost":0,"cache_creation_input_token_cost":0,"source":"manual_pr3_pi2_s2"}'::jsonb
        WHERE NOT EXISTS (
            SELECT 1 FROM model_pricing_snapshot
            WHERE provider = 'deepseek'
              AND model = 'deepseek-v4-flash'
              AND valid_to IS NULL
        )
        """
    )


def downgrade() -> None:
    """Close the deepseek-v4-flash pricing row (set valid_to = now)."""
    op.execute(
        """
        UPDATE model_pricing_snapshot
        SET valid_to = CURRENT_TIMESTAMP
        WHERE provider = 'deepseek'
          AND model = 'deepseek-v4-flash'
          AND valid_to IS NULL
        """
    )
