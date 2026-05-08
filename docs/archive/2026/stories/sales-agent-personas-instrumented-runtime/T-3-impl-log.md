# T-3 Implementation Log — personas_loader.py + tests

**Ticket:** T-3 personas_loader.py (load_actor_profile_for_tenant + get_max_turns_for_persona_kind + cross-check + lru_cache)
**Surface:** AGENTIC test-infrastructure (production_code: false)
**Builder:** builder-agentic Opus 4.7 (claude_opus_required: true)
**Started:** 2026-05-08
**Depends on:** T-1 (commit 34f0ce69) ✅ + T-2 (commit b92b5871) ✅
**Blocks:** T-5, T-6, T-7, T-8

## Skills Consulted

| Skill | Why invoked | Decision applied |
|---|---|---|
| `copilot-expert` | tocas `simulator/_internal/` test-infra w/ best-effort writes equivalent (structlog warning) | Loader is genuinely NEW per CONTEXT-BRIEF §7.5 audit. No mirror. Anti-duplication §0 cardinal applies — grepped `load_actor_profile_for_tenant` + `personas_loader` cross-codebase = ZERO matches. Justified NEW. |
| `sales-agent-expert` | tocas `tests/agentic_evals/sales_agent/simulator/_internal/` | §3 protected surfaces NO TOUCH (verified): closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup, personality_profiles.system_instruction, dialect_catalog.yaml, golden v1 fixture. Loader is in `_internal/` NOT public — H9 surface (7 names) untouched. |
| `tessl__langgraph` | applies cross-cutting | Loader is NOT LangGraph state (it returns Pydantic ActorProfile directly). Therefore `from __future__ annotations` PERMITTED per 05-guidelines.md line 14 (loader is not part of LangGraph runtime introspection chain). |
| `tessl__graceful-degradation` | external read (filesystem yaml parse) | Rule 2 fallback applied: single malformed YAML in `_scan_personas_directory` → emit `structlog.warning` + skip file + continue. Other personas still loadable. No crash. Validator `agentic_loader_yaml_parse_error_resilience` covers. |
| `tessl__pytest-api-testing` | new pytest fixtures + parametrize | Function-scoped fixtures (default), parametrize for 5-tenant happy load, `@pytest.mark.no_eval` marker (no LLM calls — pure unit tests), assert response shape (ActorProfile fields + identity for lru_cache), error-path tests (KeyError / FileNotFoundError / ValueError / yaml.YAMLError). |
| `claude-api` | not invoked (no Anthropic SDK changes) | N/A — loader uses no LLM call. |

## Cross-Module Audit (NO-NEW-LAYER)

Grep evidence (anti-duplication.md §0 cardinal):

```bash
# 1. Cross-codebase loader patterns
grep -rn "load_actor_profile_for_tenant\|personas_loader\|load_personas" backend/ docs/
# Result: ZERO BE implementations — function genuinely NEW.
#         Story B archive doc references this function as "planned D7" but no impl exists.

# 2. Existing ActorProfile class
grep -rn "class ActorProfile" backend/
# Result: ONE class at simulator/actor_profile.py (Story B v2 post T-1).
#         REUSED via import (not mirrored).

# 3. apply_migrations + CURRENT_SCHEMA_VERSIONS
grep -rn "apply_migrations\|CURRENT_SCHEMA_VERSIONS" backend/tests/agentic_evals/
# Result: ONE registry at _internal/schema_migrations.py (Story B + T-1).
#         REUSED via import.

# 4. ARCHETYPE_DIALECT_MAP (Story A)
grep -rn "ARCHETYPE_DIALECT_MAP" backend/tests/fixtures/eval/tenants/
# Result: ONE map at loader.py (Story A archived).
#         REUSED via import for D-AG-1 cross-check.
```

**Verdict:** loader is genuinely NEW (no precedent). Three EXTERNAL imports (Story A loader, Story B actor_profile, Story B schema_migrations). All declared in 05-guidelines line 80 cross-module whitelist. Zero mirror.

## Default-Flip Detection (Step 0.5)

This ticket does NOT touch `backend/src/core/config.py`. No flag flips. Step 0.5 N/A.

## Plan (TDD RED → GREEN → REFACTOR)

1. **RED** Write `test_personas_loader.py` with 11 test functions per ticket deliverable list. Loader doesn't exist yet → all tests fail at import time.
2. **GREEN** Implement `_internal/personas_loader.py` minimal per 03-arch.md §4.1 reference.
3. **Iterate** until validators GREEN (cap=3).
4. **Verify** Story B 6 arch fitness gates STILL GREEN + Story C new gate (T-2) STILL GREEN.
5. **Push** + result.md.

## Iteration log

### Iteration 1 — single-shot GREEN (2026-05-08)

**Steps executed:**
1. RED — Wrote `test_personas_loader.py` with 18 test functions (11 deliverable + 7 defensive). Run failed at import time as expected (loader module did not exist).
2. GREEN — Wrote `_internal/personas_loader.py` per 03-arch.md §4.1 reference impl. Same-day completion — loader cleared all 18 tests on first run.
3. Lint cleanup pass:
   - UP033 (`@lru_cache(maxsize=None)` → `@cache`)
   - TRY004 (`ValueError` → `TypeError` for non-dict YAML root)
   - ERA001 (removed commented-out `# actor_goal: MISSING` — moved to docstring comment above the dict)
   - B007 (`for slug, expected_dialect in _HAPPY_TENANTS:` → `_expected_dialect`)
   - SIM300 (yoda condition swapped LHS/RHS)
   - RUF003 (ambiguous `×` MULTIPLICATION SIGN → "across" in section comment)
4. Mypy strict cleanup:
   - `import yaml` → `import yaml  # type: ignore[import-untyped]` (mirroring Story B test_schema_migration_regression.py pattern)
   - autouse fixture return type annotated `Generator[None, None, None]`
   - Removed 3 unused `# type: ignore[arg-type]` on `get_max_turns_for_persona_kind("edge"/"negative")` calls — both ARE valid PersonaKind Literal values (mypy clean), only rejected at runtime per D-AG-10
   - Replaced `for kind in ("happy", "nurture", "unqualified")` with `valid_kinds: list[PersonaKind] = [...]` to satisfy mypy strict Literal narrowing
5. Format applied (`ruff format`) — 2 files reformatted, 0 issues remaining.
6. jscpd cleanup — 1 internal duplication detected (28-token clone between dialect-mismatch fixture YAML write block and parse-error-resilience YAML write block). Refactored via shared `_build_persona_dict(...)` helper; zero clones remain in T-3 files.

**Tests:**
- 18/18 GREEN in test_personas_loader.py
- 11/11 deliverable acceptance tests GREEN (run by name explicitly)
- 13/13 T-3 quality_gates validators GREEN (`be_lint`, `be_format`, `be_mypy_strict` file-scoped, `be_coverage_loader_module` 90.53%, scenario_1 × 3, scenario_2, agentic_dialect_strict_cross_check, agentic_persona_gym_5_axis_declared, agentic_bloom_4_stage_declared, agentic_loader_yaml_parse_error_resilience, jscpd_no_duplication)

**Story B + Story C T-2 regression:**
- 131 architecture tests GREEN (Story B 6 gates + Story C T-2 gate `test_personas_yaml_completeness.py`)
- Frozen golden v1 fixture UNTOUCHED (H10 byte-equal preserved)
- Full simulator suite: 204 passed, 12 skipped (Postgres unreachable native — pre-existing), 0 failed

**Iteration count:** 1 (cap was 3). No rework loop needed.

**Final state:** state=developed (tests-passing). Awaiting orchestrator → gate-runner → auditor-agentic.

### Files created (this session)

- `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` (337 LOC)
- `backend/tests/agentic_evals/sales_agent/simulator/test_personas_loader.py` (529 LOC)
- `docs/product/stories/sales-agent-personas-instrumented-runtime/T-3-impl-log.md` (this file)
- `docs/product/stories/sales-agent-personas-instrumented-runtime/T-3-result.md`

### Files NOT touched (verification)

- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` — H9 7-name surface frozen ✅
- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` — H10 byte-equal ✅
- `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py` — Story B / T-1 baseline ✅
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` — Story B / T-1 baseline ✅
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py` — Story C / T-4 baseline ✅
- `docs/specs/personas/archetype-aware/*.yaml` — Story C / T-2 baseline (15 files unchanged) ✅
- `docs/specs/personas/_legacy/*.yaml` — Story C / T-2 baseline (5 files unchanged) ✅
- `backend/tests/architecture/test_personas_yaml_completeness.py` — Story C / T-2 baseline ✅
- `backend/tests/fixtures/eval/tenants/loader.py` — Story A baseline (consumed via import) ✅
- `backend/src/core/config.py` — no flag flip (Step 0.5 N/A)
- `backend/src/modules/sales_agent/` — no production code changes ✅
- All `§3` sales-agent-expert protected surfaces — UNTOUCHED ✅

