"""Schema-level tests for Phase 1 migration ``075_copilot_observability_rebuild``.

These tests do **not** hit a live Postgres; they parse the migration source
and verify that all expected ``CREATE TABLE``, ``CREATE INDEX`` and
generated columns are declared. Real-DB validation lives in the manual
smoke step (``alembic upgrade head`` against the dev container).

Why source-parsing: tests must run native WSL without docker, and the
SQL touches Postgres-specific features (``GENERATED ALWAYS AS ... STORED``,
``UUID``, partial unique indexes) that SQLite cannot exercise.
"""

from __future__ import annotations

import re
from pathlib import Path

MIGRATION_FILE = Path(__file__).resolve().parents[4] / "alembic" / "versions" / "075_copilot_observability_rebuild.py"


def _migration_source() -> str:
    return MIGRATION_FILE.read_text(encoding="utf-8")


class TestMigrationFileExists:
    def test_file_present(self) -> None:
        assert MIGRATION_FILE.exists(), (
            f"Expected migration at {MIGRATION_FILE}; create it before running this test (TDD red)."
        )

    def test_revision_id_and_down_revision(self) -> None:
        src = _migration_source()
        assert 'revision: str = "075_copilot_observability_rebuild"' in src
        assert 'down_revision: str | None = "074_mutation_journal_natural_key_idempotent"' in src


class TestCopilotLlmCallTable:
    """``copilot_llm_call`` is the canonical event-sourced LLM-call log."""

    def test_create_table_idempotent(self) -> None:
        src = _migration_source()
        assert re.search(
            r"CREATE TABLE IF NOT EXISTS copilot_llm_call",
            src,
        )

    def test_required_columns(self) -> None:
        src = _migration_source()
        required = [
            "id UUID PRIMARY KEY",
            "tenant_id UUID NOT NULL",
            "user_id UUID",
            "conversation_id UUID",
            "turn_id UUID NOT NULL",
            "span_id UUID NOT NULL",
            "parent_span_id UUID",
            "role VARCHAR(32) NOT NULL",
            "provider VARCHAR(32) NOT NULL",
            "model_requested VARCHAR(128) NOT NULL",
            "model_responded VARCHAR(128) NOT NULL",
            "input_tokens INTEGER NOT NULL DEFAULT 0",
            "output_tokens INTEGER NOT NULL DEFAULT 0",
            "cached_read_tokens INTEGER NOT NULL DEFAULT 0",
            "cached_write_tokens INTEGER NOT NULL DEFAULT 0",
            "reasoning_tokens INTEGER NOT NULL DEFAULT 0",
            "pricing_version_id UUID NOT NULL",
            "input_unit_cost_usd NUMERIC(14,12) NOT NULL",
            "output_unit_cost_usd NUMERIC(14,12) NOT NULL",
            "cached_read_unit_cost_usd NUMERIC(14,12) NOT NULL DEFAULT 0",
            "cost_usd NUMERIC(16,10) NOT NULL",
            "tenant_currency CHAR(3)",
            "fx_rate_to_tenant NUMERIC(16,8)",
            "fx_rate_source VARCHAR(32)",
            "cost_tenant_currency NUMERIC(16,8)",
            "started_at TIMESTAMPTZ NOT NULL",
            "duration_ms INTEGER NOT NULL",
            "status VARCHAR(16) NOT NULL DEFAULT 'ok'",
            "error_type VARCHAR(64)",
        ]
        for column in required:
            assert column in src, f"Missing column declaration: {column}"

    def test_generated_columns(self) -> None:
        src = _migration_source()
        # Postgres GENERATED ALWAYS AS STORED — drives partition-friendly
        # rollups (occurred_on for daily MV, occurred_year_month for billing
        # cycle queries).
        # Postgres rejects non-IMMUTABLE expressions in stored generated
        # columns. ``TIMESTAMPTZ::DATE`` and ``to_char(TIMESTAMPTZ, ...)``
        # depend on the session timezone — so we anchor both to UTC via
        # ``AT TIME ZONE 'UTC'`` (which is IMMUTABLE).
        assert re.search(
            r"occurred_on DATE GENERATED ALWAYS AS "
            r"\(\(started_at AT TIME ZONE 'UTC'\)::date\) STORED",
            src,
        )
        # ``to_char`` is STABLE (locale-dependent), so we synthesise the
        # ``YYYY-MM`` string from ``EXTRACT`` (IMMUTABLE on timestamp w/o TZ)
        # and ``LPAD`` (IMMUTABLE).
        assert re.search(
            r"occurred_year_month VARCHAR\(7\) GENERATED ALWAYS AS",
            src,
        )
        assert "EXTRACT(YEAR FROM started_at AT TIME ZONE 'UTC')" in src
        assert "EXTRACT(MONTH FROM started_at AT TIME ZONE 'UTC')" in src
        assert "LPAD(" in src

    def test_indexes(self) -> None:
        src = _migration_source()
        for idx in (
            "ix_llm_call_tenant_day",
            "ix_llm_call_turn",
            "ix_llm_call_tenant_model_day",
            "ix_llm_call_errors",
        ):
            assert f"CREATE INDEX IF NOT EXISTS {idx}" in src, f"Missing idempotent index declaration: {idx}"
        # Partial index on errors must filter status='error'
        assert re.search(
            r"ix_llm_call_errors[\s\S]+WHERE status\s*=\s*'error'",
            src,
        )


class TestModelPricingSnapshotTable:
    def test_create_table_idempotent(self) -> None:
        src = _migration_source()
        assert "CREATE TABLE IF NOT EXISTS model_pricing_snapshot" in src

    def test_required_columns(self) -> None:
        src = _migration_source()
        required = [
            "id UUID PRIMARY KEY",
            "provider VARCHAR(32) NOT NULL",
            "model VARCHAR(128) NOT NULL",
            "input_cost_per_token NUMERIC(14,12) NOT NULL",
            "output_cost_per_token NUMERIC(14,12) NOT NULL",
            "cache_read_cost_per_token NUMERIC(14,12) DEFAULT 0",
            "cache_write_cost_per_token NUMERIC(14,12) DEFAULT 0",
            "batch_input_cost_per_token NUMERIC(14,12)",
            "source VARCHAR(32) NOT NULL",
            "source_etag VARCHAR(64)",
            "valid_from TIMESTAMPTZ NOT NULL",
            "valid_to TIMESTAMPTZ",
            "raw_payload JSONB NOT NULL",
        ]
        for column in required:
            assert column in src, f"Missing column declaration: {column}"

    def test_partial_unique_index_for_active(self) -> None:
        src = _migration_source()
        # Active snapshot per (provider, model) is the row with valid_to IS NULL.
        # Partial unique index keeps the resolver fast and prevents drift.
        assert re.search(
            r"CREATE UNIQUE INDEX IF NOT EXISTS ix_pricing_active[\s\S]+"
            r"WHERE valid_to IS NULL",
            src,
        )

    def test_lookup_index(self) -> None:
        src = _migration_source()
        assert "CREATE INDEX IF NOT EXISTS ix_pricing_lookup" in src


class TestTenantBillingConfigTable:
    def test_create_table_idempotent(self) -> None:
        src = _migration_source()
        assert "CREATE TABLE IF NOT EXISTS tenant_billing_config" in src

    def test_required_columns_and_defaults(self) -> None:
        src = _migration_source()
        required = [
            "tenant_id UUID PRIMARY KEY",
            "billing_cycle_anchor_day SMALLINT NOT NULL DEFAULT 25",
            "billing_currency CHAR(3) NOT NULL DEFAULT 'USD'",
            "fx_source VARCHAR(32) NOT NULL DEFAULT 'frankfurter'",
            "flat_fee_amount NUMERIC(14,2)",
            "cost_alert_threshold_usd NUMERIC(14,2)",
            "notes TEXT",
            "updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        ]
        for column in required:
            assert column in src, f"Missing column declaration: {column}"


class TestDowngradeIsIdempotent:
    def test_downgrade_uses_drop_if_exists(self) -> None:
        src = _migration_source()
        # Order doesn't matter; just confirm idempotent drops are emitted.
        for stmt in (
            "DROP TABLE IF EXISTS copilot_llm_call",
            "DROP TABLE IF EXISTS model_pricing_snapshot",
            "DROP TABLE IF EXISTS tenant_billing_config",
        ):
            assert stmt in src, f"Missing idempotent drop: {stmt}"
