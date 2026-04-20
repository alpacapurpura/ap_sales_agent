"""align launch_editions.variant_structure DEFAULT with model server_default

Migration 049 added ``variant_structure`` as ``NOT NULL`` after backfill but
forgot to attach a column DEFAULT. The SA model declares
``server_default="temporal_cohort"`` — that hint only fires on ``CREATE TABLE``,
not on ``ALTER COLUMN``, so prod-style DBs ended up with ``NOT NULL`` + no
default.

Symptoms in dev: any INSERT into ``launch_editions`` that relied on the model's
server_default (placeholder edition spawned by ``OfferService``) failed with
``NotNullViolation`` because the repo did not pass an explicit value.

Sprint 14.1 fixes the root cause at the application layer (the service now
derives the structure from ``ARCHETYPE_CATALOG[archetype].default_variant_structure``
and passes it explicitly). This migration is the defense-in-depth net so the
DB schema matches the model declaration: any future caller that forgets to
pass the column will land on ``temporal_cohort`` instead of crashing.

Idempotency: ``ALTER COLUMN ... SET DEFAULT`` is safe to re-run.

Revision ID: 051_launch_editions_variant_structure_default
Revises: 050_add_offer_preset_id
Create Date: 2026-04-19 22:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "051_launch_editions_variant_structure_default"
down_revision: str | None = "050_add_offer_preset_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Attach the column DEFAULT to align DB schema with the SA model."""
    op.execute(
        """
        ALTER TABLE launch_editions
            ALTER COLUMN variant_structure SET DEFAULT 'temporal_cohort'
        """
    )


def downgrade() -> None:
    """Drop the DEFAULT — restores migration 049's exact end state."""
    op.execute(
        """
        ALTER TABLE launch_editions
            ALTER COLUMN variant_structure DROP DEFAULT
        """
    )
