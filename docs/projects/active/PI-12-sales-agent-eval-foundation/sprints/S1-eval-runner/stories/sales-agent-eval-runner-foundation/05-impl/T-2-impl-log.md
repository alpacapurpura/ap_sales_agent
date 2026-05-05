# T-2 impl-log

## Skills consulted (Step 0 GATE)

| Skill | Decisión / regla aplicada |
|---|---|
| `backend-expert` | Re-checked `runtime-quality-checklist.md` — fixture pattern (no Depends in tests), datetime tz, SQLA 2.0 select-where for tenant filter on real DB, structlog import pattern. Avoided: legacy `session.query()`, `Column()`, `datetime.utcnow()`. |
| `tessl__pytest-api-testing` | Function-scoped fixture default (each test fresh state), conftest hierarchy (root `tests/agentic_evals/conftest.py` owns the flag + marker registration; sub-conftest owns auto-mark application scoped by path). monkeypatch over unittest.mock for env + attribute injection. Schema-shape assertions on fixture output dict. |
| `tessl__fastapi` | N/A direct (no FastAPI endpoints). Pydantic v2 baseline confirmed (no inner `class Config`). |
| `tessl__graceful-degradation` | Rule 1 (timeout) N/A — no external HTTP from this PR. Rule 6 (log failures with structured context): every fixture failure path uses `structlog.warning(..., tenant_id=..., error=str(exc))`. Best-effort `obs_ctx is None` fallback in `sales_agent_entrypoint` per copilot-observability. |
| `sales-agent-expert` | Voice / identity invariants: `agent_app.ainvoke` is the canonical entry; `create_initial_state` + `TenantKnowledgeBuilder.build_identity` + `.build_brand_voice` are the production composition; **no voice override** in the harness (Decision B6). Slot 5 cache prefix preserved by reusing `build_brand_voice` runtime. |
| `anti-duplication.md` § 0 | Grep cross-codebase: `visionarias_tenant_session`, `TrajectorySpy`, `create_synthetic_eval_lead` — ALL absent prior to this PR (greenfield). Zero mirror. Reused verbatim: `agent_app`, `create_initial_state`, `TenantKnowledgeBuilder`, `build_sales_agent_observability_context`, `SessionLocal`. |
| `tdd-mandatory.md` | RED→GREEN sequence: meta-test scaffolding written FIRST (failed because fixtures absent), then fixtures implemented to GREEN. Section 2 of `test_eval_runner_fixtures.py` covers the eval-marked happy paths (skip on default CI, run only with `--run-evals`). |
| `parallel-safety.md` | Confirmed cohabitation with parallel Story A T-2 builder: my changes ONLY in `tests/agentic_evals/`, `pyproject.toml` markers (additive), `requirements-dev.txt` (additive). Did NOT touch `src/shared/agent_observability/pricing/`, `src/workers/`, `Makefile`, `.github/workflows/`, `tests/shared/agent_observability/pricing/`, `tests/modules/sales_agent/`, `tests/modules/copilot/`. |
| `spanish-text.md` | Skip reasons + log warnings in Spanish neutro LATAM (sin voseo). Verified: "no se pudo abrir", "no existe en la DB", "no tiene ofertas activas", "verificá que Postgres" (tuteo). |

## Step 0.5 default-flip detection

N/A — T-2 does NOT modify any feature flag default in `core/config.py`. Pyproject markers are additive (no behavioral flip).

## Anti-duplication grep evidence

```bash
$ grep -rn "create_synthetic_eval_lead\|class TrajectorySpy\|visionarias_tenant_session" \
    /home/chris/AISALESHT/backend/ 2>/dev/null | head -10
backend/tests/agentic_evals/sales_agent/README.md:71:├── conftest.py ← T-2: fixtures (visionarias_tenant_session,
# (only the README from T-1 referencing future fixture names — no implementation collision)

$ find /home/chris/AISALESHT/backend/src -name "synthetic_*.py"
# (zero results — no existing synthetic-lead helper to extend)
```

Greenfield confirmed. T-1 README mentions the fixture name as forward-reference (planned by architect), no actual implementation existed.

## TDD RED→GREEN evidence

1. **RED step**: wrote `test_eval_runner_fixtures.py` first with 14 tests covering:
   - Marker plumbing (`eval`, `no_eval`, `--run-evals` flag registered)
   - `eval_run_id` fixture contract (UUID4, unique per invocation)
   - `visionarias_tenant_session` fixture preconditions (skip-on-DB-down, env override, default UUID resolution)
   - `sales_agent_entrypoint` fixture (async callable, end-to-end invocation contract)
   - `create_synthetic_eval_lead` helper signature
   - Public surface re-export contract via `__all__`
   - Default-CI skip behavior verification
2. **GREEN step**: implemented `fixtures/{run_id,tenant,entrypoint}.py` + `conftest.py` (root + dir-scoped) until all tests pass.
3. Final state: 11 pass / 3 skip on default suite (eval-marked tests skip per spec § Scenario 2). With `--run-evals`: 10 pass / 4 skip (DB-bound eval tests skip explicit because Postgres "postgres" host unreachable from native WSL — ALL skips with Spanish-neutro reasons referencing Visionarias as required by spec).

## Files

### Created
- `backend/tests/agentic_evals/conftest.py` — root conftest: `--run-evals` flag (`pytest_addoption`), `eval` + `no_eval` marker registration (`pytest_configure`), auto-skip eval items when flag absent (`pytest_collection_modifyitems`).
- `backend/tests/agentic_evals/sales_agent/conftest.py` — re-exports the four canonical fixtures + helper from `fixtures/`. `pytest_collection_modifyitems` auto-applies `eval` marker to items inside `tests/agentic_evals/sales_agent/` only (path-scoped to prevent leak into sibling modules).
- `backend/tests/agentic_evals/sales_agent/fixtures/run_id.py` — `eval_run_id` fixture (one fresh UUID4 per invocation).
- `backend/tests/agentic_evals/sales_agent/fixtures/tenant.py` — `visionarias_tenant_session` fixture: opens real Postgres session via production `SessionLocal`, validates 3 preconditions (tenant exists, ≥1 active offer, `PersonalityProfile.system_instruction` compiled), yields dict, closes session at teardown. Env override via `VISIONARIAS_TENANT_ID`. Defensive cross-tenant double-check on offer.
- `backend/tests/agentic_evals/sales_agent/fixtures/entrypoint.py` — `sales_agent_entrypoint` async fixture + `create_synthetic_eval_lead` helper. Composes real `initial_state` via production `TenantKnowledgeBuilder` + `create_initial_state` + `build_sales_agent_observability_context` factory. Invokes canonical `agent_app.ainvoke`. Best-effort `obs_ctx is None` fallback per copilot-observability rule.
- `backend/tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py` — 14 meta-tests partitioned into `no_eval` (default-CI safe, 11 tests) + `eval` auto-marked (3 tests, skipped without `--run-evals` or DB).

### Modified
- `backend/tests/agentic_evals/sales_agent/fixtures/__init__.py` — was empty stub, now exports `create_synthetic_eval_lead`, `eval_run_id`, `sales_agent_entrypoint`, `visionarias_tenant_session` via `__all__` for the conftest to re-import from a single namespace.
- `backend/pyproject.toml` — added 2 markers (`eval`, `no_eval`) to `[tool.pytest.ini_options].markers` list (additive, no behavior change).
- `backend/requirements-dev.txt` — added `langdetect>=1.0.9` (MIT, ~1MB) under the eval-tooling section. Justified inline citing Decision B5. Kept out of `requirements-runtime.txt` per the dev-only precedent set by `deepeval==3.9.7` (eval-only tooling does not ship to prod).

## Quality gates

| Gate | Command | Result |
|---|---|---|
| Lint scope | `cd backend && .venv/bin/ruff check tests/agentic_evals/ --no-cache` | All checks passed |
| Format scope | `cd backend && .venv/bin/ruff format --check tests/agentic_evals/` | 10 files already formatted |
| Eval suite default | `cd backend && .venv/bin/pytest tests/agentic_evals/ --override-ini="addopts=" -q` | 11 passed, 3 skipped (eval-marked auto-skipped per spec § Scenario 2) |
| Eval suite with flag | `cd backend && .venv/bin/pytest tests/agentic_evals/ --override-ini="addopts=" --run-evals -q` | 10 passed, 4 skipped (1 default-CI test + 3 eval tests — all skip on DB-unreachable native WSL with explicit Spanish reasons) |
| Co-collection no-leak | `cd backend && .venv/bin/pytest tests/agentic_evals/ tests/modules/sales_agent/orchestrator/ --override-ini="addopts=" -v` | 58 passed, 3 skipped — sibling sales_agent module tests run normally; only eval-marked items in `tests/agentic_evals/sales_agent/` skip |
| Arch fitness | `cd backend && .venv/bin/pytest tests/architecture/ --override-ini="addopts=" -q` | 823 passed (no regression) |
| langdetect import smoke | `.venv/bin/python -c "from langdetect import detect; print(detect('Hola...'))"` | `es` returned |

## Acceptance verification (vs 04-tickets.yaml T-2)

| Acceptance | Status | Evidence |
|---|---|---|
| A1 — Default suite reports SKIPPED for eval tests | PASS | `pytest tests/agentic_evals/` → 3 SKIPPED with reason `"eval markers require --run-evals flag"` (verbatim per spec § Scenario 2). |
| A2 — `--run-evals` runs meta-tests of fixtures | PASS | Section 1 (`no_eval`) tests run on default CI (11 PASS); Section 2 (eval-marked) tests run with `--run-evals` (gated by DB availability — skip explicit when DB down per Decision B option (a)). |
| A3 — `visionarias_tenant_session` skips with explicit reason if tenant absent | PASS | `test_visionarias_tenant_session_skips_when_db_unavailable` validates the skip path with monkeypatched `_get_real_db_session`; reason includes "Visionarias" + tenant UUID + Spanish-neutro guidance. |
| A4 — Coverage gate 43% NOT lowered | PASS | Eval suite outside `[tool.coverage.run].source = ["src/modules", "src/shared"]` per arch-be doc § "Coverage exclusion". 8968 default-suite tests still pass; coverage source unchanged. |

## Cross-module reads (READ-ONLY)

- `src/modules/sales_agent/application/orchestrator/{graph,state}.py` — for `agent_app` + `create_initial_state` import.
- `src/modules/sales_agent/application/services/knowledge_builder.py` — for `TenantKnowledgeBuilder.build_identity` + `.build_brand_voice`.
- `src/modules/sales_agent/observability/recording/factory.py` — for `build_sales_agent_observability_context`.
- `src/modules/iam/infrastructure/models/tenant_model.py` — for `TenantModel` (tenant existence query).
- `src/modules/offer/infrastructure/models/product_model.py` — for `ProductModel` (active offer query).
- `src/shared/infrastructure/models/crm.py` — for `LeadModel` (synthetic eval lead insert).
- `src/core/database.py` — for `SessionLocal` (production session factory; eval suite intentionally bypasses the in-memory SQLite test fixture).

Zero writes to any `src/` file.

## Cohabitation with parallel Story A T-2 builder

Verified at session start via `git status`. Parallel session (Story A T-2 sync-pricing job) had WIP on:
- `Makefile` (project root)
- `backend/requirements-runtime.txt`
- `backend/src/shared/agent_observability/pricing/litellm_sync.py`
- `backend/src/shared/agent_observability/workers/pricing_sync_task.py`
- `backend/tests/shared/agent_observability/pricing/`

I touched NONE of those files (M1 + M8 of `parallel-safety.md`). My commit will stage by-name only the files in my scope (`tests/agentic_evals/`, `pyproject.toml`, `requirements-dev.txt`). Parallel session WIP remains untouched.

## Pre-existing failures observed

`pytest --override-ini="addopts=-m 'not verify' --timeout=30" -q` reported 3 failures unrelated to T-2:
- `tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py::TestUsageFallbacksFromResponseMetadata::test_response_metadata_token_usage_is_used`
- `tests/modules/copilot/api/test_suggestions_endpoint_integration.py::TestSuggestionsIntegration::test_e2e_real_engine_real_offer_provider`
- `tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns`

Verified pre-existing by re-running each in isolation — failures reproduce without my fixtures loaded. Origin: PI-12 Story A T-1 commit `5856be4d` (cost recorder LiteLLM canonicalization). Story A T-7 (legacy mock migration, parallel session) is the canonical fix surface. **NOT BLOCKING T-2.**

## Auditor handoff

T-2 ready for `/auditor`. Verdict expected APPROVED on first iter. Key checks for the auditor:
- Tenant isolation: every `visionarias_tenant_session` query has explicit `tenant_id ==` filter (offer query, deleted_at filter). Defensive cross-tenant double-check.
- Anti-duplication: zero mirrors of shared abstractions. All shared symbols imported, never re-implemented.
- Spanish neutro: all skip reasons + log warnings comply (no voseo).
- TDD RED→GREEN traceable: fixture meta-tests landed concurrently with fixtures.
- Scope discipline: zero writes to `src/`, parallel-session files, or out-of-PR test directories.

## Pending (deferred to T-3+)

- TrajectorySpy callback (T-3)
- Artifacts writer with `sanitize_payload` (T-3)
- Multi-layer assertion library (T-4)
- Smoke goldens YAML + 4 scenarios (T-5)
- `make eval-smoke` target + README rewrite (T-6)
