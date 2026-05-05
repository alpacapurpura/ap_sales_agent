"""Repair historical mis-tagged provider rows in model_pricing_snapshot.

PI-12 S1 story ``sales-agent-litellm-canonicalization`` ticket T-3.

Background
----------
T-1 (cost_recorder) introduced canonical provider derivation via
``litellm.get_llm_provider(model)`` which returns the correct provider name
for models like ``kimi/kimi-k2.6`` → provider ``kimi``. Historical rows
in ``model_pricing_snapshot`` were mis-tagged with ``provider='openai'``
for models that belong to other providers: deepseek, kimi/moonshot, and
qwen/dashscope.

T-2 (sync-pricing) extended ``litellm_sync.py`` with drift detection to
prevent future mis-tagging. T-3 (this migration) repairs the historical
backlog.

Migration strategy
------------------
1. **Backup first (idempotent):** DROP TABLE IF EXISTS the backup table,
   then CREATE TABLE ... AS SELECT * to snapshot the pre-repair state.
   This pattern (``*_backup_pre_tN``) is the established convention for
   future T-6a/T-6c migrations to follow.
2. **Repair UPDATEs (self-idempotent):** Three UPDATE statements, each
   bounded by ``WHERE provider = 'openai' AND model LIKE '<prefix>%'``.
   Because WHERE matches ``provider='openai'`` only, rows already re-tagged
   to their canonical provider won't match on a second upgrade run.
3. **Downgrade (restore):** TRUNCATE the table, INSERT all rows from backup,
   DROP the backup.

Decisions honored
-----------------
- T-1 Decision A1 BINDING: ``model`` field stored slashed (``provider/model``
  format). UPDATE uses ``CASE WHEN model LIKE 'deepseek/%' THEN model ELSE
  'deepseek/' || model END`` to handle legacy unslashed rows while preserving
  already-slashed ones.
- T-1 Decision X2 BINDING: ``calculate_cost()`` retained as reconciliation
  utility; consumes repaired snapshot rows post-T3 repair.
- T-2 Decision A5 BINDING: ``litellm_sync.py`` EXTENDS only; T-3 is the
  one-shot historical repair that precedes future drift detection.

Provider canonicalization targets
----------------------------------
- ``provider='openai' AND model LIKE 'deepseek%'`` → ``provider='deepseek'``
- ``provider='openai' AND (model LIKE 'kimi%' OR model LIKE 'moonshot%')``
  → ``provider='kimi'``
- ``provider='openai' AND model LIKE 'qwen%'`` → ``provider='dashscope'``
  (dashscope is litellm's canonical name for Qwen/Alimama models)

Idempotency guarantee
---------------------
- Backup step: DROP IF EXISTS + CTAS → always fresh backup, no 'table exists' error.
- UPDATE steps: WHERE-bounded to ``provider='openai'`` → re-run is a no-op
  because rows already re-tagged won't match.
- Downgrade: DELETE + INSERT FROM backup → deterministic restore.

Quality gates
-------------
- A1: 2x upgrade runs without error (DROP IF EXISTS idempotency).
- A2: Post-upgrade SELECT COUNT WHERE provider='openai' AND model LIKE
  'deepseek%'/'kimi%'/'qwen%'/'moonshot%' returns 0.
- A3: Backup table ``model_pricing_snapshot_backup_pre_t3`` exists with
  original row count preserved.
- A4: Downgrade restores backup state; table returns to pre-repair shape.

Revision ID: 122_repair_pricing_snapshot_provider_tagging
Revises: 121_leads_deleted_at
Create Date: 2026-05-05
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "122_repair_pricing_snapshot_provider_tagging"
down_revision: str | None = "121_leads_deleted_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Repair mis-tagged provider rows in model_pricing_snapshot.

    Step 1: Create backup table (idempotent via DROP IF EXISTS + CTAS).
    Step 2: Re-tag deepseek rows.
    Step 3: Re-tag kimi/moonshot rows.
    Step 4: Re-tag qwen/dashscope rows.
    """
    # ── Step 1: Backup (idempotent) ─────────────────────────────────────────
    # DROP IF EXISTS ensures re-run is safe (no 'table already exists' error).
    # Convention ``*_backup_pre_tN`` established here for T-6a/T-6c to follow.
    op.execute("DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3")
    op.execute("CREATE TABLE model_pricing_snapshot_backup_pre_t3 AS SELECT * FROM model_pricing_snapshot")

    # ── Step 2: Repair deepseek rows ─────────────────────────────────────────
    # Targets rows mis-tagged as 'openai' where model prefix reveals deepseek.
    # CASE WHEN preserves already-slashed models (T-1 Decision A1 BINDING).
    # WHERE provider='openai' makes this self-idempotent on re-run.
    op.execute(
        """
        UPDATE model_pricing_snapshot
        SET
            provider = 'deepseek',
            model = CASE
                WHEN model LIKE 'deepseek/%' THEN model
                ELSE 'deepseek/' || model
            END
        WHERE
            provider = 'openai'
            AND (model LIKE 'deepseek%' OR model LIKE 'deepseek/%')
        """
    )

    # ── Step 3: Repair kimi/moonshot rows ────────────────────────────────────
    # kimi and moonshot (legacy alias) map to provider 'kimi' in LiteLLM.
    # CASE WHEN preserves already-slashed 'kimi/' prefix.
    op.execute(
        """
        UPDATE model_pricing_snapshot
        SET
            provider = 'kimi',
            model = CASE
                WHEN model LIKE 'kimi/%' THEN model
                WHEN model LIKE 'moonshot/%' THEN 'kimi/' || SUBSTRING(model FROM LENGTH('moonshot/') + 1)
                ELSE 'kimi/' || model
            END
        WHERE
            provider = 'openai'
            AND (model LIKE 'kimi%' OR model LIKE 'moonshot%')
        """
    )

    # ── Step 4: Repair qwen/dashscope rows ───────────────────────────────────
    # LiteLLM's canonical provider for Qwen (Alibaba/Alimama) is 'dashscope'.
    # CASE WHEN preserves already-slashed 'dashscope/' or 'qwen/' prefix.
    op.execute(
        """
        UPDATE model_pricing_snapshot
        SET
            provider = 'dashscope',
            model = CASE
                WHEN model LIKE 'dashscope/%' THEN model
                WHEN model LIKE 'qwen/%' THEN model
                ELSE 'dashscope/' || model
            END
        WHERE
            provider = 'openai'
            AND model LIKE 'qwen%'
        """
    )


def downgrade() -> None:
    """Restore model_pricing_snapshot from backup table.

    TRUNCATE current (repaired) state, INSERT all rows from backup,
    then DROP the backup table.

    Note: TRUNCATE is used for atomicity + speed on small snapshot table
    (~100-500 rows). If a row-by-row restore is required for safety, use
    DELETE FROM model_pricing_snapshot instead.
    """
    # Clear repaired rows
    op.execute("TRUNCATE model_pricing_snapshot")

    # Restore from backup
    op.execute("INSERT INTO model_pricing_snapshot SELECT * FROM model_pricing_snapshot_backup_pre_t3")

    # Drop backup table
    op.execute("DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3")
