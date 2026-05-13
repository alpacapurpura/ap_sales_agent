"""Migration 125 idempotency test — eval_simulator observability tables.

Story B: eval-foundation-simulator-homologation.
T-2 deliverable (test-infrastructure, production_code=false).

Verifies that migration ``125_add_eval_simulator_observability_tables``:

1. upgrade() emits CREATE TABLE IF NOT EXISTS for 3 tables.
2. upgrade() emits CREATE INDEX IF NOT EXISTS for 6 indexes.
3. Spec registration works (get_spec('eval_simulator') non-None) after bootstrap import.
4. downgrade() emits DROP TABLE IF EXISTS for all 3 tables.
5. Running upgrade() twice (idempotency) does NOT raise — IF NOT EXISTS guards hold.

All tests operate by patching ``op.execute`` with a side-effect collector; no live
Postgres connection is required (pre-prod clone workflow lives in integration tests).

Pattern precedent: ``tests/migrations/test_119_llm_eval_gate.py``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch


# ── Helpers ───────────────────────────────────────────────────────────────


def _load_migration_module():
    """Load migration 125 as a Python module without Alembic env active."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    migration_path = repo_root / "alembic" / "versions" / "125_add_eval_simulator_observability_tables.py"
    spec = importlib.util.spec_from_file_location("migration_125", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ── Revision metadata ─────────────────────────────────────────────────────


class TestRevisionMetadata:
    """Migration declares correct revision chain."""

    def test_revision_id(self) -> None:
        """Revision ID matches T-1 deliverable name."""
        module = _load_migration_module()
        assert module.revision == "125_add_eval_simulator_observability_tables"

    def test_down_revision(self) -> None:
        """down_revision points to previous migration (T-1 note: renamed 124→125 due to collision)."""
        module = _load_migration_module()
        assert module.down_revision == "124_drop_tenant_provider_api_keys"


# ── Tables created on upgrade ──────────────────────────────────────────────


class TestUpgradeCreatesTables:
    """upgrade() emits CREATE TABLE IF NOT EXISTS for the 3 eval tables."""

    def _collect_upgrade_sql(self) -> list[str]:
        module = _load_migration_module()
        executed: list[str] = []
        with patch.object(module.op, "execute", side_effect=executed.append):
            module.upgrade()
        return executed

    def test_creates_eval_simulator_llm_call(self) -> None:
        """upgrade() creates eval_simulator_llm_call table."""
        executed = self._collect_upgrade_sql()
        assert any("CREATE TABLE IF NOT EXISTS eval_simulator_llm_call" in s for s in executed)

    def test_creates_eval_simulator_trace_event(self) -> None:
        """upgrade() creates eval_simulator_trace_event table."""
        executed = self._collect_upgrade_sql()
        assert any("CREATE TABLE IF NOT EXISTS eval_simulator_trace_event" in s for s in executed)

    def test_creates_eval_synthetic_tenants(self) -> None:
        """upgrade() creates eval_synthetic_tenants table."""
        executed = self._collect_upgrade_sql()
        assert any("CREATE TABLE IF NOT EXISTS eval_synthetic_tenants" in s for s in executed)

    def test_creates_exactly_three_tables(self) -> None:
        """upgrade() creates exactly 3 tables — no extras."""
        executed = self._collect_upgrade_sql()
        table_creates = [s for s in executed if "CREATE TABLE IF NOT EXISTS" in s]
        assert len(table_creates) == 3, (
            f"Expected exactly 3 CREATE TABLE IF NOT EXISTS statements, got {len(table_creates)}: "
            f"{[s[:60] for s in table_creates]}"
        )


# ── Indexes created on upgrade ─────────────────────────────────────────────


class TestUpgradeCreatesIndexes:
    """upgrade() emits CREATE INDEX IF NOT EXISTS for all 7 required indexes.

    4 on eval_simulator_llm_call + 2 on eval_simulator_trace_event + 1 on eval_synthetic_tenants.
    """

    def _collect_upgrade_sql(self) -> list[str]:
        module = _load_migration_module()
        executed: list[str] = []
        with patch.object(module.op, "execute", side_effect=executed.append):
            module.upgrade()
        return executed

    def test_creates_llm_call_tenant_day_index(self) -> None:
        """Index ix_eval_simulator_llm_call_tenant_day on (tenant_id, occurred_on)."""
        executed = self._collect_upgrade_sql()
        assert any("ix_eval_simulator_llm_call_tenant_day" in s for s in executed)

    def test_creates_llm_call_turn_index(self) -> None:
        """Index ix_eval_simulator_llm_call_turn on (turn_id)."""
        executed = self._collect_upgrade_sql()
        assert any("ix_eval_simulator_llm_call_turn" in s for s in executed)

    def test_creates_llm_call_sim_id_index(self) -> None:
        """Index ix_eval_simulator_llm_call_sim_id on (eval_metadata->>'simulation_id')."""
        executed = self._collect_upgrade_sql()
        assert any("ix_eval_simulator_llm_call_sim_id" in s for s in executed)

    def test_creates_llm_call_run_id_index(self) -> None:
        """Index ix_eval_simulator_llm_call_run_id on (eval_metadata->>'run_id')."""
        executed = self._collect_upgrade_sql()
        assert any("ix_eval_simulator_llm_call_run_id" in s for s in executed)

    def test_creates_trace_event_tenant_turn_index(self) -> None:
        """Index ix_eval_simulator_trace_event_tenant_turn on (tenant_id, turn_id, created_at)."""
        executed = self._collect_upgrade_sql()
        assert any("ix_eval_simulator_trace_event_tenant_turn" in s for s in executed)

    def test_creates_trace_event_sim_id_index(self) -> None:
        """Index ix_eval_simulator_trace_event_sim_id on (eval_metadata->>'simulation_id')."""
        executed = self._collect_upgrade_sql()
        assert any("ix_eval_simulator_trace_event_sim_id" in s for s in executed)

    def test_creates_synthetic_tenants_slug_index(self) -> None:
        """Index ix_eval_synthetic_tenants_slug on (archetype_slug) WHERE deleted_at IS NULL."""
        executed = self._collect_upgrade_sql()
        assert any("ix_eval_synthetic_tenants_slug" in s for s in executed)

    def test_creates_exactly_seven_indexes(self) -> None:
        """upgrade() creates exactly 7 indexes — architecture spec gate.

        4 on eval_simulator_llm_call (tenant_day, turn, sim_id, run_id)
        + 2 on eval_simulator_trace_event (tenant_turn, sim_id)
        + 1 on eval_synthetic_tenants (slug partial, where deleted_at IS NULL)
        = 7 total.
        """
        executed = self._collect_upgrade_sql()
        index_creates = [s for s in executed if "CREATE INDEX IF NOT EXISTS" in s]
        assert len(index_creates) == 7, (
            f"Expected exactly 7 CREATE INDEX IF NOT EXISTS statements, got {len(index_creates)}: "
            f"{[s[:80] for s in index_creates]}"
        )


# ── Schema shape invariants ────────────────────────────────────────────────


class TestUpgradeSchemaShape:
    """Verify key schema invariants baked into the migration DDL."""

    def _collect_upgrade_sql(self) -> list[str]:
        module = _load_migration_module()
        executed: list[str] = []
        with patch.object(module.op, "execute", side_effect=executed.append):
            module.upgrade()
        return executed

    def _llm_call_ddl(self) -> str:
        executed = self._collect_upgrade_sql()
        return next(s for s in executed if "CREATE TABLE IF NOT EXISTS eval_simulator_llm_call" in s)

    def _trace_event_ddl(self) -> str:
        executed = self._collect_upgrade_sql()
        return next(s for s in executed if "CREATE TABLE IF NOT EXISTS eval_simulator_trace_event" in s)

    def _synthetic_tenants_ddl(self) -> str:
        executed = self._collect_upgrade_sql()
        return next(s for s in executed if "CREATE TABLE IF NOT EXISTS eval_synthetic_tenants" in s)

    def test_llm_call_has_tenant_id(self) -> None:
        """eval_simulator_llm_call.tenant_id NOT NULL (tenant isolation)."""
        ddl = self._llm_call_ddl()
        assert "tenant_id UUID NOT NULL" in ddl

    def test_llm_call_has_eval_metadata_jsonb(self) -> None:
        """eval_simulator_llm_call.eval_metadata JSONB NOT NULL (H5 mandatory tags)."""
        ddl = self._llm_call_ddl()
        assert "eval_metadata JSONB NOT NULL" in ddl

    def test_llm_call_lead_id_nullable(self) -> None:
        """eval_simulator_llm_call.lead_id is NULL (eval has no per-lead audit rows)."""
        ddl = self._llm_call_ddl()
        assert "lead_id UUID NULL" in ddl

    def test_llm_call_cost_usd_nullable(self) -> None:
        """eval_simulator_llm_call.cost_usd NULL allowed (parity migration 086)."""
        ddl = self._llm_call_ddl()
        assert "cost_usd NUMERIC(16,10) NULL" in ddl

    def test_llm_call_has_started_at_timestamptz(self) -> None:
        """eval_simulator_llm_call.started_at TIMESTAMPTZ (timezone-aware, no naive datetime)."""
        ddl = self._llm_call_ddl()
        assert "started_at TIMESTAMPTZ NOT NULL" in ddl

    def test_trace_event_has_eval_metadata_jsonb(self) -> None:
        """eval_simulator_trace_event.eval_metadata JSONB NOT NULL (H5 mandatory tags)."""
        ddl = self._trace_event_ddl()
        assert "eval_metadata JSONB NOT NULL" in ddl

    def test_trace_event_has_tenant_id(self) -> None:
        """eval_simulator_trace_event.tenant_id NOT NULL (tenant isolation)."""
        ddl = self._trace_event_ddl()
        assert "tenant_id UUID NOT NULL" in ddl

    def test_trace_event_has_created_at_timestamptz(self) -> None:
        """eval_simulator_trace_event.created_at TIMESTAMPTZ (timezone-aware)."""
        ddl = self._trace_event_ddl()
        assert "created_at TIMESTAMPTZ NOT NULL" in ddl

    def test_synthetic_tenants_has_deleted_at(self) -> None:
        """eval_synthetic_tenants.deleted_at nullable (soft-delete for idempotent teardown)."""
        ddl = self._synthetic_tenants_ddl()
        assert "deleted_at TIMESTAMPTZ NULL" in ddl

    def test_synthetic_tenants_has_archetype_slug(self) -> None:
        """eval_synthetic_tenants.archetype_slug VARCHAR (correlates to Story A seeds)."""
        ddl = self._synthetic_tenants_ddl()
        assert "archetype_slug VARCHAR(64) NOT NULL" in ddl


# ── Idempotency (double upgrade) ───────────────────────────────────────────


class TestUpgradeIdempotency:
    """Running upgrade() twice must not raise (IF NOT EXISTS guards).

    This simulates the pre-prod clone workflow described in
    `.claude/rules/backend-migrations.md`: after stamping the prod revision
    on a clone, running upgrade head twice must be a no-op on the second pass.
    The raw SQL ``IF NOT EXISTS`` clauses on both CREATE TABLE and CREATE INDEX
    statements absorb the duplicate call without raising DuplicateTable errors.
    """

    def test_double_upgrade_does_not_raise(self) -> None:
        """Running upgrade() twice does not raise any exception."""
        module = _load_migration_module()

        # Simulate "tables already exist" on second call by having op.execute
        # succeed silently — IF NOT EXISTS means Postgres doesn't raise either.
        # The test verifies the Python code path does NOT raise before sending SQL.
        executed: list[str] = []
        with patch.object(module.op, "execute", side_effect=executed.append):
            module.upgrade()  # first run
            first_count = len(executed)

        executed2: list[str] = []
        with patch.object(module.op, "execute", side_effect=executed2.append):
            module.upgrade()  # second run — same SQL, should not raise
            second_count = len(executed2)

        # Both passes emit the same number of SQL statements.
        assert first_count == second_count, (
            "Second upgrade pass must emit same number of SQL statements as first. "
            f"First: {first_count}, second: {second_count}"
        )

    def test_upgrade_sql_uses_if_not_exists_for_tables(self) -> None:
        """Every CREATE TABLE statement uses IF NOT EXISTS guard."""
        module = _load_migration_module()
        executed: list[str] = []
        with patch.object(module.op, "execute", side_effect=executed.append):
            module.upgrade()

        table_creates = [s for s in executed if "CREATE TABLE" in s and "eval_" in s]
        for stmt in table_creates:
            assert "IF NOT EXISTS" in stmt, f"CREATE TABLE statement missing IF NOT EXISTS guard: {stmt[:100]}"

    def test_upgrade_sql_uses_if_not_exists_for_indexes(self) -> None:
        """Every CREATE INDEX statement uses IF NOT EXISTS guard."""
        module = _load_migration_module()
        executed: list[str] = []
        with patch.object(module.op, "execute", side_effect=executed.append):
            module.upgrade()

        index_creates = [s for s in executed if "CREATE INDEX" in s]
        for stmt in index_creates:
            assert "IF NOT EXISTS" in stmt, f"CREATE INDEX statement missing IF NOT EXISTS guard: {stmt[:100]}"


# ── Downgrade ──────────────────────────────────────────────────────────────


class TestDowngrade:
    """downgrade() drops all 3 tables with CASCADE, using IF EXISTS."""

    def _collect_downgrade_sql(self) -> list[str]:
        module = _load_migration_module()
        executed: list[str] = []
        with patch.object(module.op, "execute", side_effect=executed.append):
            module.downgrade()
        return executed

    def test_downgrade_drops_llm_call_table(self) -> None:
        """downgrade() drops eval_simulator_llm_call."""
        executed = self._collect_downgrade_sql()
        assert any("DROP TABLE IF EXISTS eval_simulator_llm_call" in s for s in executed)

    def test_downgrade_drops_trace_event_table(self) -> None:
        """downgrade() drops eval_simulator_trace_event."""
        executed = self._collect_downgrade_sql()
        assert any("DROP TABLE IF EXISTS eval_simulator_trace_event" in s for s in executed)

    def test_downgrade_drops_synthetic_tenants_table(self) -> None:
        """downgrade() drops eval_synthetic_tenants."""
        executed = self._collect_downgrade_sql()
        assert any("DROP TABLE IF EXISTS eval_synthetic_tenants" in s for s in executed)

    def test_downgrade_uses_cascade(self) -> None:
        """downgrade() includes CASCADE to handle FK deps without manual ordering."""
        executed = self._collect_downgrade_sql()
        drops_with_cascade = [s for s in executed if "DROP TABLE IF EXISTS" in s and "CASCADE" in s]
        assert len(drops_with_cascade) == 3, (
            f"All 3 DROP TABLE statements must include CASCADE. Found: {len(drops_with_cascade)}"
        )

    def test_downgrade_drops_exactly_three_tables(self) -> None:
        """downgrade() issues exactly 3 DROP TABLE statements."""
        executed = self._collect_downgrade_sql()
        drops = [s for s in executed if "DROP TABLE IF EXISTS" in s]
        assert len(drops) == 3


# ── Spec registration via bootstrap ───────────────────────────────────────


class TestSpecRegistration:
    """Verifies that importing the bootstrap module registers eval_simulator spec.

    This does NOT require a live DB — the registry is in-memory dict.
    Importing agent_observability_bootstrap triggers the chain:
      bootstrap.py → eval_simulator/spec.py → register_agent_observability(...)
    """

    def test_spec_registered_after_bootstrap_import(self) -> None:
        """get_spec('eval_simulator') returns a non-None spec after bootstrap import."""
        # The bootstrap import is idempotent (re-registering same key is allowed per registry).
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec is not None

    def test_spec_agent_kind_is_eval_simulator(self) -> None:
        """Registered spec.agent_kind == 'eval_simulator'."""
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec.agent_kind == "eval_simulator"

    def test_spec_llm_call_table_name(self) -> None:
        """Spec.llm_call_table matches the migration table name."""
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec.llm_call_table == "eval_simulator_llm_call"

    def test_spec_trace_event_table_name(self) -> None:
        """Spec.trace_event_table matches the migration table name."""
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec.trace_event_table == "eval_simulator_trace_event"

    def test_spec_has_lead_id_false(self) -> None:
        """Spec.has_lead_id is False — eval simulator does not write per-lead audit rows."""
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec.has_lead_id is False

    def test_spec_retention_defaults(self) -> None:
        """Spec retention defaults are 30 days (synthetic, no audit obligation)."""
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec.trace_default_days == 30
        assert spec.llm_call_default_days == 30
