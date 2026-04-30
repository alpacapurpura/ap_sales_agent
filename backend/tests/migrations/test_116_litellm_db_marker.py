"""Migration 116 idempotency test (S3 PR-2 PI-2).

Verifies ``116_litellm_db_marker`` upgrade runs idempotently — running twice
must not raise. Catches DuplicateDatabaseError silently per migration design.

D-1: separate database ``visionarias_litellm_db`` for LiteLLM Proxy
Prisma migrations isolation from Alembic Nicolify.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_migration_module():
    """Load 116 migration file as Python module without alembic env."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    migration_path = repo_root / "alembic" / "versions" / "116_litellm_db_marker.py"
    spec = importlib.util.spec_from_file_location("migration_116", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_116_revision_metadata() -> None:
    """Migration declares correct revision + down_revision."""
    module = _load_migration_module()
    assert module.revision == "116_litellm_db_marker"
    assert module.down_revision == "115_routing_log_tier_to_role"


def test_migration_116_upgrade_creates_database() -> None:
    """upgrade() executes COMMIT + CREATE DATABASE statements."""
    module = _load_migration_module()
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        module.upgrade()

    assert "COMMIT" in executed
    assert any("CREATE DATABASE visionarias_litellm_db" in s for s in executed)


def test_migration_116_upgrade_idempotent_when_db_exists() -> None:
    """upgrade() catches 'already exists' error silently."""
    module = _load_migration_module()

    def fake_execute(sql: str) -> None:
        if "CREATE DATABASE" in sql:
            err_msg = "database 'visionarias_litellm_db' already exists"
            raise RuntimeError(err_msg)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        # Must NOT raise.
        module.upgrade()


def test_migration_116_upgrade_propagates_unknown_errors() -> None:
    """upgrade() re-raises exceptions other than 'already exists'."""
    module = _load_migration_module()

    def fake_execute(sql: str) -> None:
        if "CREATE DATABASE" in sql:
            err_msg = "permission denied for postgres user"
            raise RuntimeError(err_msg)

    with patch.object(module.op, "execute", side_effect=fake_execute):
        raised = False
        try:
            module.upgrade()
        except RuntimeError as e:
            raised = True
            assert "permission denied" in str(e)
        assert raised, "upgrade() should have raised permission denied"


def test_migration_116_downgrade_is_no_op() -> None:
    """downgrade() is intentional no-op (safety guard)."""
    module = _load_migration_module()
    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.downgrade()
    mock_op.execute.assert_not_called()
