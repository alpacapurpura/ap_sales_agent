"""Migration 118 idempotency tests — llm_role_binding seed from .env.

PI-2 S4 PR-1 db-registry-admin-ui.

Verifies:
1. Correct revision metadata and dependency chain.
2. upgrade() executes INSERT ... WHERE NOT EXISTS for each of the 6 roles.
3. Audit INSERT is also guarded by NOT EXISTS (no duplicate audit rows).
4. Idempotency: running upgrade() twice does not raise.
5. All 6 ModelRole values are seeded (nano, fast, reasoning, agent, vision, embedding).
6. downgrade() is intentional no-op.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_migration_module():
    """Load 118 migration file as Python module without alembic env."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    migration_path = repo_root / "alembic" / "versions" / "118_llm_role_binding_seed_from_env.py"
    spec = importlib.util.spec_from_file_location("migration_118", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_118_revision_metadata() -> None:
    """Migration declares correct revision + down_revision chain."""
    module = _load_migration_module()
    assert module.revision == "118_llm_role_binding_seed_from_env"
    assert module.down_revision == "117_llm_role_binding"


def test_migration_118_seeds_all_six_roles() -> None:
    """upgrade() inserts rows for all 6 ModelRole values."""
    module = _load_migration_module()
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        module.upgrade()

    combined = " ".join(executed)
    for role in ("nano", "fast", "reasoning", "agent", "vision", "embedding"):
        assert f"'{role}'" in combined, f"Role '{role}' not found in seeded SQL"


def test_migration_118_seed_inserts_are_conditional() -> None:
    """Each INSERT uses WHERE NOT EXISTS guard for idempotency."""
    module = _load_migration_module()
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        module.upgrade()

    # Each role generates 2 SQL calls (binding INSERT + audit INSERT).
    # Distinguish by the INSERT target table appearing at the start of the
    # statement (before any WHERE EXISTS sub-selects that may also reference
    # the other table).
    binding_inserts = [s for s in executed if "INSERT INTO llm_role_binding" in s]
    audit_inserts = [s for s in executed if "INSERT INTO llm_config_audit" in s]

    assert len(binding_inserts) == 6, f"Expected 6 binding inserts, got {len(binding_inserts)}"
    assert len(audit_inserts) == 6, f"Expected 6 audit inserts, got {len(audit_inserts)}"

    for sql in binding_inserts:
        assert "NOT EXISTS" in sql, "Binding INSERT must use NOT EXISTS guard"
    for sql in audit_inserts:
        assert "NOT EXISTS" in sql, "Audit INSERT must use NOT EXISTS guard"


def test_migration_118_actor_is_system_migration() -> None:
    """Seeded rows use 'system-migration-118' as actor."""
    module = _load_migration_module()
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        module.upgrade()

    combined = " ".join(executed)
    assert "system-migration-118" in combined


def test_migration_118_upgrade_idempotent_noop_on_second_run() -> None:
    """Running upgrade() twice does not raise."""
    module = _load_migration_module()

    with patch.object(module.op, "execute"):
        module.upgrade()

    with patch.object(module.op, "execute"):
        module.upgrade()


def test_migration_118_downgrade_is_no_op() -> None:
    """downgrade() is intentional no-op (seed data is part of audit trail)."""
    module = _load_migration_module()
    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.downgrade()
    mock_op.execute.assert_not_called()
