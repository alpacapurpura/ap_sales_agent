"""Migration T-3 — repair model_pricing_snapshot mis-tagged provider rows.

TDD phase 1 (RED): Tests for acceptance criteria A1-A4.

Acceptance criteria:
    A1: Migration applies idempotent (running 2x without error)
    A2: Post-upgrade, mis-tagged rows count = 0
    A3: Backup table exists with original row count preserved
    A4: Downgrade restores backup state

Test strategy: mock-based (patch op.execute) following the established
pattern in this repo (see test_116_litellm_db_marker.py, test_119_llm_eval_gate.py).
No real DB required — SQL correctness is verified at upgrade/downgrade call time
by inspecting the SQL strings passed to op.execute().

Decisions honored:
    - T-1 A1 BINDING: model field stored slashed — UPDATE CASE WHEN preserves slashed models
    - T-1 X2 BINDING: calculate_cost reconciliation utility consumes repaired data
    - T-2 A5 BINDING: litellm_sync.py extends only; T-3 is one-shot historical repair
    - T-3: backup table mandatory + downgrade restores from backup

Backup table naming convention: ``model_pricing_snapshot_backup_pre_t3``
This convention (``*_backup_pre_tN``) is established here for future
T-6a/T-6c migrations to follow.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch


def _load_migration_module():
    """Load T-3 migration file as Python module without alembic env."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    migration_path = repo_root / "alembic" / "versions" / "122_repair_pricing_snapshot_provider_tagging.py"
    spec = importlib.util.spec_from_file_location("migration_122_repair_pricing_snapshot", migration_path)
    assert spec is not None and spec.loader is not None, (
        f"Migration file not found at {migration_path}. Run Phase 2 GREEN: create the migration file first."
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── A1: Idempotency — migration structure supports 2x upgrade ─────────────────


def test_migration_122_revision_metadata() -> None:
    """Migration declares correct revision and down_revision chain."""
    module = _load_migration_module()
    assert module.revision == "122_repair_pricing_snapshot_provider_tagging"
    assert module.down_revision == "121_leads_deleted_at"


def test_migration_122_upgrade_creates_backup_idempotently() -> None:
    """upgrade() uses DROP TABLE IF EXISTS before CTAS — ensures idempotent backup.

    A1 acceptance: running 2x without error requires:
    - DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3
    - followed by CREATE TABLE model_pricing_snapshot_backup_pre_t3 AS SELECT

    The DROP IF EXISTS guard makes it safe to re-run without 'table already exists' error.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    sql_combined = "\n".join(executed)

    # Must DROP IF EXISTS before CTAS (ensures idempotency of backup step)
    assert "DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3" in sql_combined, (
        "upgrade() must DROP TABLE IF EXISTS backup table first for idempotency"
    )
    # Must create backup via CTAS
    assert "CREATE TABLE model_pricing_snapshot_backup_pre_t3" in sql_combined, (
        "upgrade() must create backup table via CTAS"
    )
    assert "SELECT * FROM model_pricing_snapshot" in sql_combined, "CTAS must copy all rows from model_pricing_snapshot"


# ── A2: No mis-tagged rows post-migration ────────────────────────────────────


def test_migration_122_repairs_deepseek_rows() -> None:
    """upgrade() contains UPDATE for deepseek mis-tagged rows.

    A2 acceptance: rows with provider='openai' AND model LIKE 'deepseek%'
    must be re-tagged to provider='deepseek'.

    T-1 A1 BINDING: model field stored slashed — CASE WHEN preserves existing
    slashed models, prepends 'deepseek/' only when not already slashed.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    deepseek_updates = [s for s in executed if "provider = 'deepseek'" in s and "model_pricing_snapshot" in s]
    assert len(deepseek_updates) >= 1, "upgrade() must UPDATE mis-tagged deepseek rows"

    # Verify WHERE clause restricts to provider='openai' rows only (idempotency bound)
    deepseek_sql = deepseek_updates[0]
    assert "provider = 'openai'" in deepseek_sql, "deepseek UPDATE WHERE must filter provider = 'openai' (idempotency)"
    # Verify CASE WHEN slashed preservation (T-1 Decision A1)
    assert "deepseek/" in deepseek_sql, "deepseek UPDATE must produce slashed model format per T-1 Decision A1"


def test_migration_122_repairs_kimi_rows() -> None:
    """upgrade() contains UPDATE for kimi/moonshot mis-tagged rows.

    A2 acceptance: rows with provider='openai' AND model LIKE 'kimi%' OR 'moonshot%'
    must be re-tagged to provider='kimi'.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    kimi_updates = [s for s in executed if "provider = 'kimi'" in s and "model_pricing_snapshot" in s]
    assert len(kimi_updates) >= 1, "upgrade() must UPDATE mis-tagged kimi/moonshot rows"

    kimi_sql = kimi_updates[0]
    assert "provider = 'openai'" in kimi_sql, "kimi UPDATE WHERE must filter provider = 'openai' (idempotency)"
    # Verify CASE WHEN slashed preservation
    assert "kimi/" in kimi_sql, "kimi UPDATE must produce slashed model format per T-1 Decision A1"


def test_migration_122_repairs_qwen_rows() -> None:
    """upgrade() contains UPDATE for qwen/dashscope mis-tagged rows.

    A2 acceptance: rows with provider='openai' AND model LIKE 'qwen%'
    must be re-tagged to provider='dashscope' (canonical per litellm).
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    qwen_updates = [s for s in executed if "provider = 'dashscope'" in s and "model_pricing_snapshot" in s]
    assert len(qwen_updates) >= 1, "upgrade() must UPDATE mis-tagged qwen rows to provider='dashscope'"

    qwen_sql = qwen_updates[0]
    assert "provider = 'openai'" in qwen_sql, "qwen UPDATE WHERE must filter provider = 'openai' (idempotency)"


def test_migration_122_no_mistagged_rows_post_migration() -> None:
    """upgrade() produces SQL that eliminates all three mis-tagged provider families.

    A2 acceptance: Combined check — deepseek + kimi + qwen all repaired.
    Verifies the migration covers all three pattern families from the spec.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    sql_combined = "\n".join(executed)

    # All three provider families must be addressed
    assert "provider = 'deepseek'" in sql_combined, "deepseek repair missing"
    assert "provider = 'kimi'" in sql_combined, "kimi repair missing"
    assert "provider = 'dashscope'" in sql_combined, "dashscope/qwen repair missing"

    # Each UPDATE must be WHERE-bounded to provider='openai' (self-idempotent)
    update_blocks = [s for s in executed if "UPDATE model_pricing_snapshot" in s]
    assert len(update_blocks) == 3, f"Expected 3 UPDATE statements (deepseek/kimi/qwen), got {len(update_blocks)}"
    for block in update_blocks:
        assert "provider = 'openai'" in block, (
            f"UPDATE not bounded to provider='openai' — not self-idempotent:\n{block}"
        )


# ── A3: Backup table preserves original row count ────────────────────────────


def test_migration_122_backup_table_preserves_original_state() -> None:
    """upgrade() creates backup table via CTAS before any UPDATE.

    A3 acceptance: backup table contains all original rows (pre-repair snapshot).

    The CTAS step (CREATE TABLE ... AS SELECT * FROM model_pricing_snapshot)
    must appear BEFORE any UPDATE statements in the execution sequence.
    This guarantees the backup captures the pre-repair state.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    # Find indices of CTAS and first UPDATE
    ctas_idx = next(
        (i for i, s in enumerate(executed) if "CREATE TABLE model_pricing_snapshot_backup_pre_t3" in s),
        None,
    )
    first_update_idx = next(
        (i for i, s in enumerate(executed) if "UPDATE model_pricing_snapshot" in s),
        None,
    )

    assert ctas_idx is not None, "CTAS backup must exist in upgrade()"
    assert first_update_idx is not None, "UPDATE repair must exist in upgrade()"
    assert ctas_idx < first_update_idx, (
        f"CTAS (idx={ctas_idx}) must precede first UPDATE (idx={first_update_idx}) to capture pre-repair state"
    )


# ── A4: Downgrade restores backup state ──────────────────────────────────────


def test_migration_122_downgrade_restores_backup() -> None:
    """downgrade() restores from backup table.

    A4 acceptance: downgrade must TRUNCATE/DELETE the repaired table
    and restore from backup, then DROP the backup.

    Verifies the downgrade SQL references:
    - DELETE or TRUNCATE of model_pricing_snapshot
    - INSERT from model_pricing_snapshot_backup_pre_t3
    - DROP TABLE backup cleanup
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.downgrade()

    sql_combined = "\n".join(executed)

    # Must clear current repaired rows
    assert "TRUNCATE model_pricing_snapshot" in sql_combined or "DELETE FROM model_pricing_snapshot" in sql_combined, (
        "downgrade() must clear current (repaired) rows"
    )

    # Must restore from backup
    assert "model_pricing_snapshot_backup_pre_t3" in sql_combined, (
        "downgrade() must reference backup table to restore data"
    )
    assert "INSERT INTO model_pricing_snapshot" in sql_combined, (
        "downgrade() must INSERT rows from backup to restore state"
    )

    # Must clean up backup table
    assert (
        "DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3" in sql_combined
        or "DROP TABLE model_pricing_snapshot_backup_pre_t3" in sql_combined
    ), "downgrade() must drop backup table after restore"


def test_migration_122_downgrade_uses_backup_source() -> None:
    """downgrade() SELECT source is the backup table.

    Verifies the INSERT ... SELECT reads FROM backup table specifically.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.downgrade()

    insert_statements = [s for s in executed if "INSERT INTO model_pricing_snapshot" in s]
    assert len(insert_statements) >= 1, "downgrade() must INSERT restored rows"

    # The INSERT must read from the backup table
    insert_sql = insert_statements[0]
    assert "model_pricing_snapshot_backup_pre_t3" in insert_sql, "INSERT restore must SELECT FROM backup table"


# ── Bonus: Structural validation ─────────────────────────────────────────────


def test_migration_122_upgrade_statement_order() -> None:
    """upgrade() executes statements in correct order: DROP backup, CTAS, then UPDATEs."""
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    assert len(executed) >= 5, f"Expected at least 5 SQL statements (DROP, CTAS, 3×UPDATE), got {len(executed)}"

    # Index of DROP IF EXISTS backup
    drop_idx = next(
        (i for i, s in enumerate(executed) if "DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3" in s),
        None,
    )
    # Index of CTAS
    ctas_idx = next(
        (i for i, s in enumerate(executed) if "CREATE TABLE model_pricing_snapshot_backup_pre_t3" in s),
        None,
    )
    assert drop_idx is not None, "DROP TABLE IF EXISTS backup must be present"
    assert ctas_idx is not None, "CTAS backup must be present"
    assert drop_idx < ctas_idx, "DROP must precede CTAS"
