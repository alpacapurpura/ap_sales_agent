<!-- voseo-allowed: audit review citing voseo glosario verbatim per R25 -->
# Backend Code Review: T-6a — Deprecate Tenant Provider API Keys (Phase 1 expand-contract)

**Date:** 2026-05-05
**PR / CONTRACT:** PI-12 / S1 / `sales-agent-litellm-canonicalization` / T-6a
**Commits:** `f6e7ad0a` (feat) + `29b97eba` (docs SHA backfill) on `development`
**Files Reviewed:** 9 src/test + 1 migration (12 in commit including 3 docs)
**Domains touched:** iam (domain/api/repo) + shared (infrastructure/llm/factory)
**Skills consulted:** backend-expert (runtime-quality-checklist, master-data, currency-handling cross-check), tessl__fastapi (Pydantic v2 `Field(deprecated=True, exclude=True)` semantics), tessl__pytest-api-testing (mock-based migration test pattern), `.claude/rules/auditor-downstream-regression.md` SSoT table
**Verdict:** **APPROVED**

---

## /test-backend Gate Status (consumed from `gate-output.json`)

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | ruff/pytest native venv 3.12 |
| 2 | Postgres pre-flight | DOWN | brain container offline at build time → A4 deferred (consistent with T-3 pattern) |
| 3 | Lint (ruff check) | PASS | 0 errors |
| 4 | Format (ruff --check) | PASS | 0 reformats (2323 files) |
| 5 | Type check (mypy) | N/A in test-backend command (not in suite invocation), independently verified ruff strict-mode rules pass | — |
| 6 | Arch fitness (823 gates) | PASS | 823/823, allowlists unchanged |
| 7 | Tests + coverage | PASS | 9041 PASS / 35 SKIP / 16 deselect (integration), exit 0 (≥43% threshold met) |
| 8 | Verify marker | N/A | T-6a not analytics |
| 9 | Integration | DEFERRED | A4 alembic upgrade x2 deferred to /pase-produccion (brain container DOWN). SQL idempotency contract verified via mock-based migration tests (T-3 pattern) |
| 10 | Migration idempotency clone | PASS (mock-based) | DROP IF EXISTS + CTAS + WHERE non-null UPDATE + downgrade no-op all verified at SQL-string level |
| 11 | jscpd | PASS (implicit — not regressed in arch fitness) | — |
| 12 | interrogate | PASS (implicit) | All new functions have Google-style docstrings |
| 13 | pip-audit | N/A in test-backend command | No new deps added |

`gate-output.json` `any_fail=false`, `command_alias=test-backend` (full suite scope — covers downstream consumers per R3 SSoT table).

A4 deferral acceptable: same pattern as T-3 (`122_repair_pricing_snapshot_provider_tagging`); SQL idempotency contract enforced via 4 mock-based migration tests; live `alembic upgrade head` x2 will run during `/pase-produccion` deploy.

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 |
| 3 | Soft Deletes | PASS (N/A — pure deprecation) | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | 0 |
| 6 | Async Consistency | PASS (no changes) | 0 |
| 7 | Pydantic v2 / DTOs / PII | PASS | 0 |
| 8 | Migration Quality | PASS | 0 |
| 9 | Security | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Cross-cutting (master-data, currency, Spanish, Native-First, Decisions Honored) | PASS | 0 |
| 12 | Mirror detection (anti-duplication) | PASS (N/A — pure deprecation, no new abstractions) | 0 |

---

## Cross-scope flags

None. T-6a touches `iam` business module + `shared/infrastructure/llm/factory.py` only. No `modules/copilot/` or `modules/sales_agent/` files modified — schema-mirror exception R5 does NOT apply.

---

## Findings

### Category 1 — DDD Compliance — **PASS**

- `iam/domain/tenant.py` is pure Pydantic v2 — zero SQLAlchemy/FastAPI imports.
- `iam/api/settings.py` thin: validates input, delegates to ORM session via `Depends(get_db)`. No business logic creep.
- `iam/infrastructure/repositories/tenant_repository.py` implements data access; cleanly removes deprecated col writes from `create()` + `update()`.
- `shared/infrastructure/llm/factory.py` deletion of `_extract_tenant_key` is a *removal* of dead code, not a layer violation.
- Wave-based extraction orchestrator pattern N/A (no extractors touched).

### Category 2 — Tenant Isolation — **PASS**

- Migration is whole-table DDL/DML targeting all tenants — `tenant_id` filter not applicable for schema-level changes.
- Modified routes in `settings.py` continue to filter by `current_user.tenant_id` (lines 113, 219, 258, etc.). Pre-existing pattern preserved.
- `tenant_repository.get_by_id`/`get_by_slug` filter by tenant intrinsic identity (this IS the tenant entity — pre-existing canonical exception, not introduced by T-6a).
- Test `test_repo_create_update_no_longer_writes` validates write-side surface preservation.

### Category 3 — Soft Deletes — **PASS (N/A)**

T-6a does no soft/hard delete operations. The migration NULLs columns on existing rows (data deprecation, not row deletion). The factory method deletion is source-code level — no DB rows affected.

### Category 4 — Code Quality — **PASS**

- ruff lint: 0 errors (independently re-verified by auditor on changed files).
- ruff format: 0 reformats.
- McCabe ≤12: largest changed function (`update_ai_settings`) is ~20 lines, complexity well within budget.
- jscpd: not regressed in arch fitness suite.
- interrogate: all new functions have Google-style docstrings (migration upgrade/downgrade, all 11 new tests, repo create/update updated docstrings).
- No `# noqa` / `# type: ignore` introduced.

### Category 5 — SQLAlchemy 2.0 — **PASS**

- `tenant_repository.py` uses `db.execute(select(...).where(...)).scalars().first()` — modern 2.0 sintaxis.
- No `session.query()` legacy patterns.
- `TenantModel` ORM attributes (`Column(String, nullable=True)` at lines 33-37 of `tenant_model.py`) preserved for ORM read-side until T-6c — correct expand-contract pattern.

### Category 6 — Async Consistency — **PASS**

T-6a does not modify async/sync boundary. Routes remain `async def`. Repo is sync (pre-existing pattern in iam — uses sync `Session`, not `AsyncSession`). No new blocking I/O introduced.

### Category 7 — Pydantic v2 / DTOs / PII — **PASS**

- `Field(default=None, deprecated=True, exclude=True)` correctly applied to all 4 deprecated fields across `Tenant`, `AISettings`, `TenantSettingsUpdate` (lines 42-46, 63-67, 80-84 of `tenant.py`).
- `gemini_api_key` correctly retained without `deprecated=True` (architect §2.4 Q4).
- Tessl PII reference: deprecated API keys are sensitive credentials. Post-T-6a, they are excluded from `model_dump()` output (verified via `test_dto_excludes_deprecated_fields`). PATCH endpoint silently ignores writes (`update_ai_settings` line 266 only persists `gemini_api_key`). This is **PII allowlist tightening** — explicit removal, no new exposure.
- Routes use return type annotations (`-> AISettings`, `-> GeneralSettings`, `-> WebhookSettings`, `-> SystemUserProfile`, `-> TeamMemberSchema`) which FastAPI honors for serialization (per `tessl__fastapi` skill: "Return types are used to validate, filter, document, and serialize the response"). Pattern is pre-existing in iam module — T-6a does not regress.
- No raw `dict[str, Any]` introduced; all DTOs typed.
- `model_config = ConfigDict(...)` inherited via `BaseEntity` (shared base) — no inner `class Config` reintroduced.

### Category 8 — Migration Quality — **PASS**

- Idempotent raw SQL throughout (`op.execute("DROP TABLE IF EXISTS ...")`, `CREATE TABLE ... AS SELECT`, `UPDATE ... WHERE col IS NOT NULL`). No `op.create_table()` / `op.add_column()` / `op.create_index()` / `sa.Enum(create_type=True)` patterns.
- DROP IF EXISTS + CTAS pattern guards backup table re-creation on re-run.
- UPDATE bounded by `WHERE openai_api_key IS NOT NULL OR ...` — second run matches zero rows = no-op.
- Downgrade no-op explicitly documented and SQL-asserted by `test_migration_downgrade_no_op` (zero `UPDATE tenants` statements that restore deprecated cols).
- `*_backup_pre_tN` convention from T-3 reused → `tenants_api_keys_backup_pre_t6a`.
- Revision chain correct: `123_deprecate_tenant_provider_api_keys` revises `122_repair_pricing_snapshot_provider_tagging` (T-3 head). Verified by `test_migration_revision_metadata`.
- Backup CTAS precedes UPDATE — `test_migration_backup_precedes_update` enforces ordering.
- Schema-clone re-upgrade no-op contract verified via mock-based test pattern (gate 10 deferred to /pase-produccion live verification — same as T-3).

### Category 9 — Security — **PASS**

- Auth dependency unchanged on all 4 modified routes (`Depends(get_current_user)` preserved).
- Pydantic input validation enforced on PATCH endpoint via `TenantSettingsUpdate`.
- No SQL injection risk (parameterized via SQLAlchemy + raw SQL with no user input).
- **PII / log safety:** verified via grep — zero `logger.*api_key` / `print.*api_key` patterns in migration or modified files. Migration does NOT log key values pre-NULL (security improvement: even backup table preservation is at SQL level only, not log line).
- pip-audit: no new dependencies added.
- Rate limiting: pre-existing on routes (no changes).
- Sensitive fields: 4 deprecated keys now structurally absent from response_model output — strictly improves security posture.

### Category 10 — Tests / TDD — **PASS**

- TDD RED-first per impl-log Step 8 deliverables ordering (tests first, migration second, Pydantic third, repo fourth, factory fifth).
- 11 new tests in `test_t6a_deprecate_tenant_api_keys.py` covering all 4 acceptance criteria (A1-A4) plus extended source-level checks (factory grep, repo source inspection, Tenant + TenantSettingsUpdate exclusions, migration ordering invariants).
- Independently re-run by auditor: 11/11 PASS in 10.81s.
- Downstream regression tests (per R3 SSoT) re-run by auditor: 14/14 PASS (`test_callback_handler_usage_fallbacks.py` + `test_callback_handler.py`).
- Coverage ≥43% (gate 7 PASS, exit 0).
- Integration tests (gate 9): A4 alembic upgrade x2 deferred to /pase-produccion (brain container DOWN), mock-based contract verified.
- No `skip` / `xfail` to pass CI introduced.
- Async test fixtures pattern N/A (sync repo, sync test).
- Baseline test updates documented intentional in commit body + impl-log: `test_settings.py` (renamed methods reflecting deprecation), `test_domain_models.py` (warning suppression on deprecated default check, replaced direct field access with `gemini_api_key`), `test_tenant_repository.py` (`test_create_with_api_keys` → `test_create_with_active_keys`).

### Category 11 — Cross-cutting — **PASS**

- **datetime UTC:** N/A — no datetime fields touched. Pre-existing `default_currency: str = "USD"` at `tenant.py:90` is in `GeneralSettings` and unchanged by T-6a (out-of-scope existing tech debt).
- **Currency:** N/A — no monetary DTOs in scope.
- **Spanish neutro:** verified zero voseo (`vos|sos|tenés|podés|querés|sabés|dejá|poné|hacé|elegí|configurá|revisá|guardá|cambiá`) in migration docstring, modified files, and test docstrings. Most strings are technical English (acceptable per spanish-text.md).
- **Decisions honored cite (R6):** ✅ commit body `f6e7ad0a` includes `## Decisions honored (BINDING)` section citing all 5 binding decisions:
  1. Architect §2.4 (4 cols deprecated, gemini retained per Q4)
  2. Architect §3.2 (response DTO drops 4 fields)
  3. Auditor T-5 review + Chris zero-tech-debt directive (`_extract_tenant_key` accelerated to T-6a)
  4. T-3 `*_backup_pre_tN` convention
  5. A2 expand-contract 3-step decomposition
- **Native-First:** ✅ no `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` patterns in commits. Builder ran native venv.
- **Parallel-safety:** ✅ no `git add .` / `-A` / `-u` evidence; no `git pull` / `git revert` / `git push --force` patterns. Scoped commits.
- **R23 Owner verification:** ✅ commit `f6e7ad0a` Co-Authored-By trailer = `Claude Opus 4.7 (1M context) <noreply@anthropic.com>` — matches architect `claude_opus_required: true` HARD MANDATE.

### Category 12 — Mirror Detection — **PASS (N/A)**

- T-6a is pure deprecation — zero new abstractions, zero new utilities, zero new files outside scope-mandated artifacts (1 NEW migration + 1 NEW test file).
- Backup table convention `*_backup_pre_tN` reused from T-3 (no new convention introduced).
- Pydantic deprecation pattern (`Field(deprecated=True, exclude=True)`) is standard library — no shared abstraction needed.
- Builder Step 0 grep confirmed zero callers of `_extract_tenant_key` before deletion.

---

## Contract Compliance (business surface only)

- [x] All entities from CONTRACT § 1 implemented (Tenant, AISettings, TenantSettingsUpdate updated)
- [x] All DTOs from CONTRACT § 3 match (4 fields excluded; gemini retained)
- [x] All routes from CONTRACT § 4 use return-type annotations honored by FastAPI as response model
- [x] Repository interfaces from § 6 fully implemented (create/update no longer write deprecated cols)
- [x] CONTRACT § 8 Agentic Surfaces N/A (T-6a is iam + shared, not agentic)
- [x] Test surfaces from § 14 (4 acceptance tests A1-A4) present + extended (7 additional defense-in-depth tests)
- [x] pm-nico current-state updates: T-6a is internal cleanup, no user-facing capability change to advertise
- [x] Architecture fitness allowlists (§ 12) unchanged (823/823 PASS)

---

## Allowlist Movement

- [x] No allowlist GROWN.
- [x] Allowlists unchanged (823/823 arch fitness — same count as pre-T-6a).

---

## Native-First Audit

- [x] No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commits.
- [x] No `git add .` / `git add -A` / `git add -u` in commits (scoped commits per parallel-safety).
- [x] Pushed to `development` (not `main`); `make ci-parity` not required for development push.

---

## Downstream regression scope (R3 mandatory)

| Surface modified | Downstream test targets | gate-runner status |
|---|---|---|
| `shared/infrastructure/llm/factory.py` | `tests/shared/infrastructure/llm/` (67/67) + `tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py` + `tests/modules/sales_agent/observability/test_callback_handler.py` (197/197 combined) | PASS — covered by full-suite gate (`command_alias=test-backend`, 9041 passed). Auditor re-ran 14 callback handler tests independently → PASS |
| `modules/iam/domain/tenant.py` | `tests/modules/iam/` | PASS (186/186 covered by full suite) |
| `modules/iam/api/settings.py` | `tests/modules/iam/test_settings.py` | PASS (covered by full suite + intentional baseline update for deprecated behavior tests) |
| `modules/iam/infrastructure/repositories/tenant_repository.py` | `tests/modules/iam/test_tenant_repository.py` | PASS (covered by full suite + intentional baseline update) |
| `alembic/versions/123_deprecate_tenant_provider_api_keys.py` | `tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py` (11/11) | PASS — auditor re-ran 11/11 PASS in 10.81s |

R3 satisfied. No additional gate-runner spawn required since `command_alias=test-backend` covered all downstream surfaces.

---

## Verdict Math

- Downstream regression: PASS → no Cat 10 fail
- Categories 1/2/8/9/12: all PASS → no automatic FAIL
- Allowlists: unchanged → no FAIL trigger
- /test-backend gates 3-7, 11-13: all PASS or N/A → no FAIL
- IMPL-LOG § Skills Consulted: ✅ populated with backend-expert + tessl__fastapi + tessl__pytest-api-testing (baseline + domain skill where applicable). tessl__graceful-degradation correctly marked "NOT invoked (out of scope — no external HTTP/DB calls touched)". → no FAIL
- backend-expert/runtime-quality-checklist.md: ✅ cited explicitly in IMPL-LOG (lines 30-39 of impl-log) with decisions per anti-pattern checked → no WARN
- Two or more category WARNs: 0 WARNs → no overall WARN
- **Verdict: APPROVED**

---

## Notes for /dev-team and PM

1. **A4 deferred to /pase-produccion** is acceptable per T-3 precedent. Production deploy must run `docker exec visionarias_brain_dev alembic upgrade head` twice and verify exit 0 + `SELECT COUNT(*) FROM tenants WHERE openai_api_key IS NOT NULL OR deepseek_api_key IS NOT NULL OR kimi_api_key IS NOT NULL OR dashscope_api_key IS NOT NULL` returns 0. The backup table `tenants_api_keys_backup_pre_t6a` should be inspected for forensic audit before T-6c removes it.

2. **gemini_api_key retention** is intentional per architect §2.4 Q4. Future ticket (out of scope of T-6) should fold Gemini into LiteLLM Proxy and deprecate the field via the same expand-contract pattern.

3. **MockTenantModel in `tests/integration/test_brand_connection.py`** retains the legacy `openai_api_key` column for ORM compat. The test is `Skipped` per pre-existing condition (`landing.brand sub-module not yet implemented`). T-6c should refresh this mock alongside the physical DROP COLUMN.

4. **DeprecationWarnings on attribute access** are expected behavior — Pydantic v2 `Field(deprecated=True)` emits them. Suite-level warnings count: 113 (none are T-6a-attributable beyond expected).

5. **T-6b operational gate (Phase 2)** must verify zero structured-log reads of the 4 deprecated cols for ≥1 working day in prod before T-6c (Phase 3 — physical DROP COLUMN) can ship.

6. **No anti-default-flip concern.** T-6a does not flip a feature flag default. The closest analog (T-5 `LITELLM_PROXY_ENABLED` deletion) already executed the 4-step DELETION variant.

