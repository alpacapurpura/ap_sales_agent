"""Drop tenant provider API keys (Phase 3 expand-contract — physical removal).

PI-12 S1 story ``sales-agent-litellm-canonicalization`` ticket T-6c.

Background
----------
Final phase of three-phase expand-contract migration:

1. **Phase 1 (T-6a — 123_deprecate_tenant_provider_api_keys):** NULLed
   the 4 deprecated cols + Pydantic ``deprecated=True, exclude=True`` +
   repo stops writes + ``LLMFactory._extract_tenant_key`` DELETED.
2. **Phase 2 (T-6b — operational gate, no code, PM-ratified
   2026-05-06 02:50Z pre-clientes per R7):** observed zero reads.
3. **Phase 3 (T-6c — this migration):** physically ``ALTER TABLE
   tenants DROP COLUMN IF EXISTS`` for the 4 deprecated cols.

Columns dropped
---------------
- ``openai_api_key``
- ``deepseek_api_key``
- ``kimi_api_key``
- ``dashscope_api_key``

Column preserved
----------------
- ``gemini_api_key`` — out of scope per architect 03-arch-be.md §2.4
  (Q4 ratification). Still consumed by landing extractors that bypass
  the LiteLLM Proxy.

Migration strategy
------------------
1. **Raw SQL ``DROP COLUMN IF EXISTS`` (idempotent):** four separate
   ``op.execute()`` calls per ``.claude/rules/backend-migrations.md``
   Pattern. ``IF EXISTS`` guard means re-runs after the first apply
   are no-ops (cols already gone → no error). Never use
   ``op.drop_column()`` (raises on re-run when col absent).
2. **Downgrade adds cols back as nullable TEXT:** rolls the schema
   back so an operator may revert the migration if needed. **Data
   CANNOT be restored** — the keys were already NULLed by T-6a, and
   the backup table ``tenants_api_keys_backup_pre_t6a`` (also dropped
   here) contained pre-NULL state for forensic audit during the T-6b
   operational gate window only. Per architect 04-tickets.yaml T-6c
   acceptance: schema-rollback works; data-loss is documented +
   accepted (ephemeral credentials, customer may have rotated keys
   in the meantime, restoring stale credentials would be worse than
   the schema regression).
3. **Backup table cleanup:** drop ``tenants_api_keys_backup_pre_t6a``
   (created by T-6a) since the operational gate window has closed.
   ``DROP TABLE IF EXISTS`` for idempotency.

Decisions honored
-----------------
- Architect 03-arch-be.md §2.4 BINDING (Q4 ratification): 4 cols
  deprecated, ``gemini_api_key`` retained.
- Architect 03-arch-be.md §3.4 BINDING: three-phase expand-contract
  shape; T-6c is the physical contract.
- T-3 BINDING + T-6a BINDING: ``*_backup_pre_tN`` convention; backup
  table cleanup at the end of the lifecycle (T-6c drops the T-6a
  backup since operational gate has closed).
- Backend-migrations rule BINDING: ``op.execute()`` raw SQL with
  ``IF EXISTS``/``IF NOT EXISTS`` guards, never ``op.drop_column()``
  / ``op.add_column()`` (not idempotent in SA 2.0.27 + raise on
  re-run).
- T-6b BINDING (PM-ratified 2026-05-06 02:50Z): zero traffic
  pre-clientes verified; safe to physically drop.

Idempotency guarantee
---------------------
- Each ``DROP COLUMN IF EXISTS`` is self-idempotent.
- Backup table drop guarded by ``DROP TABLE IF EXISTS``.
- Downgrade ``ADD COLUMN IF NOT EXISTS`` is self-idempotent.
- Test ``test_alembic_drop_column_idempotent`` enforces the
  ``IF EXISTS`` contract (mock-based per T-3/T-6a precedent).
- Live ``alembic upgrade head && alembic upgrade head`` validation
  deferred to ``/pase-produccion`` per T-3/T-6a precedent (brain
  container DOWN in dev).

Quality gates (per 04-tickets.yaml § T-6c)
-------------------------------------------
- A1: Migration idempotent (mock-based, ``IF EXISTS`` guards).
- A2: ``TenantModel.__table__.columns`` excludes 4 cols, retains gemini.
- A3: Pydantic ``model_fields`` excludes 4 fields, retains gemini.
- A4: ``tenant_repository.py`` source has zero functional references.
- A5: Live alembic dual-run (deferred to ``/pase-produccion``).

Revision ID: 124_drop_tenant_provider_api_keys
Revises: 123_deprecate_tenant_provider_api_keys
Create Date: 2026-05-05
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "124_drop_tenant_provider_api_keys"
down_revision: str | None = "123_deprecate_tenant_provider_api_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop deprecated tenant provider API key columns (Phase 3 expand-contract).

    Step 1: ``DROP COLUMN IF EXISTS`` for each of 4 deprecated cols.
            Idempotent — re-run is a no-op (cols already gone).
            ``gemini_api_key`` is intentionally NOT dropped (out of
            scope per arch §2.4 — still active for landing extractors).
    Step 2: Drop the T-6a backup table since the operational gate
            window has closed (T-6b ratified 2026-05-06 02:50Z). The
            backup contained pre-NULL state for forensic audit during
            the gate window only; post-T-6c it is dead weight.
    """
    # ── Step 1: DROP 4 deprecated columns (idempotent via IF EXISTS) ───────
    # Each statement is independent so failure-mid-run leaves a clear
    # partial-apply state that ``alembic upgrade`` can re-apply safely
    # (the IF EXISTS guard makes already-dropped cols a no-op).
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS openai_api_key")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS deepseek_api_key")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS kimi_api_key")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS dashscope_api_key")

    # ── Step 2: Drop T-6a backup table (operational gate has closed) ───────
    # T-6a created ``tenants_api_keys_backup_pre_t6a`` to preserve
    # pre-NULL state during the T-6b operational verify window. Post
    # T-6b ratification (2026-05-06 02:50Z), the backup is no longer
    # needed for forensic audit. ``IF EXISTS`` guards re-runs.
    op.execute("DROP TABLE IF EXISTS tenants_api_keys_backup_pre_t6a")


def downgrade() -> None:
    """Restore deprecated tenant API key columns as nullable TEXT.

    **DATA CANNOT BE RESTORED** — the keys were ephemeral credentials
    NULLed by T-6a, and the backup table is dropped by ``upgrade()``
    (operational gate has closed). This downgrade only restores the
    schema shape so an operator may revert the migration if a
    rollback is required for operational reasons.

    Per architect 03-arch-be.md §2.4 + 04-tickets.yaml T-6c
    deliverables: data loss on downgrade is documented + accepted.
    The customer may have rotated keys after T-6a NULLed them;
    attempting to restore stale credentials would be a worse
    security posture than the schema regression.

    Idempotency: ``ADD COLUMN IF NOT EXISTS`` so re-running downgrade
    after a successful upgrade-then-downgrade is a no-op.
    """
    # Restore 4 deprecated columns as nullable TEXT (matching original schema).
    # IF NOT EXISTS guards re-runs and accidental re-applies on a partially
    # downgraded schema.
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS openai_api_key TEXT")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deepseek_api_key TEXT")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS kimi_api_key TEXT")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS dashscope_api_key TEXT")
