"""Test fixtures for scripts/ tests.

Creates the copilot_backfill_runs table in the SQLite test DB, since this
table is created by alembic migration 111 (not via SQLA models — raw SQL only,
by design — so it's not in Base.metadata).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def _create_backfill_runs_table(db: Session) -> None:
    """Ensure copilot_backfill_runs exists in the SQLite test DB.

    This table is created by migration 111 via raw SQL. Since it has no SQLA
    model, it's absent from Base.metadata and therefore not created by
    conftest.db_engine. We create it here for tests that need it.

    SQLite-compatible DDL (no gen_random_uuid(), no TIMESTAMPTZ checks).
    """
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS copilot_backfill_runs (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                tenant_id TEXT NULL,
                started_at TEXT NOT NULL DEFAULT (datetime('now')),
                ended_at TEXT NULL,
                mode TEXT NOT NULL,
                convs_scanned INTEGER NOT NULL DEFAULT 0,
                convs_updated INTEGER NOT NULL DEFAULT 0,
                msgs_legacy_converted INTEGER NOT NULL DEFAULT 0,
                convs_skipped_corrupt INTEGER NOT NULL DEFAULT 0,
                failed_conv_ids TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL,
                error_message TEXT NULL,
                git_sha TEXT NULL
            )
            """
        )
    )
    db.commit()
