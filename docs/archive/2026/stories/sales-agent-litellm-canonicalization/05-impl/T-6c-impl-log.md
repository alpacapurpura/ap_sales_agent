# T-6c Implementation Log

**Ticket:** T-6c — Migration DROP COLUMN tenant API keys (Phase 3 expand-contract)
**Story:** sales-agent-litellm-canonicalization
**Sprint:** S1-eval-runner / PI-12
**Builder:** `builder-backend` (Claude Opus 4.7 — `claude_opus_required: true` per architect)
**Commit:** `a10e146c` (pushed to `development` 2026-05-05)
**Date:** 2026-05-05
**State (R30):** `tests-passing` — awaiting orchestrator → gate-runner → auditor-backend independent verdict.

## Summary

Final phase (Phase 3) of the three-phase Stripe-style expand-contract deprecation
of the per-tenant provider API key columns. T-6c physically removes the 4
deprecated columns from the `tenants` table, deletes the matching SQLAlchemy
`Column` declarations, deletes the deprecated Pydantic `Field` declarations
across `Tenant` / `AISettings` / `TenantSettingsUpdate`, and drops the T-6a
forensic-audit backup table now that the operational gate window has closed.

`gemini_api_key` remains active per architect 03-arch-be.md §2.4 (Q4
ratification) — still consumed by landing extractors that bypass the LiteLLM
Proxy.

Phase chain:
- **Phase 1 (T-6a, merged + audit-APPROVED):** NULLed cols, Pydantic
  `deprecated=True, exclude=True`, repo stopped writes, `_extract_tenant_key`
  DELETED, backup table created (`tenants_api_keys_backup_pre_t6a`).
- **Phase 2 (T-6b, PM-ratified 2026-05-06 02:50Z pre-clientes per R7):** zero
  traffic operational verify, trivially PASS.
- **Phase 3 (T-6c, this ticket):** physical DROP COLUMN + model/Pydantic/repo
  cleanup + backup table cleanup.

## Skills Consulted (Step 0 GATE)

- **`backend-expert`** — invoked Step 3 SOP routing. Loaded
  `references/runtime-quality-checklist.md` BEFORE commit. Decisions:
  - Migration uses raw SQL `op.execute()` per `.claude/rules/backend-migrations.md`
    Pattern (NEVER `op.drop_column()` — not idempotent in SA 2.0.27 + raises on
    re-run when col absent).
  - Pydantic v2 field-removal pattern: physical deletion of `Field(...)`
    declaration vs T-6a's `deprecated=True, exclude=True` (which kept the
    field but excluded from `model_dump`). Post-T-6c, old clients sending the
    deprecated keys via raw JSON have those keys silently ignored by Pydantic
    v2 default `extra='ignore'`.
  - SQLA 2.0 `Mapped` Column declaration removal: simple physical deletion of
    4 lines in `tenant_model.py`. `__table__.columns` introspection in test A2
    verifies the model no longer maps to dropped DB cols.
  - DDD schema-mirror exception (R5 2026-05-05) explicitly N/A — T-6c touches
    `iam/persistence/models/` directly (not shared/ ripple). Standard DDD
    pattern: business module owns its own column drop migration.
  - 501-stub / Annotated dep / response_model anti-patterns N/A (no new
    endpoints).
- **`tessl__fastapi`** — invoked for Pydantic v2 field-removal semantics.
  Decision: `extra='ignore'` (BaseEntity default ConfigDict) means raw-JSON
  POST/PATCH bodies can still carry the deprecated keys; Pydantic silently
  drops them at validation time. This preserves backward compatibility with
  any old client that hadn't migrated post-T-6a. Verified via reading
  `BaseEntity.model_config` → `ConfigDict(from_attributes=True,
  populate_by_name=True)` (no `extra` override → default `'ignore'`).
- **`tessl__pytest-api-testing`** — invoked for migration test pattern.
  Decision: follow T-3 + T-6a mock-based pattern (`importlib.util` to load
  migration module, `patch.object(module.op, "execute",
  side_effect=executed.append)`, inspect SQL strings). Live alembic dual-run
  deferred to `/pase-produccion` per T-3/T-6a precedent (brain container DOWN
  in dev; native pytest cannot bootstrap Alembic env without Postgres up).
  Reference precedent: `tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py`
  + `tests/migrations/test_t3_pricing_snapshot_repair.py`.

NOT invoked (out of scope):
- `tessl__graceful-degradation` — no external HTTP/DB calls touched.
- `brand-expert`, `offer-expert`, `offer-type-preset-expert`, `metrics-expert`,
  `manychat-expert` — domain catalogs untouched (T-6c is iam-scoped).

## Default-flip pre-audit (Step 0.5)

**Trigger evaluation:** T-6c does NOT flip a `core/config.py` feature flag
default. Per `.claude/rules/anti-default-flip-audit.md` § "Cuándo aplica":
flag default that gates a runtime call path side-effect. T-6c only drops
columns + deletes Pydantic fields + deletes a backup table — none of the
inventoried flags (USE_OUTBOX_PATTERN_*, USE_DEEPAGENTS_*, etc.) are
affected.

**Verdict:** N/A. Skipped per rule § "Cuándo aplica" matrix.

## Existing systems audit (NO NEW LAYER rule)

Pure deletion + cleanup work — zero new abstractions introduced:

```bash
$ grep -rn "openai_api_key\|deepseek_api_key\|kimi_api_key\|dashscope_api_key" backend/src/ 2>/dev/null
# Pre-T-6c: matches in tenant_model.py (Column), tenant.py (Pydantic Field),
# repo + factory docstrings. Zero functional reads anywhere.
# Post-T-6c: zero functional refs anywhere; only docstring history references.

$ grep -rn "_extract_tenant_key" backend/src/ 2>/dev/null
src/shared/infrastructure/llm/factory.py:14:    - The orphaned ``_extract_tenant_key``...
# Docstring only — method body deleted by T-6a per Wave 3 scope refresh.
# T-6c regression test (A5) verifies it stays deleted.
```

Anti-duplication §0 GATE: nothing new created. T-6c is closure of an existing
deprecation cycle.

## Files modified

| File | Change | Rationale |
|---|---|---|
| `backend/alembic/versions/124_drop_tenant_provider_api_keys.py` | NEW (4 raw SQL DROP COLUMN IF EXISTS + backup-table drop + downgrade ADD COLUMN IF NOT EXISTS) | Phase 3 physical removal per architect §3.4 |
| `backend/src/modules/iam/infrastructure/models/tenant_model.py` | -4 Column declarations + comment update | A2 acceptance: `__table__.columns` excludes 4 cols |
| `backend/src/modules/iam/domain/tenant.py` | -12 deprecated Field declarations across 3 classes (Tenant + AISettings + TenantSettingsUpdate) + module docstring update + removed unused `Field` import | A3 acceptance: `model_fields` excludes 4 fields |
| `backend/src/modules/iam/infrastructure/repositories/tenant_repository.py` | Module + create() + update() docstrings updated to past-tense (Phase 3 closure) | A4 acceptance: zero functional refs (already T-6a clean) |
| `backend/tests/modules/iam/test_t6c_drop_tenant_api_keys.py` | NEW — 9 tests (A1..A5 acceptance + revision metadata + downgrade) | TDD RED-first per `.claude/rules/tdd-mandatory.md` |
| `backend/tests/modules/iam/test_domain_models.py` | 3 hunks updated (module docstring, `test_optional_keys_default_none`, `test_from_orm_mode`) — replace `t.openai_api_key is None` with `not hasattr(t, "openai_api_key")`; remove unused `warnings` import; remove deprecated keys from ORM-mode dict fixture | Downstream regression: tests referenced fields removed in T-6c |

**factory.py: NO CHANGE** — `_extract_tenant_key` already deleted by T-6a per
Wave 3 scope refresh; A5 regression test (`hasattr=False` + source grep)
confirms it stays deleted. Factory docstring left as-is per ticket spec
"factory.py: NO CHANGE".

## Acceptance verification (per 04-tickets.yaml § T-6c)

| ID | Acceptance | Verifier | Result |
|---|---|---|---|
| A1 | Migration idempotent (mock-based, `IF EXISTS` guards) | `test_alembic_drop_column_idempotent` | ✅ PASS — 4 `DROP COLUMN IF EXISTS` statements emitted, gemini NOT in dropped list, every DROP guarded `IF EXISTS` |
| A2 | `TenantModel.__table__.columns` excludes 4 cols, retains gemini | `test_tenant_model_columns_dropped` | ✅ PASS |
| A3 | `Tenant` / `AISettings` / `TenantSettingsUpdate` `model_fields` excludes 4 fields, retains gemini | 3 separate tests | ✅ PASS |
| A4 | `tenant_repository.py` zero functional col references | `test_repo_no_legacy_col_references` | ✅ PASS (T-6a already cleaned writes; A4 confirms post-T-6c state) |
| A5 (regression) | `LLMFactory._extract_tenant_key` stays DELETED | `test_factory_extract_tenant_key_method_still_deleted` | ✅ PASS (hasattr=False + source-grep confirmed) |
| Bonus | Migration revision chain T-6a → T-6c | `test_migration_revision_metadata` | ✅ PASS (`revision="124_drop_tenant_provider_api_keys"`, `down_revision="123_deprecate_tenant_provider_api_keys"`) |
| Bonus | Downgrade `ADD COLUMN IF NOT EXISTS` for 4 cols | `test_migration_downgrade_adds_columns_back` | ✅ PASS |

**Live alembic dual-run (`alembic upgrade head && alembic upgrade head`)**
deferred to `/pase-produccion` per T-3/T-6a precedent. Brain container DOWN
in dev; native pytest cannot bootstrap Alembic env without Postgres up.
Idempotency contract enforced at SQL-string level (mock-based) which
matches the runtime guarantee since `IF EXISTS` is a Postgres-engine
feature evaluated at execute time.

## Quality gates (native — NEVER docker exec)

| Gate | Result |
|---|---|
| `ruff check src/ tests/ --no-cache` | ✅ All checks passed (only pre-existing unrelated noqa warning) |
| `ruff format --check src/ tests/` | ✅ 2329 files already formatted |
| `pytest tests/modules/iam/test_t6c_drop_tenant_api_keys.py -v` | ✅ 9/9 PASS |
| `pytest tests/modules/iam/ -v` | ✅ 195/195 PASS (full iam regression) |
| `pytest tests/architecture/ -x -q` | ✅ 827/827 PASS (no ratchet violations) |
| `pytest tests/modules/sales_agent/ tests/modules/copilot/observability/ -x -q` | ✅ 837/837 PASS (downstream regression) |
| `pytest -m "not integration and not verify" -q` (full BE suite) | ✅ 9070 passed, 29 skipped, 0 failed |

## Decisions honored (R6)

- **Architect 03-arch-be.md §2.4 BINDING (Q4 ratification):** 4 cols
  deprecated, `gemini_api_key` retained throughout — verified across migration
  upgrade/downgrade, model, all 3 Pydantic DTOs, repo.
- **Architect 03-arch-be.md §3.4 BINDING:** three-phase expand-contract shape;
  T-6c is the physical contract closing the cycle.
- **T-3 BINDING:** `*_backup_pre_tN` raw SQL idempotency convention. T-6c
  drops the T-6a backup table (`tenants_api_keys_backup_pre_t6a`) since the
  operational gate window has closed (T-6b PM-ratified).
- **T-6a BINDING:** mock-based migration test pattern (`importlib.util` +
  `patch.object(module.op, "execute")` + SQL string inspection); revision
  chain parent=`123_deprecate_tenant_provider_api_keys`.
- **Backend-migrations rule BINDING:** raw SQL `op.execute("ALTER TABLE
  tenants DROP COLUMN IF EXISTS …")`. Never `op.drop_column()` (not
  idempotent in SA 2.0.27).
- **TDD rule BINDING:** RED first per `.claude/rules/tdd-mandatory.md` —
  initial run showed 7/9 FAIL, 2/9 PASS (the 2 already-clean cases: A4
  repo + A5 factory regression). Post-implementation: 9/9 GREEN.
- **R30 BINDING:** builder phase output is `tests-passing` ONLY. No verdict
  claim in footer. Auditor (independent contract) decides.
- **R5 schema-mirror exception N/A:** T-6c touches own-module persistence
  (`modules/iam/infrastructure/models/`), not a shared/ ripple to consumer
  module. Standard DDD pattern, not the schema-mirror exception scope.

## Cross-module reads (read-only, no writes)

None. T-6c is iam-scoped. The only cross-cutting touch is the regression test
`test_factory_extract_tenant_key_method_still_deleted` which imports from
`src.shared.infrastructure.llm.factory` to assert the method stays deleted —
this is a read-only verification, no factory.py modifications.

## Parallel-safety (M1-M8)

- **M1:** T-6c is single-module BE work (iam) — no cross-module collisions.
- **M3:** Tests run sequential (not concurrent with another session's tests).
- **M5:** No `git pull` / `git fetch && merge` / `git push --force` /
  `git revert` used.
- **M7:** Staged files by exact name only (`git add <path>`); never
  `git add .` / `-A` / `-u`. Working tree had pre-existing R32 reconcile
  capabilities WIP from another session — DID NOT TOUCH per ticket spec
  parallel-safety guard.
- **M8:** Did extend (not replace) the T-6a context already established
  in `tenant_repository.py` (docstring update past-tense vs replacement of
  the file).

## Test artifact references

- `backend/tests/modules/iam/test_t6c_drop_tenant_api_keys.py` (9 tests, all PASS)
- `backend/tests/modules/iam/test_domain_models.py` (3 hunks updated, full file PASS)
- `backend/alembic/versions/124_drop_tenant_provider_api_keys.py` (new migration)

## Next steps (handoff to orchestrator)

1. Orchestrator (`/dev-team`) reads this impl log + reads commit SHA.
2. Orchestrator spawns `gate-runner` Haiku 4.5 for `/test-backend` 13 gates.
3. Orchestrator spawns `auditor-backend` Opus 4.7 (independent verdict).
4. If REVIEW.md verdict = APPROVED → `/pm` merges + closes Wave 6 + closes
   Story A code scope.
5. If verdict = CHANGES_REQUESTED → builder fixes within scope; max 3 iter
   per `.claude/rules/parallel-safety.md`.

Story A code scope COMPLETE post-T-6c audit-APPROVED.
