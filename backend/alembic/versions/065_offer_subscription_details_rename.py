"""offer: rename SubscriptionDetails JSONB keys (Fase 02 · Block D)

Revision ID: 065_offer_subscription_details_rename
Revises: 064_offer_value_stack_anchor
Create Date: 2026-04-24

Rewrites `products.specific_details` JSONB keys for MEMBRESIA offers
so SubscriptionDetails stays backward-compatible after the Pydantic
renames:

  - billing_cycle           → billing_frequency
  - content_update_freq     → content_update_frequency

The 5 new fields introduced in the same block
(auto_renewal_with_notice_days, cancellation_anticipation_days,
grace_period_days_on_failed_payment, member_benefits,
primary_communication_channel) default to null via Pydantic; no data
migration needed for them.

Idempotent: each UPDATE filters on the presence of the *old* key AND the
absence of the *new* key, so re-running is a no-op.

refs: docs/refactors/field-contract-ssot/phases/02-migrate-sections/
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "065_offer_subscription_details_rename"
down_revision: str | None = "064_offer_value_stack_anchor"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rewrite SubscriptionDetails JSONB keys (idempotent)."""
    # billing_cycle -> billing_frequency
    op.execute(
        """
        UPDATE products
        SET specific_details =
            (specific_details - 'billing_cycle')
            || jsonb_build_object('billing_frequency', specific_details->'billing_cycle')
        WHERE archetype = 'MEMBRESIA'
          AND specific_details ? 'billing_cycle'
          AND NOT specific_details ? 'billing_frequency';
        """
    )

    # content_update_freq -> content_update_frequency
    op.execute(
        """
        UPDATE products
        SET specific_details =
            (specific_details - 'content_update_freq')
            || jsonb_build_object('content_update_frequency', specific_details->'content_update_freq')
        WHERE archetype = 'MEMBRESIA'
          AND specific_details ? 'content_update_freq'
          AND NOT specific_details ? 'content_update_frequency';
        """
    )


def downgrade() -> None:
    """Reverse rename (idempotent)."""
    op.execute(
        """
        UPDATE products
        SET specific_details =
            (specific_details - 'billing_frequency')
            || jsonb_build_object('billing_cycle', specific_details->'billing_frequency')
        WHERE archetype = 'MEMBRESIA'
          AND specific_details ? 'billing_frequency'
          AND NOT specific_details ? 'billing_cycle';
        """
    )
    op.execute(
        """
        UPDATE products
        SET specific_details =
            (specific_details - 'content_update_frequency')
            || jsonb_build_object('content_update_freq', specific_details->'content_update_frequency')
        WHERE archetype = 'MEMBRESIA'
          AND specific_details ? 'content_update_frequency'
          AND NOT specific_details ? 'content_update_freq';
        """
    )
