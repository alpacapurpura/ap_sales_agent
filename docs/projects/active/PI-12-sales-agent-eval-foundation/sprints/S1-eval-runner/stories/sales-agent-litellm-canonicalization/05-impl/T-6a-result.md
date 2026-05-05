# T-6a Result

**Ticket:** T-6a — Migration deprecation tenant API keys (Phase 1 expand-contract)
**State:** tests-passing — awaiting `gate-runner` + `auditor-backend` independent verdict
**Builder:** Claude Opus 4.7 (per architect mandate `claude_opus_required: true`)
**Date:** 2026-05-05

## Acceptance verdict matrix

| ID | Criterion | Verifier | Verdict | Evidence |
|---|---|---|---|---|
| A1 | Post-migration, 0 tenants with non-NULL deprecated API keys | `pytest tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py::test_post_migration_zero_non_null` | PASS | UPDATE statement asserts SET 4 cols = NULL with WHERE non-null guards (idempotent re-run no-op) |
| A2 | `factory._extract_tenant_key` method DELETED entirely | bash `! grep -q 'def _extract_tenant_key' backend/src/shared/infrastructure/llm/factory.py` | PASS | `grep -c 'def _extract_tenant_key' src/shared/infrastructure/llm/factory.py` = 0 (only docstring history references on line 14) |
| A3 | TenantResponseDTO (`AISettings`) excludes 4 deprecated fields | `pytest tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py::test_dto_excludes_deprecated_fields` | PASS | `AISettings.model_dump()` confirmed to exclude all 4 deprecated cols, retain `gemini_api_key` (active per arch §2.4 Q4) |
| A4 | Migration idempotent (run 2x no error) | `docker exec visionarias_brain_dev alembic upgrade head` (×2) | DEFERRED to `/pase-produccion` | Brain container DOWN at build time. SQL idempotency contract verified via mock-based migration tests (4 tests covering DROP IF EXISTS, WHERE non-null guards, downgrade no-op, CTAS-precedes-UPDATE ordering — same pattern as T-3) |

## Native tests run

| Suite | Result |
|---|---|
| Ruff lint (`src/ tests/`) | PASS — All checks passed |
| Ruff format (`src/ tests/`) | PASS — 2323 files already formatted |
| Architecture fitness (`tests/architecture/`) | PASS — 823/823 |
| T-6a tests (`test_t6a_deprecate_tenant_api_keys.py`) | PASS — 11/11 |
| IAM module (`tests/modules/iam/`) | PASS — 186/186 |
| LLM factory downstream (`tests/shared/infrastructure/llm/`) | PASS — 67/67 |
| Observability downstream (per `auditor-downstream-regression` table) — copilot + sales_agent | PASS — 197/197 |
| Full BE suite + coverage (`pytest -m "not integration" --cov=src/modules --cov=src/shared`) | PASS — 9041 passed / 35 skipped / 16 deselected / 113 warnings (648.94s, exit 0). Coverage `fail_under=43` met implicitly (exit 0). |

## Files changed

```
NEW    backend/alembic/versions/123_deprecate_tenant_provider_api_keys.py
NEW    backend/tests/modules/iam/test_t6a_deprecate_tenant_api_keys.py
MOD    backend/src/modules/iam/domain/tenant.py
MOD    backend/src/modules/iam/api/settings.py
MOD    backend/src/modules/iam/infrastructure/repositories/tenant_repository.py
MOD    backend/src/shared/infrastructure/llm/factory.py
MOD    backend/tests/modules/iam/test_settings.py            (intentional baseline update — old tests asserted deprecated behavior)
MOD    backend/tests/modules/iam/test_domain_models.py        (intentional baseline update — replaced direct deprecated-field assertions with active gemini_api_key + warning suppression)
MOD    backend/tests/modules/iam/test_tenant_repository.py    (intentional baseline update — `test_create_with_api_keys` → `test_create_with_active_keys`, asserts `gemini_api_key` persistence)
```

9 files (1 NEW migration, 1 NEW test file, 7 MOD files in src + tests).

## Decisions honored

- **Architect 03-arch-be.md §2.4 BINDING:** 4 cols deprecated, `gemini_api_key` retained per Q4 ratification.
- **Architect 03-arch-be.md §3.2 BINDING:** response DTO drops 4 fields.
- **Auditor T-5 review BINDING + Chris zero-tech-debt directive:** `_extract_tenant_key` deleted now in T-6a (originally T-6c, accelerated; zero callers verified).
- **T-3 BINDING:** `*_backup_pre_tN` convention applied → `tenants_api_keys_backup_pre_t6a`.
- **A2 expand-contract 3-step decomposition BINDING:** T-6a is Phase 1; T-6b operational gate + T-6c physical DROP COLUMN remain in scope of later tickets.

## Risks / limitations

1. **A4 verification deferred to `/pase-produccion`:** brain container DOWN at build time. SQL-string idempotency contract verified via mock-based tests; actual `alembic upgrade head` 2x will run during production deploy.
2. **`gemini_api_key` retention:** intentional per architect Q4 — landing extractors still call Gemini directly outside the LiteLLM Proxy. Future ticket (out of scope for T-6) will fold Gemini into the proxy.
3. **MockTenantModel in `tests/integration/test_brand_connection.py`:** retains the legacy column (`openai_api_key`) for ORM compat. Test is `Skipped` per pre-existing condition (`landing.brand sub-module not yet implemented`). T-6c will refresh this mock.
4. **DeprecationWarnings on attribute access:** Pydantic `Field(deprecated=True)` emits `DeprecationWarning` when the attribute is read. Legacy tests in `test_domain_models.py` were updated to use only active fields or wrap deprecated access in `warnings.catch_warnings()`. Suite runs clean (113 warnings total — none are T-6a-attributable beyond what's expected).

## Out-of-scope (per architect)

- Physical `DROP COLUMN` (T-6c, blocked by T-6b operational gate).
- `gemini_api_key` deprecation (out of scope per Q4 ratification).
- T-5 LITELLM_PROXY_ENABLED flag deletion (already shipped — commit 28617716).

## Commit (pending)

Will be appended after `git add` + `git commit` + `git push origin development`
in scope-bounded mode (only files this session touched).
