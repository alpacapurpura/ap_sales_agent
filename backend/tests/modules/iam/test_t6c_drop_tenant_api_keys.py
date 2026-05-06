"""Tests for T-6c — DROP COLUMN tenant provider API keys (Phase 3 expand-contract).

PI-12 S1 story ``sales-agent-litellm-canonicalization`` ticket T-6c.

Background
----------
Final phase of three-phase expand-contract migration:

- Phase 1 (T-6a): NULL the 4 deprecated cols + Pydantic
  ``deprecated=True, exclude=True`` + repo stops writes + factory
  ``_extract_tenant_key`` DELETED.
- Phase 2 (T-6b — operational gate, PM-ratified 2026-05-06 02:50Z
  pre-clientes per R7): zero traffic verify, trivially PASS.
- Phase 3 (T-6c — this ticket): physically ``ALTER TABLE tenants DROP
  COLUMN IF EXISTS`` for the 4 deprecated cols + remove SQLAlchemy
  ``Column`` declarations + remove Pydantic ``Field`` declarations.

``gemini_api_key`` is preserved throughout — it remains active per
architect 03-arch-be.md §2.4 (Q4 ratification) because landing
extractors still call Gemini directly bypassing the LiteLLM Proxy.

Acceptance criteria (per 04-tickets.yaml § T-6c)
------------------------------------------------
- A1: Migration ``124_drop_tenant_provider_api_keys.py`` is idempotent
  (raw SQL ``DROP COLUMN IF EXISTS`` so re-runs are no-ops). Mock-based
  per T-3/T-6a precedent — live alembic ``upgrade head && upgrade head``
  deferred to ``/pase-produccion`` (brain container DOWN; native pytest
  cannot bootstrap an Alembic env without Postgres up).
- A2: ``TenantModel.__table__.columns`` does NOT contain the 4
  deprecated cols + DOES contain ``gemini_api_key``.
- A3: Pydantic ``Tenant``/``AISettings``/``TenantSettingsUpdate``
  ``model_fields`` does NOT contain the 4 deprecated fields + DOES
  contain ``gemini_api_key``.
- A4: ``tenant_repository.py`` source has zero functional references to
  the 4 deprecated col names (docstring references are allowed).
- A5 (regression from T-6a): ``LLMFactory._extract_tenant_key`` method
  remains DELETED.

Decisions honored
-----------------
- Architect 03-arch-be.md §2.4 BINDING: 4 cols deprecated, gemini
  retained.
- T-3 BINDING: ``*_backup_pre_tN`` raw SQL idempotency convention.
- Backend-migrations rule BINDING: ``op.execute()`` raw SQL with
  ``IF EXISTS``/``IF NOT EXISTS`` guards, never ``op.drop_column()``
  (not idempotent).
- TDD rule BINDING: this file written RED first per
  ``.claude/rules/tdd-mandatory.md``; GREEN after migration + model
  edits.
- T-6a precedent BINDING: mock-based ``op.execute`` SQL inspection
  pattern (matches ``test_t6a_deprecate_tenant_api_keys.py``).

Test strategy
-------------
Mirror T-6a test pattern: load migration via ``importlib.util``,
patch ``op.execute``, inspect SQL strings produced. No real DB
required for migration assertions.

For model + DTO + repo assertions: direct Python introspection
(``__table__.columns``, ``model_fields``, source-file grep).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Migration loading helper (mirrors T-3 + T-6a test pattern)
# ---------------------------------------------------------------------------


_DEPRECATED_COLS = (
    "openai_api_key",
    "deepseek_api_key",
    "kimi_api_key",
    "dashscope_api_key",
)
_RETAINED_COL = "gemini_api_key"
_MIGRATION_FILENAME = "124_drop_tenant_provider_api_keys.py"
_MIGRATION_REVISION = "124_drop_tenant_provider_api_keys"
_MIGRATION_DOWN_REVISION = "123_deprecate_tenant_provider_api_keys"


def _load_migration_module():
    """Load T-6c migration file as Python module without alembic env.

    Mirrors helper in ``test_t6a_deprecate_tenant_api_keys.py``. Loads
    the migration by absolute path so we can mock ``op.execute`` and
    inspect emitted SQL strings without bootstrapping the Alembic
    environment (which requires a live Postgres connection).
    """
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    migration_path = repo_root / "alembic" / "versions" / _MIGRATION_FILENAME
    spec = importlib.util.spec_from_file_location(f"migration_{_MIGRATION_REVISION}", migration_path)
    assert spec is not None and spec.loader is not None, (
        f"Migration file not found at {migration_path}. "
        "T-6c GREEN requires the migration file to exist before tests pass."
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# A1 — Migration idempotency + correctness (mock-based per T-6a precedent)
# ---------------------------------------------------------------------------


def test_alembic_drop_column_idempotent() -> None:
    """A1 — upgrade() emits ``DROP COLUMN IF EXISTS`` for each of 4 cols.

    Idempotency contract: ``IF EXISTS`` guard means re-running upgrade
    after the first apply is a no-op (cols already gone → no error).
    Mirrors ``backend-migrations.md`` Pattern: raw SQL via
    ``op.execute()``, never ``op.drop_column()`` (the latter raises on
    re-run when col absent).

    Mock-based verification: capture all SQL strings produced by
    ``upgrade()`` and confirm one ``ALTER TABLE tenants DROP COLUMN
    IF EXISTS <col>`` per deprecated col.

    Live alembic dual-run (``upgrade head`` x2) deferred to
    ``/pase-produccion`` per T-3 + T-6a precedent (brain container DOWN
    in dev; native pytest cannot bootstrap Alembic env without
    Postgres up).
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.upgrade()

    sql_combined = "\n".join(executed)

    # Each deprecated column must have a DROP COLUMN IF EXISTS statement
    for col in _DEPRECATED_COLS:
        assert f"DROP COLUMN IF EXISTS {col}" in sql_combined, (
            f"upgrade() must emit 'ALTER TABLE tenants DROP COLUMN IF EXISTS {col}' "
            "(idempotent raw SQL per .claude/rules/backend-migrations.md). "
            "Use op.execute() — never op.drop_column() (not idempotent on re-run)."
        )

    # gemini_api_key must NOT be dropped (architect §2.4 — still active)
    assert f"DROP COLUMN IF EXISTS {_RETAINED_COL}" not in sql_combined, (
        f"upgrade() must NOT drop {_RETAINED_COL} (out of scope per arch §2.4 — "
        "still consumed by landing extractors bypassing LiteLLM Proxy)."
    )

    # Idempotency contract: every DROP must use IF EXISTS
    drop_stmts = [s for s in executed if "DROP COLUMN" in s]
    assert len(drop_stmts) >= len(_DEPRECATED_COLS), (
        f"Expected at least {len(_DEPRECATED_COLS)} DROP COLUMN statements, "
        f"got {len(drop_stmts)}. Each deprecated col needs its own statement."
    )
    for stmt in drop_stmts:
        assert "IF EXISTS" in stmt, (
            f"DROP COLUMN statement missing IF EXISTS guard: {stmt!r}. "
            "Required for re-run safety per backend-migrations.md."
        )


def test_migration_revision_metadata() -> None:
    """Migration declares correct revision chain (T-6a → T-6c).

    Parent revision must be ``123_deprecate_tenant_provider_api_keys``
    (T-6a, current head post-T-6a merge). T-6c is the new head after
    apply.
    """
    module = _load_migration_module()
    assert module.revision == _MIGRATION_REVISION, f"Expected revision={_MIGRATION_REVISION}, got {module.revision!r}"
    assert module.down_revision == _MIGRATION_DOWN_REVISION, (
        f"Expected down_revision={_MIGRATION_DOWN_REVISION} (T-6a head), got {module.down_revision!r}"
    )


def test_migration_downgrade_adds_columns_back() -> None:
    """downgrade() emits ``ADD COLUMN IF NOT EXISTS`` for each col.

    Schema rollback path: the 4 cols are recreated as nullable TEXT
    (matching original schema). Data CANNOT be restored — the keys
    were already NULLed by T-6a; this is documented in spec.

    Idempotency: ``IF NOT EXISTS`` guard means re-running downgrade
    after a successful upgrade restores the schema, but on a fresh
    DB where cols never existed, the second run is a no-op.
    """
    module = _load_migration_module()
    executed: list[str] = []

    with patch.object(module.op, "execute", side_effect=executed.append):
        module.downgrade()

    sql_combined = "\n".join(executed)

    for col in _DEPRECATED_COLS:
        assert f"ADD COLUMN IF NOT EXISTS {col}" in sql_combined, (
            f"downgrade() must emit 'ALTER TABLE tenants ADD COLUMN IF NOT EXISTS "
            f"{col} TEXT' (idempotent rollback per backend-migrations.md)."
        )

    # gemini_api_key must NOT be added — it was never dropped
    assert f"ADD COLUMN IF NOT EXISTS {_RETAINED_COL}" not in sql_combined, (
        f"downgrade() must NOT add {_RETAINED_COL} (it was never dropped)."
    )


# ---------------------------------------------------------------------------
# A2 — TenantModel SQLAlchemy columns dropped
# ---------------------------------------------------------------------------


def test_tenant_model_columns_dropped() -> None:
    """A2 — TenantModel.__table__.columns excludes 4 deprecated cols.

    Source-of-truth check: SQLAlchemy ``Mapped`` declarations in
    ``tenant_model.py`` must be deleted post-T-6c. The Column metadata
    is reflected in ``__table__.columns``; absence confirms the model
    no longer maps to the dropped DB cols.

    ``gemini_api_key`` MUST remain present (architect §2.4 — still
    active).
    """
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel

    column_names = {col.name for col in TenantModel.__table__.columns}

    for col in _DEPRECATED_COLS:
        assert col not in column_names, (
            f"TenantModel.__table__.columns must NOT include '{col}' post-T-6c. "
            f"Remove the Column declaration from "
            f"backend/src/modules/iam/infrastructure/models/tenant_model.py."
        )

    assert _RETAINED_COL in column_names, (
        f"TenantModel.__table__.columns MUST retain '{_RETAINED_COL}' "
        "(out of scope per arch §2.4 — landing extractors still consume it)."
    )


# ---------------------------------------------------------------------------
# A3 — Pydantic fields dropped from Tenant + AISettings + TenantSettingsUpdate
# ---------------------------------------------------------------------------


def test_pydantic_tenant_fields_dropped() -> None:
    """A3 — Tenant aggregate.model_fields excludes 4 deprecated fields.

    Pydantic v2 introspection: ``model_fields`` contains every declared
    field. Post-T-6c, the deprecated ``Field(deprecated=True,
    exclude=True)`` declarations are physically removed from
    ``tenant.py`` so the fields do not appear in ``model_fields`` at
    all (vs T-6a where they existed-but-excluded-from-dump).

    ``gemini_api_key`` MUST remain.
    """
    from src.modules.iam.domain.tenant import Tenant

    field_names = set(Tenant.model_fields.keys())

    for col in _DEPRECATED_COLS:
        assert col not in field_names, (
            f"Tenant.model_fields must NOT include '{col}' post-T-6c. "
            "Remove the deprecated Field declaration from "
            "backend/src/modules/iam/domain/tenant.py."
        )

    assert _RETAINED_COL in field_names, f"Tenant.model_fields MUST retain '{_RETAINED_COL}' (still active)."


def test_pydantic_aisettings_fields_dropped() -> None:
    """A3 — AISettings response DTO excludes 4 deprecated fields entirely.

    Post-T-6a the fields existed with ``exclude=True`` (invisible in
    ``model_dump`` output but present in ``model_fields``). Post-T-6c
    the Field declarations are physically removed.
    """
    from src.modules.iam.domain.tenant import AISettings

    field_names = set(AISettings.model_fields.keys())

    for col in _DEPRECATED_COLS:
        assert col not in field_names, (
            f"AISettings.model_fields must NOT include '{col}' post-T-6c. "
            "Remove the deprecated Field declaration from tenant.py."
        )

    assert _RETAINED_COL in field_names, f"AISettings.model_fields MUST retain '{_RETAINED_COL}' (still active)."


def test_pydantic_tenant_settings_update_fields_dropped() -> None:
    """A3 — TenantSettingsUpdate request DTO excludes 4 deprecated fields.

    The PATCH /settings/ai endpoint accepts this DTO. Removing the
    deprecated fields from the schema means old clients sending them
    via raw JSON will have those keys silently ignored by Pydantic v2
    (default ``extra='ignore'``), preserving backward compatibility
    while preventing silent writes.
    """
    from src.modules.iam.domain.tenant import TenantSettingsUpdate

    field_names = set(TenantSettingsUpdate.model_fields.keys())

    for col in _DEPRECATED_COLS:
        assert col not in field_names, (
            f"TenantSettingsUpdate.model_fields must NOT include '{col}' post-T-6c. "
            "Remove the deprecated Field declaration from tenant.py."
        )

    assert _RETAINED_COL in field_names, (
        f"TenantSettingsUpdate.model_fields MUST retain '{_RETAINED_COL}' (still writable per arch §2.4)."
    )


# ---------------------------------------------------------------------------
# A4 — Repo source has zero functional references to deprecated cols
# ---------------------------------------------------------------------------


def test_repo_no_legacy_col_references() -> None:
    """A4 — tenant_repository.py source: zero functional references.

    Source-level inspection: load the repo file and confirm no Python
    statements reference the 4 deprecated columns. Docstring references
    (e.g. T-6a context comments) are tolerated by extracting code
    lines only — but post-T-6c the docstring should also be cleaned up
    to reflect Phase 3 completion (no longer "T-6c will…").

    Patterns checked (must be absent in code):
      - ``getattr(``...``, "<col>")`` fallback access
      - ``.<col>`` attribute access on tenant or db_tenant
      - ``<col>=`` keyword argument
      - ``"<col>"`` string-literal column name reference

    ``gemini_api_key`` MUST remain referenced (still active).
    """
    from src.modules.iam.infrastructure.repositories import tenant_repository

    repo_path = Path(tenant_repository.__file__)
    source = repo_path.read_text(encoding="utf-8")

    # Strip docstrings and comments — we only care about functional code
    # references. The migration history reference in the module docstring
    # is informational-only and tolerated.
    lines = source.split("\n")
    code_lines: list[str] = []
    in_docstring = False
    docstring_delim = '"""'
    for raw_line in lines:
        stripped = raw_line.strip()
        # Toggle docstring state on triple-quote delimiters
        delim_count = stripped.count(docstring_delim)
        if delim_count >= 2:
            # Single-line docstring (open + close on same line) — skip
            continue
        if delim_count == 1:
            in_docstring = not in_docstring
            continue
        if in_docstring:
            continue
        # Strip inline comments
        code_line = raw_line.split("#", 1)[0] if "#" in raw_line else raw_line
        code_lines.append(code_line)
    code_only = "\n".join(code_lines)

    for col in _DEPRECATED_COLS:
        # Check for various functional reference patterns
        kwarg_pattern = f"{col}="
        attr_pattern = f".{col}"
        getattr_pattern = f'"{col}"'
        assert kwarg_pattern not in code_only, (
            f"tenant_repository.py code must NOT contain kwarg '{kwarg_pattern}' "
            f"(deprecated col {col} dropped in T-6c). Found at line(s):\n"
            f"  {[i + 1 for i, line in enumerate(code_lines) if kwarg_pattern in line]}"
        )
        assert attr_pattern not in code_only, (
            f"tenant_repository.py code must NOT contain attribute access '{attr_pattern}' "
            f"(deprecated col {col} dropped in T-6c)."
        )
        assert getattr_pattern not in code_only, (
            f"tenant_repository.py code must NOT contain string literal {getattr_pattern!r} "
            f"(deprecated col {col} dropped in T-6c)."
        )

    # gemini_api_key MUST remain (still active per arch §2.4)
    assert f"{_RETAINED_COL}=" in code_only or f".{_RETAINED_COL}" in code_only, (
        f"tenant_repository.py MUST continue to reference '{_RETAINED_COL}' "
        "(out of scope per arch §2.4 — gemini still active)."
    )


# ---------------------------------------------------------------------------
# A5 — Regression check from T-6a (factory._extract_tenant_key DELETED)
# ---------------------------------------------------------------------------


def test_factory_extract_tenant_key_method_still_deleted() -> None:
    """A5 — Regression: ``LLMFactory._extract_tenant_key`` remains DELETED.

    Defense-in-depth from T-6a (where the method was first removed per
    auditor T-5 review acceleration). T-6c MUST NOT re-add the method.

    Equivalent bash:
        ``! grep -q 'def _extract_tenant_key' \
          backend/src/shared/infrastructure/llm/factory.py``
    """
    from src.shared.infrastructure.llm import factory
    from src.shared.infrastructure.llm.factory import LLMFactory

    assert not hasattr(LLMFactory, "_extract_tenant_key"), (
        "LLMFactory._extract_tenant_key must remain DELETED post-T-6c "
        "(T-6a regression check). If you see this fail with hasattr=True, "
        "remove the method from factory.py — it was orphaned post-T-5 and "
        "should never come back."
    )

    factory_source = Path(factory.__file__).read_text(encoding="utf-8")
    assert "def _extract_tenant_key" not in factory_source, (
        "factory.py must NOT contain 'def _extract_tenant_key' "
        "(orphaned method, deleted in T-6a, MUST stay deleted post-T-6c)."
    )
