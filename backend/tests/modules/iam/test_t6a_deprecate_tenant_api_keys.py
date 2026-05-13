"""Tests for T-6a — deprecate tenant provider API keys (Phase 1 expand-contract).

PI-12 S1 story ``sales-agent-litellm-canonicalization`` ticket T-6a.

Background
----------
Nicolify model: company pays master key, tenants do NOT provide keys.
Post-T-5 (LITELLM_PROXY_ENABLED deletion), the per-tenant key columns
(openai_api_key, deepseek_api_key, kimi_api_key, dashscope_api_key) are
unused. T-6a is Phase 1 of a 3-phase expand-contract deprecation:

- Phase 1 (T-6a — this ticket): NULL the 4 deprecated columns, mark
  Pydantic fields ``deprecated=True`` + ``exclude=True``, drop fields from
  response DTO, DELETE the orphaned ``LLMFactory._extract_tenant_key``
  method, stop assigning to deprecated cols in repo.
- Phase 2 (T-6b — operational gate): observe zero reads in prod for ≥1
  working day.
- Phase 3 (T-6c): physically DROP COLUMN.

``gemini_api_key`` is OUT OF SCOPE — it remains active per architect's
expand-contract decision (only the 4 specific cols are deprecated).

Acceptance criteria
-------------------
- A1: Post-migration, 0 tenants with non-NULL deprecated API keys.
- A2: ``LLMFactory._extract_tenant_key`` method DELETED entirely.
- A3: ``AISettings`` Pydantic schema excludes 4 deprecated fields from
  serialization (``model_dump`` output) but keeps ``gemini_api_key``.
- A4: Migration idempotent (run 2x — covered by migration test pattern
  established in T-3 via mock-based ``op.execute`` inspection).

Test strategy
-------------
Mock-based following T-3 pattern (``test_t3_pricing_snapshot_repair.py``):
patch ``op.execute`` and inspect SQL strings. No real DB required for
migration assertions — SQL correctness verified by call-time inspection.

Decisions honored
-----------------
- Architect 03-arch-be.md §2.4 BINDING: 4 cols deprecated, gemini_api_key
  retained (Q4 ratification).
- Auditor T-5 review BINDING: ``_extract_tenant_key`` is orphaned post-T-5;
  delete now (originally scoped T-6c, accelerated to T-6a per zero-tech-debt
  directive).
- T-3 backup convention BINDING: backup table named
  ``tenants_api_keys_backup_pre_t6a`` (``*_backup_pre_tN`` pattern).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Migration loading helper (mirrors T-3 test pattern)
# ---------------------------------------------------------------------------


_DEPRECATED_COLS = (
    "openai_api_key",
    "deepseek_api_key",
    "kimi_api_key",
    "dashscope_api_key",
)
_RETAINED_COL = "gemini_api_key"
_BACKUP_TABLE = "tenants_api_keys_backup_pre_t6a"
_MIGRATION_FILENAME = "123_deprecate_tenant_provider_api_keys.py"
_MIGRATION_REVISION = "123_deprecate_tenant_provider_api_keys"
_MIGRATION_DOWN_REVISION = "122_repair_pricing_snapshot_provider_tagging"


def _load_migration_module():
    """Load T-6a migration file as Python module without alembic env.

    Mirrors helper in ``tests/migrations/test_t3_pricing_snapshot_repair.py``.
    Migration is loaded by absolute path (Alembic env not bootstrapped).
    """
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    migration_path = repo_root / "alembic" / "versions" / _MIGRATION_FILENAME
    spec = importlib.util.spec_from_file_location(f"migration_{_MIGRATION_REVISION}", migration_path)
    assert spec is not None and spec.loader is not None, (
        f"Migration file not found at {migration_path}. "
        "Build phase 2 GREEN: create the migration file before running tests."
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# A1 — Post-migration: deprecated cols NULLed (verified via SQL inspection)
# ---------------------------------------------------------------------------


def test_post_migration_zero_non_null() -> None:
    """A1 — upgrade() emits UPDATE that NULLs all 4 deprecated cols.

    Acceptance: post-migration, ``SELECT COUNT(*) FROM tenants WHERE
    openai_api_key IS NOT NULL OR deepseek_api_key IS NOT NULL OR
    kimi_api_key IS NOT NULL OR dashscope_api_key IS NOT NULL`` returns 0.

    Mock-based verification: inspect SQL strings produced by upgrade()
    and confirm an UPDATE statement on tenants exists with SET col=NULL
    for each of the 4 deprecated columns.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    sql_combined = "\n".join(executed)

    # UPDATE tenants statement must be present
    update_stmts = [s for s in executed if "UPDATE tenants" in s]
    assert len(update_stmts) >= 1, "upgrade() must contain UPDATE tenants statement"

    update_sql = update_stmts[0]

    # Each deprecated column must be NULLed
    for col in _DEPRECATED_COLS:
        assert f"{col} = NULL" in update_sql or f"{col}=NULL" in update_sql, f"upgrade() UPDATE must SET {col} = NULL"

    # gemini_api_key must NOT be NULLed (architect Q4 ratification)
    assert f"{_RETAINED_COL} = NULL" not in update_sql, (
        f"upgrade() must NOT NULL {_RETAINED_COL} (out of scope per arch §2.4)"
    )
    assert f"{_RETAINED_COL}=NULL" not in update_sql, (
        f"upgrade() must NOT NULL {_RETAINED_COL} (out of scope per arch §2.4)"
    )

    # Idempotency: WHERE clause must filter non-null rows
    # so re-runs are no-ops (post-first-run, all cols already NULL → 0 rows match).
    assert "IS NOT NULL" in update_sql, "upgrade() UPDATE must guard with WHERE col IS NOT NULL for idempotency"

    # Backup table convention from T-3 — must precede UPDATE
    assert _BACKUP_TABLE in sql_combined, (
        f"upgrade() must create backup table {_BACKUP_TABLE} per *_backup_pre_tN convention"
    )


def test_migration_revision_metadata() -> None:
    """Migration declares correct revision chain (T-3 head → T-6a)."""
    module = _load_migration_module()
    assert module.revision == _MIGRATION_REVISION
    assert module.down_revision == _MIGRATION_DOWN_REVISION


def test_migration_idempotent_backup_via_drop_if_exists() -> None:
    """A4 — backup table creation guarded by DROP IF EXISTS for re-run safety.

    Mirrors T-3 idempotency contract: DROP TABLE IF EXISTS before CTAS
    so re-running upgrade does not error with 'table already exists'.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    sql_combined = "\n".join(executed)

    assert f"DROP TABLE IF EXISTS {_BACKUP_TABLE}" in sql_combined, (
        "upgrade() must DROP TABLE IF EXISTS backup table for idempotency"
    )
    assert f"CREATE TABLE {_BACKUP_TABLE}" in sql_combined, "upgrade() must create backup via CTAS"
    # Backup must contain pre-NULL state — query selects deprecated cols
    backup_stmts = [s for s in executed if f"CREATE TABLE {_BACKUP_TABLE}" in s]
    assert len(backup_stmts) == 1
    backup_sql = backup_stmts[0]
    for col in _DEPRECATED_COLS:
        assert col in backup_sql, f"backup CTAS must include {col} so downgrade can audit pre-NULL state"


def test_migration_backup_precedes_update() -> None:
    """A4 — CTAS backup must execute before UPDATE so backup captures pre-NULL state."""
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    ctas_idx = next(
        (i for i, s in enumerate(executed) if f"CREATE TABLE {_BACKUP_TABLE}" in s),
        None,
    )
    update_idx = next(
        (i for i, s in enumerate(executed) if "UPDATE tenants" in s),
        None,
    )
    assert ctas_idx is not None, "CTAS backup must exist in upgrade()"
    assert update_idx is not None, "UPDATE tenants must exist in upgrade()"
    assert ctas_idx < update_idx, (
        f"CTAS (idx={ctas_idx}) must precede UPDATE (idx={update_idx}) to capture pre-NULL state"
    )


def test_migration_downgrade_no_op() -> None:
    """downgrade() is no-op (cannot restore ephemeral keys; documented in spec).

    Per architect 03-arch-be.md §2.4 + 04-tickets.yaml T-6a deliverables:
    'downgrade no-op (cannot restore ephemeral keys)' is the documented
    contract. Since the backup table preserves pre-NULL state for audit
    purposes, downgrade may either DROP the backup or be a strict no-op.
    Either choice is acceptable — assert downgrade() runs without error.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        # Should not raise
        module.downgrade()

    # No-op or backup cleanup — both acceptable
    # Assert: zero UPDATE statements that restore deprecated cols (cannot restore ephemeral keys)
    restore_attempts = [
        s for s in executed if "UPDATE tenants" in s and any(f"{col} =" in s for col in _DEPRECATED_COLS)
    ]
    assert len(restore_attempts) == 0, (
        "downgrade() must NOT attempt to restore deprecated keys (they are ephemeral and lost)"
    )


# ---------------------------------------------------------------------------
# A2 — Factory _extract_tenant_key method DELETED
# ---------------------------------------------------------------------------


def test_factory_extract_tenant_key_method_deleted() -> None:
    """A2 — ``LLMFactory._extract_tenant_key`` method does NOT exist.

    Verified via ``hasattr`` — confirms attribute removed from class.
    Bash equivalent verifier (in 04-tickets.yaml acceptance):
        ``! grep -q 'def _extract_tenant_key' backend/src/shared/infrastructure/llm/factory.py``

    Origin: orphaned post-T-5 per /pm orchestrator + auditor T-5 review.
    Originally scoped to T-6c, accelerated to T-6a per zero-tech-debt
    directive (no caller anywhere in src/ or tests/).
    """
    from luana_core_llm.factory import LLMFactory

    assert not hasattr(LLMFactory, "_extract_tenant_key"), (
        "LLMFactory._extract_tenant_key must be DELETED (orphaned post-T-5). "
        "If you see this fail with hasattr=True, remove the method body from "
        "backend/src/shared/infrastructure/llm/factory.py."
    )


# ---------------------------------------------------------------------------
# A3 — DTO excludes deprecated fields from response serialization
# ---------------------------------------------------------------------------


def test_dto_excludes_deprecated_fields() -> None:
    """A3 — ``AISettings`` Pydantic model excludes 4 deprecated fields.

    Per architect 03-arch-be.md §3.2: ``TenantResponseDTO`` (the response
    model that exposes API keys, namely ``AISettings`` in the actual
    codebase) must drop the 4 deprecated fields and retain
    ``gemini_api_key``.

    Pydantic v2 semantics: ``Field(deprecated=True, exclude=True)``:
    - ``deprecated=True``: emits DeprecationWarning when accessed.
    - ``exclude=True``: removes from ``model_dump()`` output (the
      serialization that FastAPI uses to render JSON response).

    Both are required for the field to be absent from the wire response.
    """
    from luana_core_iam.domain.tenant import AISettings

    # Construct an instance with all 5 keys populated (legacy bridge —
    # ORM may still pass them in until T-6c drops the columns).
    instance = AISettings(
        openai_api_key="sk-old",
        gemini_api_key="gm-active",
        deepseek_api_key="ds-old",
        kimi_api_key="kimi-old",
        dashscope_api_key="ds-old",
        can_use_platform_keys=True,
    )

    dumped = instance.model_dump()

    # The 4 deprecated fields must NOT appear in the serialized dict
    for col in _DEPRECATED_COLS:
        assert col not in dumped, (
            f"AISettings.model_dump() must exclude {col} (deprecated post-T-6a). "
            "Set Field(default=None, deprecated=True, exclude=True) in "
            "backend/src/modules/iam/domain/tenant.py."
        )

    # gemini_api_key must remain present (architect Q4 ratification — out of scope)
    assert _RETAINED_COL in dumped, f"AISettings.model_dump() must retain {_RETAINED_COL} (out of scope per arch §2.4)"
    assert dumped[_RETAINED_COL] == "gm-active"

    # can_use_platform_keys must remain present
    assert "can_use_platform_keys" in dumped


def test_tenant_domain_excludes_deprecated_fields() -> None:
    """A3 (extended) — Tenant aggregate excludes 4 deprecated fields from dump.

    Same exclusion contract applies to the ``Tenant`` aggregate root since
    it is the primary domain entity used by the repository to construct
    DB records. Deprecated fields must not propagate via ``model_dump``.
    """
    from uuid import uuid4

    from luana_core_iam.domain.tenant import Tenant

    instance = Tenant(
        id=uuid4(),
        name="T6a Test",
        slug="t6a-test",
        openai_api_key="sk-old",
        gemini_api_key="gm-active",
        deepseek_api_key="ds-old",
        kimi_api_key="kimi-old",
        dashscope_api_key="ds-old",
    )

    dumped = instance.model_dump()
    for col in _DEPRECATED_COLS:
        assert col not in dumped, f"Tenant.model_dump() must exclude {col} post-T-6a"
    assert _RETAINED_COL in dumped


def test_tenant_settings_update_excludes_deprecated_fields() -> None:
    """A3 (extended) — TenantSettingsUpdate excludes 4 deprecated fields.

    The PATCH /ai endpoint accepts this DTO. Excluding deprecated fields
    on the request side prevents accidental writes by old clients.
    """
    from luana_core_iam.domain.tenant import TenantSettingsUpdate

    instance = TenantSettingsUpdate(
        openai_api_key="sk-attempt",
        gemini_api_key="gm-active",
        deepseek_api_key="ds-attempt",
        kimi_api_key="kimi-attempt",
        dashscope_api_key="ds-attempt",
    )

    dumped = instance.model_dump()
    for col in _DEPRECATED_COLS:
        assert col not in dumped, f"TenantSettingsUpdate.model_dump() must exclude {col} post-T-6a"
    assert _RETAINED_COL in dumped


# ---------------------------------------------------------------------------
# A4 — Repository no longer writes deprecated columns
# ---------------------------------------------------------------------------


def test_repo_create_update_no_longer_writes() -> None:
    """A4 — TenantRepository.create + update do NOT assign deprecated cols.

    Source-level inspection: read the repo file and confirm no assignment
    statements like ``db_tenant.openai_api_key = ...`` or kwargs like
    ``openai_api_key=...`` exist for the 4 deprecated columns.

    ``gemini_api_key`` writes must remain (it is still active).
    """
    from luana_core_iam.infrastructure.repositories import tenant_repository

    repo_source = Path(tenant_repository.__file__).read_text(encoding="utf-8")

    # 4 deprecated cols: NO assignment statements should remain
    for col in _DEPRECATED_COLS:
        # Match patterns the legacy repo used:
        #   1. kwargs in TenantModel(...) constructor: `openai_api_key=tenant.openai_api_key,`
        #   2. db_tenant attr assign: `db_tenant.openai_api_key = tenant.openai_api_key`
        kwarg_pattern = f"{col}=tenant."
        attr_assign_pattern = f"db_tenant.{col} ="
        assert kwarg_pattern not in repo_source, (
            f"tenant_repository.py must NOT have kwarg '{kwarg_pattern}' (deprecated col {col} should not be written)"
        )
        assert attr_assign_pattern not in repo_source, (
            f"tenant_repository.py must NOT have assignment '{attr_assign_pattern}' "
            f"(deprecated col {col} should not be written)"
        )

    # gemini_api_key writes MUST remain (it is still active)
    assert (
        f"{_RETAINED_COL}=tenant.{_RETAINED_COL}" in repo_source
        or f"db_tenant.{_RETAINED_COL} = tenant.{_RETAINED_COL}" in repo_source
    ), f"tenant_repository.py must continue writing {_RETAINED_COL} (out of scope per arch §2.4 — gemini still active)"


# ---------------------------------------------------------------------------
# A2 (additional source-level grep verifier — bash equivalent)
# ---------------------------------------------------------------------------


def test_factory_source_no_extract_tenant_key_def() -> None:
    """A2 (source-level) — ``def _extract_tenant_key`` not present in factory.py.

    Equivalent to bash verifier in 04-tickets.yaml acceptance:
        ``! grep -q 'def _extract_tenant_key' backend/src/shared/infrastructure/llm/factory.py``

    Acts as a defense-in-depth check alongside ``hasattr`` test above —
    catches dynamic re-additions or commented-out methods.
    """
    from luana_core_llm import factory

    factory_source = Path(factory.__file__).read_text(encoding="utf-8")
    assert "def _extract_tenant_key" not in factory_source, (
        "factory.py must NOT contain 'def _extract_tenant_key' "
        "(orphaned method, deleted in T-6a per auditor T-5 recommendation)"
    )
