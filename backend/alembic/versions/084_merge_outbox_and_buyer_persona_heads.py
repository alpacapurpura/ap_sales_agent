"""Merge heads: outbox+observability and drop_buyer_persona_fields.

Revision ID: 084_merge_outbox_and_buyer_persona_heads
Revises: 083_add_domain_event_outbox_and_campaign_observability, acdcfa45d526
Create Date: 2026-04-29
"""

revision = "084_merge_outbox_and_buyer_persona_heads"
down_revision = (
    "083_add_domain_event_outbox_and_campaign_observability",
    "acdcfa45d526",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge only — no DDL changes."""


def downgrade() -> None:
    """Merge only — no DDL changes."""
