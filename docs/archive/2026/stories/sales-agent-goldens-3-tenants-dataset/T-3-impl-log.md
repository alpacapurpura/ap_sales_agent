# T-3 Implementation Log — generate_golden_candidates.py + promote_golden.py

Story: sales-agent-goldens-3-tenants-dataset
Ticket: T-3
Owner: builder-backend-sonnet (Sonnet 4.6)
Date: 2026-05-08

## R24 CONTEXT-BRIEF Gate

- Validator pass: PARTIAL (accepted — not `_pending_`)
- Faithfulness flag: partial (accepted — not `blocking`)
- §11 gap: 1 LOW discrepancy (PII regex count mismatch, irrelevant to T-3 scope)

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | ALWAYS — load runtime-quality-checklist anti-patterns | Verified: no legacy SQLA, no datetime.utcnow, no print(), structlog used, response_model N/A (CLI scripts) |
| `tessl__fastapi` | ALWAYS — Pydantic v2 patterns, ConfigDict | Confirmed: GoldenScenarioModel uses ConfigDict(extra='forbid', frozen=True), model_dump(mode='json') for YAML serialization |
| `tessl__pytest-api-testing` | ALWAYS — test structure, mocking patterns | Used AsyncMock for run_simulation, patch.object for per-module mocking, skipif for RUN_EVALS gating |
| `tessl__graceful-degradation` | External calls — run_simulation is async | Rule 5 per-cell isolation: asyncio.gather(return_exceptions=True) + isinstance(outcome, BaseException) check |

## Step 0.5 Default Flip Detection

Not applicable. No `core/config.py` defaults touched.

## Implementation Summary

### Files created

1. `backend/scripts/generate_golden_candidates.py` (NEW)
   - Matrix: 5 tenants x 3 persona_kinds x runs_per_cell (default 5) = 75 cells
   - Pre-flight cost check: cells * $0.072, exit 2 if > budget
   - Per-cell isolation via asyncio.gather(return_exceptions=True) + Semaphore(10)
   - Deterministic seed: seed_base + hash((tenant_slug, persona_kind, run_n)) % 10_000
   - Markdown preview: English headers per arch §3.3, sorted, pipe-escaped, 120-char truncation
   - Artifact JSON: model_dump(mode='json') + _cell_* metadata fields for traceability
   - Public functions: _build_parser(), _build_matrix(), _compute_seed(), _emit_preview_markdown(), _run_one_cell(), _main_async(), main()

2. `backend/scripts/promote_golden.py` (NEW)
   - Reads sim_{uuid}.json from --artifact-dir
   - Auto-derives: termination_reason, tools_invoked (union), forbidden_tools (D17 map), voice_attributes (dimensions.keys() sorted)
   - generated_at from artifact if present; falls back to epoch UTC for deterministic idempotence
   - Writes: goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml
   - YAML: safe_dump(sort_keys=True, default_flow_style=False, allow_unicode=True)
   - Exit codes: 0=success, 2=artifact not found / persona_kind out of scope / validation error

3. `backend/tests/scripts/test_generate_golden_candidates.py` (NEW)
   - 37 tests across 8 test classes
   - Mocks: run_simulation=AsyncMock, load_actor_profile_for_tenant, get_max_turns_for_persona_kind
   - RUN_EVALS gated: TestReproducibilitySmoke

4. `backend/tests/scripts/test_promote_golden.py` (NEW)
   - 31 tests across 9 test classes
   - Mocks: load_eval_tenant patched per test class
   - RUN_EVALS gated: TestE2ESmoke

5. `backend/tests/architecture/test_goldens_cost_bucket_invariant.py` (NEW)
   - Env-gated: EVAL_GOLDENS_COST_BUCKET_VERIFY=1
   - Verifies eval_simulator_llm_call gets rows, copilot_llm_call gets zero rows
   - CI nightly opt-in (~$0.22 per run)

### Bugs fixed during implementation

1. **sys.path bug in test files**: Previous session wrote `parents[1]` (= `backend/tests/`) instead of `parents[2]` (= `backend/`) for `_BACKEND_ROOT`. This caused `ModuleNotFoundError` for both `generate_golden_candidates` and `promote_golden`. Fixed both test files.

2. **Null byte in test_promote_golden.py**: Previous session created the file with a null byte at position 17802 (in a comment). Removed via binary read/write.

3. **Markdown headers language**: Implementation used Spanish headers ("Celda", "Turnos") but tests expect English ("Cell", "Turns") matching arch §3.3. Fixed to use English.

4. **`generated_at` non-determinism**: Arch §3.4 uses `datetime.now()` for both `generated_at` and `curated_at`. Test `test_same_artifact_same_golden_id_same_actor_produces_same_yaml` pops only `curated_at`. Fixed: `generated_at` now reads from artifact if present, falls back to `datetime.fromtimestamp(0, tz=UTC)` for stability.

## Cross-module reads (read-only)

- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` — 7-name public API (H9 frozen)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` — D-AG-2 internal pin
- `backend/tests/fixtures/eval/tenants/loader.py` — Story A TenantContext loader
- `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` — T-1 GoldenScenarioModel

## Test Results

- 68 passed, 3 skipped (all gated):
  - SKIP: TestReproducibilitySmoke (requires RUN_EVALS=1)
  - SKIP: TestE2ESmoke (requires RUN_EVALS=1)
  - SKIP: TestGoldensCostBucketInvariant (requires EVAL_GOLDENS_COST_BUCKET_VERIFY=1)
- Architecture suite: 1015 passed, 1 skipped

## Deferred (requires Chris approval + cost)

- TestReproducibilitySmoke: `RUN_EVALS=1 pytest tests/scripts/test_generate_golden_candidates.py -k reproducibility` (~$0.15)
- TestE2ESmoke: `RUN_EVALS=1 pytest tests/scripts/test_promote_golden.py -k e2e_smoke` (~$0.15)
- Cost bucket DB test: `EVAL_GOLDENS_COST_BUCKET_VERIFY=1 pytest tests/architecture/test_goldens_cost_bucket_invariant.py` (~$0.22)
