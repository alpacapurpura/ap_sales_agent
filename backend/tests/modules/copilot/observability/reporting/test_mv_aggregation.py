"""Tests for the daily-LLM-cost materialised view.

Schema parsing only — same approach as ``test_migration_schema.py``. The
materialised view exercises Postgres-only features (``REFRESH
MATERIALIZED VIEW CONCURRENTLY``, generated-column dependent rollup) so
hitting a live DB belongs to the integration suite. Source-parse keeps
the structural invariants in a fast unit test.
"""

from __future__ import annotations

import re
from pathlib import Path

MIGRATION_FILE = Path(__file__).resolve().parents[5] / "alembic" / "versions" / "077_copilot_daily_llm_cost_mv.py"


def _src() -> str:
    return MIGRATION_FILE.read_text(encoding="utf-8")


class TestMigrationFile:
    def test_file_present(self) -> None:
        assert MIGRATION_FILE.exists(), (
            f"Expected migration at {MIGRATION_FILE}; create it before running this test (TDD red)."
        )

    def test_revision_id_and_down_revision(self) -> None:
        src = _src()
        assert 'revision: str = "077_copilot_daily_llm_cost_mv"' in src
        assert 'down_revision: str | None = "076_copilot_billing_cycle_function"' in src


class TestMaterializedView:
    def test_create_mv_is_idempotent(self) -> None:
        src = _src()
        assert re.search(
            r"CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_llm_cost_per_tenant",
            src,
        )

    def test_grouped_by_tenant_day_model_provider_role(self) -> None:
        src = _src()
        # The five group-by columns drive the rollup grain. They must
        # appear in the GROUP BY clause exactly.
        for column in [
            "tenant_id",
            "occurred_on",
            "model_responded",
            "provider",
            "role",
        ]:
            assert column in src

        assert re.search(
            r"GROUP BY\s+tenant_id\s*,\s*occurred_on\s*,\s*model_responded\s*,\s*provider\s*,\s*role",
            src,
            re.IGNORECASE,
        )

    def test_aggregates_present(self) -> None:
        src = _src()
        for clause in [
            "COUNT(*) AS call_count",
            "COUNT(DISTINCT turn_id)",
            "COUNT(DISTINCT conversation_id)",
            "SUM(input_tokens)",
            "SUM(output_tokens)",
            "SUM(cached_read_tokens)",
            "SUM(cost_usd)",
            "SUM(cost_tenant_currency)",
            "AVG(duration_ms)",
        ]:
            assert clause in src, f"Missing aggregate: {clause}"

    def test_error_count_uses_filter_clause(self) -> None:
        # ``COUNT(...) FILTER (WHERE status='error')`` is the canonical
        # Postgres-style aggregate filter.
        src = _src()
        assert re.search(
            r"COUNT\(\*\)\s+FILTER\s+\(WHERE\s+status\s*=\s*'error'\)\s+AS\s+error_count",
            src,
            re.IGNORECASE,
        )

    def test_unique_index_for_concurrent_refresh(self) -> None:
        # CONCURRENT refresh requires a UNIQUE index covering the GROUP
        # BY columns.
        src = _src()
        assert re.search(
            r"CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_daily_llm_cost_per_tenant_pk",
            src,
        )

    def test_downgrade_drops_mv(self) -> None:
        src = _src()
        assert "DROP MATERIALIZED VIEW IF EXISTS mv_daily_llm_cost_per_tenant" in src
