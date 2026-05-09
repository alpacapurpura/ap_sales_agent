# T-6 Implementation Log — cache.py hash composition + lookup/persist

Story: sales-agent-voice-fidelity-grader-runtime
Ticket: T-6
Builder: builder-agentic (Opus 4.7)
Started: 2026-05-09T03:30:00Z
Surface: AGENTIC test-infra (cero producción código)

## Skills Consulted (R8 Step 0 GATE)

| Skill | Why invoked | Decision cited |
|---|---|---|
| `backend-expert` (`runtime-quality-checklist.md`) | Required before commit per R8 — anti-patterns FastAPI/SQLA/test/migration not caught by mypy+ruff+pytest | Apply: SQLA 2.0 `select(Model).where(...)` (NEVER `session.query()`); `AsyncSession` async/await; structlog NOT print/logging; tenant isolation N/A (eval-only test-infra cache table not tenant-scoped). |
| `tessl__fastapi` | Pydantic v2 cache types | `MajEvalScore` already T-2 frozen=True extra=forbid — cache simply roundtrips via `model_dump_json()` / `model_validate_json()`. |
| `tessl__pytest-api-testing` | Test patterns for db fixtures + factory + parametrize | Apply: function-scoped fixtures default; mock `session.execute` for graceful-degradation test; in-memory MajEvalScore factory across tests; assert response shape NOT only "no exception". |
| `tessl__graceful-degradation` | DB fallback mandatory per Rule 2 | Apply Rule 2: DB unavailable → log structlog warn + return None (lookup) / skip persist (no exception bubbles). Each external call (DB) wrapped try/except with structured warning + dependency name + error. |
| `sales-agent-expert` | personality_profile SSoT read-only Slot 3 | Apply §3 cement: `compute_tenant_voice_hash(voice_profile)` reads `voice_profile.system_instruction` verbatim. NEVER mutate, NEVER mirror to brand_voice_summary table, NEVER fine-tune per tenant. |
| `copilot-expert` (referenced — observability bridge) | shared cost_recorder pattern referenced indirectly | T-6 does NOT call cost_recorder (state machine T-5 owns it). T-6 only reads/writes cache rows. |

## Step 0 GATE — Anti-duplication grep audit

```bash
find /home/chris/AISALESHT/backend/src -name "cache.py" -type f 2>/dev/null
# /home/chris/AISALESHT/backend/src/modules/campaigns/application/services/cache.py  (UNRELATED — campaigns redis cache)

grep -rn "def compute_cache_key\|def cache_lookup\|def cache_persist" backend/src/ backend/tests/ 2>/dev/null | grep -v __pycache__
# zero matches — genuinely NEW functions
```

Verdict: CLEAN. No mirror risk. Cache.py at `tests/agentic_evals/sales_agent/grader/_internal/cache.py` does not collide with any shared abstraction (anti-duplication.md inventory rev 2026-05-08).

## Step 0.5 — Default-flip detection

N/A. T-6 does NOT touch `core/config.py`. No flag flip.

## Files created

| File | Purpose |
|---|---|
| `backend/tests/agentic_evals/sales_agent/grader/_internal/__init__.py` | package marker (zero re-exports) |
| `backend/tests/agentic_evals/sales_agent/grader/_internal/cache.py` | hash composition + lookup/persist + graceful degradation |
| `backend/tests/agentic_evals/sales_agent/grader/test_cache_unit.py` | 9 unit tests RED→GREEN |

## Cross-module reads

- `src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_grade_cache.EvalSimulatorGradeCacheModel` — consume schema-mirror (T-2 R5 exception). READ ORM table.
- `tests.agentic_evals.sales_agent.grader.result.MajEvalScore` — consume Pydantic v2 type for serialization roundtrip.

Zero touches to `modules/copilot/`, `modules/sales_agent/{domain,application,api,observability}` runtime, frontend, or shared/ outside the eval-simulator persistence model already exposed via T-2.

## TDD workflow

1. RED — wrote `test_cache_unit.py` 9 tests (all fail, cache.py missing).
2. GREEN — wrote `cache.py` minimal implementation (compute_cache_key + 4 hash helpers + cache_lookup + cache_persist).
3. REFACTOR — minor — added module-level structlog logger + return type narrowing.
4. Validators sequential native:
   - `cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/grader/_internal/cache.py tests/agentic_evals/sales_agent/grader/test_cache_unit.py --no-cache`
   - `cd backend && .venv/bin/ruff format --check tests/agentic_evals/sales_agent/grader/_internal/cache.py tests/agentic_evals/sales_agent/grader/test_cache_unit.py`
   - `cd backend && .venv/bin/mypy tests/agentic_evals/sales_agent/grader/_internal/cache.py`
   - `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/grader/test_cache_unit.py -v`

## Decisions implemented

- **D8** (cache key 5-field composition cement): order alphabetical (`judge_set_hash`, `rubric_id`, `rubric_version`, `tenant_voice_hash`, `transcript_hash`) — composition cement frozen, drift = idempotency break.
- **D16** (cache invalidation precision): rubric_version bump → key changes → automatic invalidation. Test enforces.
- **D-BE-2** (cache table separate): cache.py reads/writes only `eval_simulator_grade_cache` table. Independent lifecycle from `eval_simulator_grade`.
- **D-BE-6** (sha256 64-char hex): all hash functions return `hashlib.sha256(...).hexdigest()` (length 64).
- **DQ7** (cache table separate, TTL=null): cache row INSERT → no expiration; invalidation only via key recomposition (D8/D16).
- **Graceful Degradation Rule 2**: DB unavailable in lookup → structlog.warn + return None. DB unavailable in persist → structlog.warn + skip. NEVER raise exception out of cache.py to caller.
- **JSON canonical order**: `json.dumps(payload, sort_keys=True, separators=(",", ":"))` — bytewise stable.

## Out of scope verified

- judge_registry.py (T-4) — not touched.
- judge_prompts.py (T-7) — not touched.
- maj_eval.py state machine (T-5) — not touched (depends on T-6 done).
- run_simulation hook (T-9) — not touched.
- Migration / models (T-1, T-2) — not touched (consumed read-only).

## Validators executed

| Validator | Status | Evidence |
|---|---|---|
| be_lint | PASS | ruff check 0 errors |
| be_format | PASS | ruff format --check 0 files reformatted |
| be_mypy_strict | PASS | mypy 0 errors on cache.py |
| pytest test_cache_unit.py 9 tests | PASS | 9/9 GREEN |

## Notes for auditor-agentic

- `cache.py` does not import LLM clients directly — pure hash + DB CRUD.
- Graceful degradation: caught exceptions logged via `structlog` + dependency name `eval_simulator_grade_cache`. NO bare `except`. NO `pass` swallow without log.
- ON CONFLICT DO NOTHING is implemented via `dialect_specific=postgresql.insert(...)` for idempotent first-writer-wins persistence.
- Composition order is FROZEN cement (anti-drift) — changing causes silent re-grade explosion in CI.
- Helper functions `compute_transcript_hash` and `compute_tenant_voice_hash` are duck-typed (accept anything with `.role/.content/.turn_number` or `.system_instruction`) per architectural design — RubricGradeRequest declares `list[Any]` and `Any` to avoid circular imports.
- Tests use lightweight stand-in protocols + dataclasses since Story D `GoldenTurnModel` and Story A `PersonalityProfile` are not imported by cache.py module surface (test-infra defensive against circular imports).
