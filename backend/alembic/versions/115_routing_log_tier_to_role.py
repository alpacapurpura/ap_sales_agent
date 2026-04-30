"""Rename copilot_routing_log.tier_selected → role_selected + value migration.

S3 PR-1 cleanup-modeltier-convergence (PI-2). SSoT alignment per
docs/domains/llm-routing.md — ModelTier deprecated en favor de ModelRole.

Migración:
1. RENAME column ``copilot_routing_log.tier_selected`` → ``role_selected``
   (idempotente: rename solo si tier_selected existe y role_selected no).
2. UPDATE valores legacy ModelTier → ModelRole en ``copilot_routing_log.role_selected``:
   ``mini`` → ``fast``, ``heavy`` → ``agent`` (NANO y REASONING permanecen).
3. UPDATE valores legacy en ``copilot_conversation.last_tier_used`` (column name preserva
   por telemetría histórica, pero values ahora son ModelRole strings).

Idempotente — todo bajo ``IF EXISTS`` + UPDATE …WHERE value IN legacy.

Revision ID: 115_routing_log_tier_to_role
Revises: 114_pricing_deepseek_v4_flash
Create Date: 2026-04-30
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "115_routing_log_tier_to_role"
down_revision: str | None = "114_pricing_deepseek_v4_flash"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename column + UPDATE legacy values to ModelRole."""
    # 1. Rename column tier_selected → role_selected (idempotente)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'copilot_routing_log'
                  AND column_name = 'tier_selected'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'copilot_routing_log'
                  AND column_name = 'role_selected'
            ) THEN
                ALTER TABLE copilot_routing_log
                    RENAME COLUMN tier_selected TO role_selected;
            END IF;
        END $$;
        """
    )

    # 2. UPDATE legacy ModelTier values → ModelRole (idempotente — re-run no-op)
    op.execute(
        """
        UPDATE copilot_routing_log
        SET role_selected = 'fast'
        WHERE role_selected = 'mini'
        """
    )
    op.execute(
        """
        UPDATE copilot_routing_log
        SET role_selected = 'agent'
        WHERE role_selected = 'heavy'
        """
    )

    # 3. UPDATE legacy values en copilot_conversation.last_tier_used
    op.execute(
        """
        UPDATE copilot_conversation
        SET last_tier_used = 'fast'
        WHERE last_tier_used = 'mini'
        """
    )
    op.execute(
        """
        UPDATE copilot_conversation
        SET last_tier_used = 'agent'
        WHERE last_tier_used = 'heavy'
        """
    )


def downgrade() -> None:
    """Revert column rename + value swap (best-effort).

    Down migration provided for completeness — production usa forward-only.
    """
    # Revert values
    op.execute(
        """
        UPDATE copilot_conversation
        SET last_tier_used = 'heavy'
        WHERE last_tier_used = 'agent'
        """
    )
    op.execute(
        """
        UPDATE copilot_conversation
        SET last_tier_used = 'mini'
        WHERE last_tier_used = 'fast'
        """
    )
    op.execute(
        """
        UPDATE copilot_routing_log
        SET role_selected = 'heavy'
        WHERE role_selected = 'agent'
        """
    )
    op.execute(
        """
        UPDATE copilot_routing_log
        SET role_selected = 'mini'
        WHERE role_selected = 'fast'
        """
    )
    # Revert column rename
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'copilot_routing_log'
                  AND column_name = 'role_selected'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'copilot_routing_log'
                  AND column_name = 'tier_selected'
            ) THEN
                ALTER TABLE copilot_routing_log
                    RENAME COLUMN role_selected TO tier_selected;
            END IF;
        END $$;
        """
    )
