"""add offer_extraction_traces table.

Revision ID: 060_offer_extraction_traces
Revises: 059_copilot_trace_event
Create Date: 2026-04-23

Idempotent — creates the table only if absent. Mirrors the brand_extraction
trace schema so the ``OfferExtractionTraceCollector`` can persist timeline
events, crawl/merge durations, and status transitions. Without this table
the worker raises ``UndefinedTable`` the first time a URL/doc extraction
runs in an environment that stamps from an earlier revision.
"""

from __future__ import annotations

from alembic import op

revision: str = "060_offer_extraction_traces"
down_revision: str | None = "059_copilot_trace_event"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create offer_extraction_traces table (idempotent)."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_extraction_traces (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            job_id VARCHAR NOT NULL,
            mode VARCHAR NOT NULL,
            url TEXT,
            status VARCHAR NOT NULL DEFAULT 'running',
            content_length INTEGER DEFAULT 0,
            sections_total INTEGER DEFAULT 0,
            sections_succeeded INTEGER DEFAULT 0,
            total_duration_s DOUBLE PRECISION,
            error_message TEXT,
            events JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """,
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_extraction_traces_tenant_id ON offer_extraction_traces (tenant_id);",
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_extraction_traces_job_id ON offer_extraction_traces (job_id);",
    )


def downgrade() -> None:
    """Drop offer_extraction_traces table (idempotent)."""
    op.execute("DROP INDEX IF EXISTS ix_offer_extraction_traces_job_id;")
    op.execute("DROP INDEX IF EXISTS ix_offer_extraction_traces_tenant_id;")
    op.execute("DROP TABLE IF EXISTS offer_extraction_traces;")
