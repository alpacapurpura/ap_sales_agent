"""Deprecate tenant provider API keys (Phase 1 expand-contract).

PI-12 S1 story ``sales-agent-litellm-canonicalization`` ticket T-6a.

Background
----------
Nicolify model: company pays the master LLM key (LiteLLM Proxy resolves
credentials via ``litellm_config.yaml``). Tenants do NOT provide keys.
Post-T-5 the ``LITELLM_PROXY_ENABLED`` flag is gone and all dispatch
flows through the proxy regardless of the tenant key columns. Therefore
the per-tenant key columns

    openai_api_key, deepseek_api_key, kimi_api_key, dashscope_api_key

are unused dead data.

T-6a is **Phase 1** of a Stripe-style expand-contract deprecation:

1. **Phase 1 (this migration):** NULL the 4 deprecated columns; mark
   Pydantic fields ``deprecated=True`` + ``exclude=True``; remove writes
   from the repository; DELETE the orphaned ``LLMFactory._extract_tenant_key``
   helper.
2. **Phase 2 (T-6b — operational gate):** observe zero reads for ≥1
   working day in prod via structured logs.
3. **Phase 3 (T-6c):** physically ``DROP COLUMN`` the 4 cols.

``gemini_api_key`` is **out of scope** per architect 03-arch-be.md §2.4
(Q4 ratification): it remains active because it is still consumed by
landing extractors that bypass the LiteLLM Proxy.

Migration strategy
------------------
1. **Backup first (idempotent):** DROP TABLE IF EXISTS the backup table,
   then CREATE TABLE ... AS SELECT to snapshot the pre-NULL state. Backup
   table named ``tenants_api_keys_backup_pre_t6a`` per the
   ``*_backup_pre_tN`` convention established in T-3
   (``122_repair_pricing_snapshot_provider_tagging.py``).
2. **NULL UPDATE (self-idempotent):** A single UPDATE statement bounded
   by ``WHERE openai_api_key IS NOT NULL OR ... IS NOT NULL``. Because
   the WHERE clause matches non-null rows only, a re-run after the first
   apply matches zero rows (no-op).
3. **Downgrade no-op:** Cannot restore ephemeral keys once NULLed
   (the DB column still exists; the data is gone). Architect contract
   per 04-tickets.yaml T-6a deliverables: ``downgrade no-op (cannot
   restore ephemeral keys)``. The backup table is preserved by the
   downgrade so an operator may audit pre-NULL state if forensic review
   is required; T-6c removes the backup as part of physical column drop.

Decisions honored
-----------------
- Architect 03-arch-be.md §2.4 BINDING: 4 cols deprecated,
  ``gemini_api_key`` retained (Q4 ratification).
- Architect 03-arch-be.md §3.2 BINDING: response DTO drops 4 fields.
- Auditor T-5 review BINDING: ``_extract_tenant_key`` is orphaned
  post-T-5; delete now in T-6a (originally T-6c, accelerated per
  zero-tech-debt directive).
- T-3 BINDING: ``*_backup_pre_tN`` convention applied —
  backup table = ``tenants_api_keys_backup_pre_t6a``.

Idempotency guarantee
---------------------
- Backup step: DROP IF EXISTS + CTAS → always fresh backup, no
  'table already exists' error on re-run.
- UPDATE step: WHERE-bounded to non-null cols → re-run is a no-op
  (rows already NULLed do not match the predicate).
- Downgrade: no-op (does not restore data, does not error).

Quality gates
-------------
- A1: Post-upgrade ``SELECT COUNT(*) FROM tenants WHERE openai_api_key
  IS NOT NULL OR deepseek_api_key IS NOT NULL OR kimi_api_key IS NOT NULL
  OR dashscope_api_key IS NOT NULL`` returns 0.
- A4: 2x upgrade runs succeed without error (idempotency).

Revision ID: 123_deprecate_tenant_provider_api_keys
Revises: 122_repair_pricing_snapshot_provider_tagging
Create Date: 2026-05-05
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "123_deprecate_tenant_provider_api_keys"
down_revision: str | None = "122_repair_pricing_snapshot_provider_tagging"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """NULL deprecated tenant provider API key columns (Phase 1 expand-contract).

    Step 1: Backup table (idempotent via DROP IF EXISTS + CTAS) preserves
            pre-NULL state of the 4 deprecated cols (plus tenant id) so
            operators can audit forensically during the operational gate
            window (T-6b) before the physical DROP COLUMN in T-6c.
    Step 2: UPDATE tenants SET 4 cols = NULL — bounded by WHERE non-null
            for self-idempotency (re-run matches zero rows).
    """
    # ── Step 1: Backup (idempotent) ────────────────────────────────────────
    # DROP IF EXISTS guards re-run from 'table already exists' errors.
    # Convention ``*_backup_pre_tN`` from T-3 (122_repair_pricing_snapshot).
    # Backup includes only the relevant cols (id + 4 deprecated) — slim
    # snapshot since tenants table has many unrelated columns.
    op.execute("DROP TABLE IF EXISTS tenants_api_keys_backup_pre_t6a")
    op.execute(
        """
        CREATE TABLE tenants_api_keys_backup_pre_t6a AS
        SELECT
            id,
            openai_api_key,
            deepseek_api_key,
            kimi_api_key,
            dashscope_api_key
        FROM tenants
        WHERE
            openai_api_key IS NOT NULL
            OR deepseek_api_key IS NOT NULL
            OR kimi_api_key IS NOT NULL
            OR dashscope_api_key IS NOT NULL
        """
    )

    # ── Step 2: NULL the 4 deprecated columns (self-idempotent) ────────────
    # WHERE clause matches only rows with at least one non-null deprecated
    # col; on re-run after Phase 1 apply, all rows are already NULL → 0
    # rows match → no-op, no error. ``gemini_api_key`` is intentionally
    # untouched (out of scope per arch §2.4 — still active).
    op.execute(
        """
        UPDATE tenants
        SET
            openai_api_key = NULL,
            deepseek_api_key = NULL,
            kimi_api_key = NULL,
            dashscope_api_key = NULL
        WHERE
            openai_api_key IS NOT NULL
            OR deepseek_api_key IS NOT NULL
            OR kimi_api_key IS NOT NULL
            OR dashscope_api_key IS NOT NULL
        """
    )


def downgrade() -> None:
    """No-op downgrade — cannot restore ephemeral API keys.

    Per architect 03-arch-be.md §2.4 + 04-tickets.yaml T-6a deliverables:
    ``downgrade no-op (cannot restore ephemeral keys)``.

    Rationale: the per-tenant API keys are sensitive credentials that
    were already deprecated at the architect level (Q4 ratification —
    company pays master key). Restoring them on a downgrade would
    re-expose stale credentials that may have been rotated by the
    customer in the meantime, creating a security risk worse than the
    schema regression. The backup table is left in place so operators
    may forensically audit pre-NULL state until T-6c drops it as part
    of the physical DROP COLUMN cleanup.

    This function intentionally executes zero SQL statements. If you
    need to recover a specific tenant's keys, query
    ``tenants_api_keys_backup_pre_t6a`` directly.
    """
    # No-op. See docstring for rationale.
    return
