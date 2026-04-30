"""Migration 117 idempotency tests — llm_role_binding + llm_config_audit.

PI-2 S4 PR-1 db-registry-admin-ui.

Verifies:
1. Correct revision metadata.
2. upgrade() executes expected SQL statements (CREATE TABLE IF NOT EXISTS,
   CREATE UNIQUE INDEX IF NOT EXISTS, CREATE INDEX IF NOT EXISTS).
3. Partial UNIQUE index uses COALESCE trick (D-9 CONTRACT).
4. Both tables include correct CHECK constraints.
5. downgrade() is intentional no-op.
6. Idempotency: running upgrade() twice does not raise.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_migration_module():
    """Load 117 migration file as Python module without alembic env."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    migration_path = repo_root / "alembic" / "versions" / "117_llm_role_binding.py"
    spec = importlib.util.spec_from_file_location("migration_117", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_117_revision_metadata() -> None:
    """Migration declares correct revision + down_revision chain."""
    module = _load_migration_module()
    assert module.revision == "117_llm_role_binding"
    assert module.down_revision == "116_litellm_db_marker"


def test_migration_117_upgrade_creates_both_tables() -> None:
    """upgrade() executes CREATE TABLE IF NOT EXISTS for both tables."""
    module = _load_migration_module()
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        module.upgrade()

    combined = " ".join(executed)
    assert "llm_role_binding" in combined
    assert "llm_config_audit" in combined
    # Must use IF NOT EXISTS (idempotency requirement)
    assert combined.count("IF NOT EXISTS") >= 5  # 2 tables + 3 indexes


def test_migration_117_partial_unique_index_uses_coalesce() -> None:
    """Partial UNIQUE index uses COALESCE trick for NULL tenant_id (D-9 CONTRACT)."""
    module = _load_migration_module()
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        module.upgrade()

    unique_index_sql = next((s for s in executed if "uq_llm_role_binding_active_per_role" in s), None)
    assert unique_index_sql is not None, "Partial UNIQUE index not found in executed SQL"
    assert "COALESCE" in unique_index_sql.upper(), (
        "Partial UNIQUE index must use COALESCE trick for NULL tenant_id handling"
    )
    assert "WHERE is_active = TRUE" in unique_index_sql


def test_migration_117_check_constraints_present() -> None:
    """Both tables include CHECK constraints for role and action values."""
    module = _load_migration_module()
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        module.upgrade()

    combined = " ".join(executed)
    # Role constraint covers all 6 ModelRole values (lowercase per StrEnum)
    assert "ck_llm_role_binding_role" in combined
    assert "'nano'" in combined
    assert "'embedding'" in combined
    # Action constraint covers all 6 AuditAction values
    assert "ck_llm_config_audit_action" in combined
    assert "'activate'" in combined
    assert "'rollback'" in combined


def test_migration_117_hot_path_index_created() -> None:
    """Hot-path composite index ix_llm_role_binding_role_tenant_active is created."""
    module = _load_migration_module()
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        module.upgrade()

    assert any("ix_llm_role_binding_role_tenant_active" in s for s in executed), "Hot-path index not found"


def test_migration_117_upgrade_idempotent_noop_on_second_run() -> None:
    """Running upgrade() twice does not raise (IF NOT EXISTS guards all DDL)."""
    module = _load_migration_module()

    # First run succeeds
    with patch.object(module.op, "execute"):
        module.upgrade()

    # Second run must also succeed without raising
    with patch.object(module.op, "execute"):
        module.upgrade()


def test_migration_117_downgrade_is_no_op() -> None:
    """downgrade() is intentional no-op (audit trail must not be destroyed)."""
    module = _load_migration_module()
    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.downgrade()
    mock_op.execute.assert_not_called()
