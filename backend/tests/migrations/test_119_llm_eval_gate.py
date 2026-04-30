"""Migration 119 idempotency + threshold seed tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch


def _load_migration_module():
    """Load 119 migration file as Python module."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    migration_path = repo_root / "alembic" / "versions" / "119_llm_eval_gate.py"
    spec = importlib.util.spec_from_file_location("migration_119", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_119_revision_metadata() -> None:
    """Migration declares correct revision + down_revision."""
    module = _load_migration_module()
    assert module.revision == "119_llm_eval_gate"
    assert module.down_revision == "118_llm_role_binding_seed_from_env"


def test_migration_119_creates_both_tables() -> None:
    """upgrade() executes CREATE TABLE for runs + threshold."""
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    has_runs = any("CREATE TABLE IF NOT EXISTS llm_eval_gate_runs" in s for s in executed)
    has_threshold = any("CREATE TABLE IF NOT EXISTS llm_eval_gate_threshold" in s for s in executed)
    assert has_runs
    assert has_threshold


def test_migration_119_seeds_six_thresholds() -> None:
    """upgrade() inserts 6 role thresholds (NANO..EMBEDDING)."""
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    insert_count = sum(1 for s in executed if "INSERT INTO llm_eval_gate_threshold" in s)
    assert insert_count == 6


def test_migration_119_seeds_use_on_conflict_do_nothing() -> None:
    """Seed inserts are idempotent via ON CONFLICT DO NOTHING."""
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    threshold_inserts = [s for s in executed if "INSERT INTO llm_eval_gate_threshold" in s]
    assert all("ON CONFLICT (role) DO NOTHING" in s for s in threshold_inserts)


def test_migration_119_default_thresholds_per_role() -> None:
    """Per CONTRACT §5: NANO=0.95, FAST=0.95, REASONING=0.93, AGENT=0.95, VISION=0.90, EMBEDDING=0.95."""
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    threshold_inserts = "\n".join(s for s in executed if "INSERT INTO llm_eval_gate_threshold" in s)

    # Spot-check each role threshold present.
    assert "'NANO', 0.95" in threshold_inserts
    assert "'FAST', 0.95" in threshold_inserts
    assert "'REASONING', 0.93" in threshold_inserts
    assert "'AGENT', 0.95" in threshold_inserts
    assert "'VISION', 0.90" in threshold_inserts
    assert "'EMBEDDING', 0.95" in threshold_inserts


def test_migration_119_downgrade_no_op() -> None:
    """downgrade() is intentional no-op (preserves audit)."""
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.downgrade()

    assert executed == []
