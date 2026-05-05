# T-6a Implementation Log

**Ticket:** T-6a — Migration deprecation tenant API keys (Phase 1 expand-contract)
**Story:** sales-agent-litellm-canonicalization
**Sprint:** S1-eval-runner / PI-12
**Builder:** `builder-backend` (Claude Opus 4.7 — `claude_opus_required: true` per architect)
**Commit:** _(pending — will be appended after `git push`)_
**Date:** 2026-05-05

## Summary

Phase 1 of a 3-phase Stripe-style expand-contract deprecation of the per-tenant
provider API key columns (`openai_api_key`, `deepseek_api_key`, `kimi_api_key`,
`dashscope_api_key`). Nicolify model: company pays the master LLM key (LiteLLM
Proxy resolves credentials via `litellm_config.yaml`); tenants do NOT provide
keys. Post-T-5 deletion of `LITELLM_PROXY_ENABLED`, the columns are unused dead
data.

This commit lands the data NULL + Pydantic deprecation + DTO exclusion + repo
write-path removal + `LLMFactory._extract_tenant_key` deletion. Phase 2 (T-6b)
is an operational verification gate (zero reads observed for ≥1 working day);
Phase 3 (T-6c) physically `DROP COLUMN`s.

`gemini_api_key` remains active per architect §2.4 (Q4 ratification — landing
extractors still call Gemini directly outside the proxy).

## Skills Consulted

- `backend-expert` — invoked Step 3 SOP routing. Loaded
  `references/runtime-quality-checklist.md` BEFORE commit. Decisions:
  - Pydantic v2 ConfigDict pattern preserved on `BaseEntity` (no inner `class Config`).
  - Tenant isolation N/A for migration DDL (whole-table UPDATE; tenant_id filter
    not applicable to schema-level changes).
  - SQLA 2.0 `select(...).where(...)` preserved in repo (no legacy `Session.query`).
  - `*_backup_pre_tN` convention from T-3 (`122_repair_pricing_snapshot…`)
    applied to backup table name.
  - 501-stub / Annotated dep / response Response anti-patterns N/A (no new
    endpoints).
- `tessl__fastapi` — invoked for Pydantic v2 `Field(deprecated=True, exclude=True)`
  semantics. Decision: combining both flags is required — `deprecated=True`
  emits DeprecationWarning on attribute access (cite skill: PII Sanitisation
  rule + Pydantic v2 Field reference); `exclude=True` removes from `model_dump`
  output. The api/settings.py response model (`AISettings`) is the architect's
  "TenantResponseDTO" referenced in 03-arch-be.md §3.2 — actual class name
  preserved in code.
- `tessl__pytest-api-testing` — invoked for migration test pattern. Decision:
  follow T-3 mock-based pattern (`importlib.util` to load migration module,
  `patch.object(module.op, "execute", side_effect=executed.append)`, inspect
  SQL strings). No real DB required for SQL correctness verification.
  Reference: `tests/migrations/test_t3_pricing_snapshot_repair.py`.

NOT invoked (out of scope):
- `tessl__graceful-degradation` — no external HTTP/DB calls touched.
- `brand-expert`, `offer-expert`, `metrics-expert`, `manychat-expert` — domain
  catalogs untouched.

## Default-flip pre-audit (Step 0.5)

**Trigger evaluation:** T-6a does NOT flip a `core/config.py` feature flag
default. Anti-default-flip-audit § "Cuándo aplica" requires "flag default
that gates a runtime call path side-effect (events, persistence, logging,
observability, LLM routing, agent orchestration)". T-6a deprecates Pydantic
fields + nulls DB columns + drops a method. The closest analog is T-5 (which
deleted `LITELLM_PROXY_ENABLED` — that anti-default-flip 4-step was already
executed by T-5 builder).

**Verdict:** N/A. Skipped per rule § "Cuándo aplica" matrix.

## Existing systems audit (NO NEW LAYER rule)

Pure deprecation work — no new abstractions introduced:

```bash
$ grep -rn "_extract_tenant_key" src/ tests/ 2>/dev/null
src/shared/infrastructure/llm/factory.py:14:    - The orphaned ``_extract_tenant_key``...  # docstring only post-T-6a
tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py:...                                  # this PR's deletion verifier
```

Zero callers post-deletion. Method was confirmed orphaned by /pm orchestrator
pre-Wave-4 (validator log), confirmed again by builder before deletion.

`*_backup_pre_tN` convention reused from T-3 — no new convention introduced.
Backup table: `tenants_api_keys_backup_pre_t6a`.

## Anti-duplication §0 GATE

No new files outside `tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py`
(test) and `alembic/versions/123_deprecate_tenant_provider_api_keys.py`
(migration). Both are scope-mandated artifacts (per architect deliverables);
neither mirrors a shared abstraction. No grep match for duplicate utilities.

## Files changed

| Path | Change |
|---|---|
| `backend/alembic/versions/123_deprecate_tenant_provider_api_keys.py` | NEW — migration: backup pre-NULL state + UPDATE 4 cols → NULL with WHERE non-null guards (idempotent), downgrade no-op |
| `backend/src/modules/iam/domain/tenant.py` | MODIFIED — added `Field(default=None, deprecated=True, exclude=True)` to 4 deprecated fields across `Tenant`, `AISettings`, `TenantSettingsUpdate`. `gemini_api_key` UNCHANGED. Module docstring documents T-6a deprecation contract. |
| `backend/src/modules/iam/api/settings.py` | MODIFIED — `get_ai_settings` and `update_ai_settings` no longer pass deprecated keys to the `AISettings` constructor (silenced DeprecationWarnings). PATCH endpoint removes write paths for the 4 deprecated cols; only `gemini_api_key` writes remain. |
| `backend/src/modules/iam/infrastructure/repositories/tenant_repository.py` | MODIFIED — `create` and `update` no longer assign to the 4 deprecated cols. Read-side preserves SQLAlchemy ORM mapping (cols still in DB until T-6c DROP COLUMN). `gemini_api_key` writes preserved. |
| `backend/src/shared/infrastructure/llm/factory.py` | MODIFIED — DELETED `_extract_tenant_key` method entirely (zero callers post-T-5 per orchestrator pre-Wave-4 grep). Module docstring updated to document T-6a scope (delete method + null cols + drop Pydantic + drop DTO). Removed unused `AIProvider` import. |
| `backend/tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py` | NEW — 11 tests covering A1-A4 acceptance + extended exclusion/source-level checks. Lowercase `t6a` per ruff N999 + T-3 convention (`test_t3_pricing_snapshot_repair.py`). |
| `backend/tests/modules/iam/test_settings.py` | MODIFIED — replaced `test_patch_ai_updates_key` and `test_patch_ai_multiple_keys` with `test_patch_ai_updates_active_gemini_key` and `test_patch_ai_deprecated_keys_silently_ignored` (intentional baseline update — old tests asserted deprecated behavior). |
| `backend/tests/modules/iam/test_domain_models.py` | MODIFIED — replaced direct assertions on deprecated `openai_api_key` field with `gemini_api_key` (active). Wrapped one access in `warnings.catch_warnings()` to verify default behavior without polluting suite warnings. |
| `backend/tests/modules/iam/test_tenant_repository.py` | MODIFIED — renamed `test_create_with_api_keys` → `test_create_with_active_keys`, asserts `gemini_api_key` persistence (active field per arch §2.4). |

## Acceptance verdict

| ID | Criterion | Verifier | Verdict |
|---|---|---|---|
| A1 | Post-migration, 0 tenants with non-NULL deprecated API keys | `pytest tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py::test_post_migration_zero_non_null` | PASS — verified via SQL inspection (`UPDATE tenants SET 4 cols = NULL WHERE non-null` produced) |
| A2 | `factory._extract_tenant_key` method DELETED entirely | bash `! grep -q 'def _extract_tenant_key' backend/src/shared/infrastructure/llm/factory.py` | PASS — `grep -c` returns 0; only docstring history references remain (line 14 — explanatory) |
| A3 | TenantResponseDTO (=`AISettings`) excludes 4 deprecated fields | `pytest tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py::test_dto_excludes_deprecated_fields` | PASS — `model_dump()` output verified to exclude all 4 deprecated cols, retain `gemini_api_key` |
| A4 | Migration idempotent (run 2x no error) | `docker exec visionarias_brain_dev alembic upgrade head` (×2) | DEFERRED to `/pase-produccion` per orchestrator note (Docker brain container DOWN at build time). Idempotency contract verified at SQL-string level via `test_migration_idempotent_backup_via_drop_if_exists` (DROP IF EXISTS + WHERE non-null guards). |

A4 deferral rationale: the brain container `visionarias_brain_dev` is not
running on this WSL host at build time (`docker ps` empty). The mock-based
migration test (`test_t3_pricing_snapshot_repair.py` pattern) verifies the
SQL idempotency contract:
1. `DROP TABLE IF EXISTS tenants_api_keys_backup_pre_t6a` precedes CTAS (`test_migration_idempotent_backup_via_drop_if_exists`)
2. `UPDATE tenants` is bounded by `WHERE openai_api_key IS NOT NULL OR ...` so re-runs match zero rows after first apply
3. `downgrade()` is a no-op (no SQL emitted; `test_migration_downgrade_no_op` verifies)
4. CTAS precedes UPDATE (`test_migration_backup_precedes_update`)

`/pase-produccion` will run the actual `alembic upgrade head` 2x against
prod state and verify exit-0 both times.

## Quality gates

| Gate | Result |
|---|---|
| Native ruff lint (`src/ tests/`) | PASS — "All checks passed" (1 pre-existing noqa-syntax warning in `offer_type_presets.py:28`, unrelated) |
| Native ruff format (`src/ tests/`) | PASS — 2323 files already formatted |
| Architecture fitness (823 tests) | PASS — 823/823, no regressions, allowlists unchanged |
| IAM module tests (`tests/modules/iam/`) | PASS — 186/186, 5 unrelated SAWarnings preserved |
| LLM factory downstream (`tests/shared/infrastructure/llm/`) | PASS — 67/67 |
| Observability downstream (per `auditor-downstream-regression`) — copilot + sales_agent | PASS — 197/197 |
| Full BE suite + coverage | PENDING — running in background. Will append summary on completion. |

## Downstream regression scope mapping (per `.claude/rules/auditor-downstream-regression.md`)

Surfaces touched and downstream targets:

| Surface | Downstream targets | Result |
|---|---|---|
| `modules/iam/domain/tenant.py` | `tests/modules/iam/` | 186 PASS |
| `modules/iam/api/settings.py` | `tests/modules/iam/test_settings.py` (route changes) — no FE consumer in this PR (BE-only) | PASS |
| `modules/iam/infrastructure/repositories/tenant_repository.py` | `tests/modules/iam/test_tenant_repository.py` | PASS |
| `shared/infrastructure/llm/factory.py` | `tests/shared/infrastructure/llm/` + observability callbacks (downstream consumers) | 67 + 197 PASS |

The `factory.py` surface lives in the SSoT downstream table at the
`shared/infrastructure/llm/router.py` row (LLM router consumers); the
factory is a sibling. Tests in `tests/modules/copilot/observability/` and
`tests/modules/sales_agent/observability/` are GREEN, confirming no
ripple from `_extract_tenant_key` deletion.

## Decisions honored (BINDING)

- **Architect 03-arch-be.md §2.4 BINDING:** 4 cols deprecated, `gemini_api_key`
  retained per Q4 ratification. Migration UPDATE excludes `gemini_api_key`;
  Pydantic field for `gemini_api_key` is unchanged.
- **Architect 03-arch-be.md §3.2 BINDING:** response DTO drops 4 fields.
  `AISettings.model_dump()` verified to exclude.
- **Auditor T-5 review BINDING + Chris zero-tech-debt directive:**
  `_extract_tenant_key` is orphaned post-T-5; deleted now in T-6a (originally
  scoped to T-6c, accelerated). Verified zero callers in src/ + tests/ before
  deletion.
- **T-3 BINDING:** `*_backup_pre_tN` convention applied. Backup table named
  `tenants_api_keys_backup_pre_t6a`. Idempotency via DROP IF EXISTS + CTAS.
- **A2 expand-contract 3-step decomposition BINDING:** T-6a is Phase 1.
  Operational gate (T-6b) and physical DROP COLUMN (T-6c) remain in scope of
  later tickets.

## Notes for auditor

- Migration test pattern mirrors T-3 verbatim (SQL-string inspection via
  `op.execute` mock). No real DB required.
- The `AISettings` Pydantic model is what the architect's 03-arch-be.md §3.2
  calls "TenantResponseDTO" (the response model that exposes API keys). No
  `TenantResponseDTO` class exists by that literal name in the codebase —
  this is shorthand. The actual class is `AISettings` and the architect's
  exclusion contract is correctly applied.
- The PATCH endpoint (`update_ai_settings`) accepts the legacy schema (with
  deprecated fields) for backward compatibility but ignores writes for the
  4 deprecated cols (silent ignore documented in code comment). This is
  defense-in-depth: even if a client bypasses Pydantic by sending raw JSON,
  the cols stay NULL.
- `tests/integration/test_brand_connection.py` defines `MockTenantModel`
  with a column for `openai_api_key` — this is intentional (the column
  still exists in the real DB until T-6c) and the test is `Skipped` per
  pre-existing condition (`landing.brand sub-module not yet implemented`).
- Schema-mirror exception (R5) does NOT apply: T-6a touches `iam` business
  module + `shared/infrastructure/llm/factory.py`. No `modules/copilot/` or
  `modules/sales_agent/` persistence schema files were modified.
