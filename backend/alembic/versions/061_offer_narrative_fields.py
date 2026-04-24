"""offer: +13 narrative columns for OFFER_LEVEL sections

Revision ID: 061_offer_narrative_fields
Revises: 060_offer_extraction_traces
Create Date: 2026-04-24

Columns added to `products`:
  promise:    before_state, after_state, why_now, measurable_outcomes
  psychology: cultural_trust_barriers, emotional_triggers, status_drivers, regret_scenarios
  closing:    refund_process_description, urgency_drivers, scarcity_reason_honest,
              bonus_if_act_now, final_push_copy

refs: docs/contracts/offer-narrative-fields-CONTRACT.md §2
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "061_offer_narrative_fields"
down_revision: str | None = "060_offer_extraction_traces"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add 13 narrative columns to products table (idempotent)."""
    # --- promise ------------------------------------------------------
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS before_state TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS after_state TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS why_now TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS measurable_outcomes JSONB NOT NULL DEFAULT '[]'::jsonb")

    # --- psychology ---------------------------------------------------
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS cultural_trust_barriers JSONB NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS emotional_triggers JSONB NOT NULL DEFAULT '[]'::jsonb")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS status_drivers JSONB NOT NULL DEFAULT '[]'::jsonb")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS regret_scenarios JSONB NOT NULL DEFAULT '[]'::jsonb")

    # --- closing ------------------------------------------------------
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS refund_process_description TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS urgency_drivers JSONB NOT NULL DEFAULT '[]'::jsonb")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS scarcity_reason_honest TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS bonus_if_act_now TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS final_push_copy TEXT")


def downgrade() -> None:
    """Explicit NO-OP.

    Narrative columns are purely additive; dropping them would destroy tenant
    data. Use a forward-only migration if a rollback is really needed.
    """
