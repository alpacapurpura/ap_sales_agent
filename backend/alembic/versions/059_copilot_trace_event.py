"""Copilot observability: trace-event table.

One row per significant event inside a copilot turn:

* ``turn_start`` / ``turn_end`` — envelope for a single /copilot/chat request.
* ``llm_call`` — each model invocation (agent reasoning + re-invocations after
  tool results). Carries model, prompt/tokens snapshot, duration, status.
* ``tool_call`` — each LangChain tool invocation with name, args, output, status.
* ``card_emitted`` — each CardBlock emitted during streaming.
* ``node_enter`` / ``node_exit`` — LangGraph node transitions.
* ``error`` — exceptions or timeouts.

Events share ``turn_id`` (request-scoped) and may reference ``parent_span_id``
to build a call-tree. All heavy payloads go under ``data`` JSONB so the schema
stays stable while the copilot grows new event kinds.

Idempotent: ``CREATE TABLE IF NOT EXISTS`` + ``CREATE INDEX IF NOT EXISTS``.

Revision ID: 059_copilot_trace_event
Revises: 058_drop_interview_sessions
Create Date: 2026-04-23 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "059_copilot_trace_event"
down_revision: str | None = "058_drop_interview_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the copilot_trace_event table + supporting indexes."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_trace_event (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            user_id UUID,
            conversation_id UUID,
            message_id UUID,
            turn_id UUID NOT NULL,
            span_id UUID NOT NULL,
            parent_span_id UUID,
            event_type VARCHAR(32) NOT NULL,
            name VARCHAR(128),
            data JSONB NOT NULL DEFAULT '{}'::jsonb,
            duration_ms INTEGER,
            status VARCHAR(16) NOT NULL DEFAULT 'ok',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    # Most queries scope by conversation or turn; these indexes cover both.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_trace_event_conversation
        ON copilot_trace_event (conversation_id, created_at DESC)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_trace_event_turn
        ON copilot_trace_event (turn_id, created_at)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_trace_event_tenant_time
        ON copilot_trace_event (tenant_id, created_at DESC)
        """,
    )
    # Fast filtering errors for an alerting / summary query.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_trace_event_errors
        ON copilot_trace_event (tenant_id, created_at DESC)
        WHERE status = 'error'
        """,
    )


def downgrade() -> None:
    """Drop the trace-event table. Idempotent."""
    op.execute("DROP TABLE IF EXISTS copilot_trace_event CASCADE")
