"""S8 — sales_agent scheduler meetings + webhook dedup.

Adds:

1. ``agent_state_checkpoints.scheduled_meetings`` JSONB column (default
   ``[]``) — append-only list of meetings tracked by the conversation.
   Each entry shape::

       {
         "tracking_id": str,                # BookingLink.token
         "event_slug": str,
         "expires_at": iso8601,
         "appointment_id": uuid | null,
         "scheduled_at": iso8601 | null,
         "status": "link_created" | "confirmed" | "completed" | "no_show"
                   | "cancelled" | "expired" | "missed",
         "reminder_24h_sent_at": iso8601 | null,
         "reminder_1h_sent_at":  iso8601 | null,
         "postcheck_sent_at":    iso8601 | null,
         "created_at": iso8601,
       }

2. ``scheduler_webhook_event`` table — idempotency log + audit for inbound
   webhooks from external scheduler providers (Cal.com / Calendly /
   Google Calendar push). Internal scheduler does NOT route through this
   table (its bookings come via ``POST /event-types/.../book`` direct).
   Natural key ``(provider, tracking_id, event_type, occurred_at)`` is
   UNIQUE — replays return 200 ``duplicate``.

Idempotent: every DDL statement uses ``IF NOT EXISTS`` so re-running
``alembic upgrade head`` is a no-op.

Revision ID: 080_sales_agent_scheduler_meetings
Revises: 079_cross_agent_daily_cost_mv
Create Date: 2026-04-28 06:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "080_sales_agent_scheduler_meetings"
down_revision: str | None = "079_cross_agent_daily_cost_mv"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply S8 scheduler schema additions."""
    op.execute(
        """
        ALTER TABLE agent_state_checkpoints
            ADD COLUMN IF NOT EXISTS scheduled_meetings JSONB
                NOT NULL DEFAULT '[]'::jsonb
        """,
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduler_webhook_event (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            provider VARCHAR(50) NOT NULL,
            tracking_id VARCHAR(255),
            event_type VARCHAR(50) NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL,
            tenant_id UUID,
            lead_id UUID,
            payload_raw JSONB NOT NULL,
            received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_scheduler_webhook_dedup
            ON scheduler_webhook_event (provider, tracking_id, event_type, occurred_at)
        """,
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_scheduler_webhook_tenant
            ON scheduler_webhook_event (tenant_id, received_at DESC)
        """,
    )


def downgrade() -> None:
    """Reverse S8 scheduler schema additions."""
    op.execute("DROP INDEX IF EXISTS ix_scheduler_webhook_tenant")
    op.execute("DROP INDEX IF EXISTS uq_scheduler_webhook_dedup")
    op.execute("DROP TABLE IF EXISTS scheduler_webhook_event")
    op.execute(
        "ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS scheduled_meetings",
    )
