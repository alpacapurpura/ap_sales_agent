# T-3 Result — personas_loader.py + tests

**Story:** sales-agent-personas-instrumented-runtime
**Ticket:** T-3 personas_loader.py (load_actor_profile_for_tenant + get_max_turns_for_persona_kind + cross-check + lru_cache)
**Builder:** builder-agentic Opus 4.7 (claude_opus_required: true)
**Surface:** AGENTIC test-infrastructure (production_code: false)
**State:** developed (tests-passing)
**Estimate:** 3h · **Actual:** ~1h (single-iteration implementation post-CONTEXT-BRIEF)
**Date:** 2026-05-08
**Commit SHA:** `cbd98b76` (pushed to origin/development 2026-05-08)

## Files delivered

| Path | Type | LOC | Purpose |
|---|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` | NEW | 337 | Multi-tenant personas YAML loader (D-AG-1 cross-check, D-AG-5 recursive glob, D-AG-6 apply_migrations, D-AG-8 graceful degradation, D-AG-10 loader-only kinds, D5 strict slug, D6 lru_cache identity, D15 max_turns matriz) |
| `backend/tests/agentic_evals/sales_agent/simulator/test_personas_loader.py` | NEW | 529 | 18 test functions covering all 11 deliverable acceptance points + 7 defensive checks |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/T-3-impl-log.md` | NEW | 89 | Implementation log + skills consulted + cross-module audit + plan |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/T-3-result.md` | NEW | this file | Acceptance summary + validators run |

**Net add:** 2 production-side files + 2 docs files. Zero deletions. Zero edits to existing files.

## Acceptance criteria (06-tickets.yaml T-3)

| ID | Description | Verifier | Result |
|---|---|---|---|
| A1 | Loader returns 5 ActorProfile instances for 5 happy tenants | `test_load_5_archetype_aware` | ✅ PASS |
| A2 | lru_cache identity check (`is` not `==`) | `test_loader_lru_cache_returns_same_instance` | ✅ PASS |
| A3 | Helper max_turns matriz returns 10/15/8/5 + KeyError for edge/negative | `test_get_max_turns_matrix` + `test_get_max_turns_for_loader_only_kinds_raises_keyerror` | ✅ PASS |
| A4 | Negative scenarios — malformed YAML / bad dialect / unknown slug raise correct exceptions | `test_yaml_malformed_raises_validation_error` + `test_invalid_dialect_code_raises` + `test_unknown_tenant_slug_raises_keyerror` | ✅ PASS |
| A5 | Cross-check D-AG-1 + parse error resilience | `test_dialect_matches_archetype_dialect_map_strict` + `test_malformed_yaml_logs_warning_no_crash` | ✅ PASS |

**5/5 acceptance criteria GREEN.**

## Validators run (04-validators.yaml T-3 quality_gates)

| Validator ID | Status | Evidence |
|---|---|---|
| `be_lint` | ✅ PASS | `ruff check tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_personas_yaml_completeness.py --no-cache` → "All checks passed!" |
| `be_format` | ✅ PASS | `ruff format --check ...` → "1 file left unchanged" (post auto-format) |
| `be_mypy_strict` (file-scoped) | ✅ PASS | `mypy --strict --ignore-missing-imports personas_loader.py test_personas_loader.py` → "Success: no issues found in 2 source files" |
| `be_mypy_strict` (dir-scoped per validator) | ⚠️ INFRA | Pre-existing CLI quirk per T-1 result.md — `mypy --strict tests/agentic_evals/sales_agent/simulator/ --ignore-missing-imports` exits 2 with "There are no .py[i] files in directory". Same baseline issue T-1 documented. NOT introduced by T-3. |
| `be_coverage_loader_module` | ✅ PASS | `pytest --cov=tests.agentic_evals.sales_agent.simulator._internal.personas_loader --cov=tests.agentic_evals.sales_agent.simulator._internal.customer_persona_prompt --cov-fail-under=85` → loader 89% / customer_persona_prompt 100% / TOTAL **90.53%** ≥ 85% |
| `scenario_1_load_archetype_aware_5_tenants` | ✅ PASS | `pytest test_personas_loader.py::test_load_5_archetype_aware` |
| `scenario_1_loader_idempotency` | ✅ PASS | `pytest test_personas_loader.py::test_loader_lru_cache_returns_same_instance` |
| `scenario_1_helper_max_turns_matrix` | ✅ PASS | `pytest test_personas_loader.py::test_get_max_turns_matrix` |
| `scenario_2_yaml_malformed` | ✅ PASS | 3 tests (malformed/invalid dialect/unknown slug) all green |
| `agentic_dialect_strict_cross_check` | ✅ PASS | `test_dialect_matches_archetype_dialect_map_strict` — 5 tenants × ARCHETYPE_DIALECT_MAP strict |
| `agentic_persona_gym_5_axis_declared` | ✅ PASS | `test_metadata_persona_gym_axes_valid` — all 15 personas (3 kinds × 5 tenants) declare valid subset of canonical 5 axes |
| `agentic_bloom_4_stage_declared` | ✅ PASS | `test_metadata_bloom_stages_valid` — all 15 personas declare valid subset of canonical 4 Bloom stages |
| `agentic_loader_yaml_parse_error_resilience` | ✅ PASS | `test_malformed_yaml_logs_warning_no_crash` — single malformed YAML → structlog warning + skip, good sibling still loadable |
| `jscpd_no_duplication` | ✅ PASS | jscpd from repo root — zero clones in personas_loader.py / test_personas_loader.py |

**13/13 functional + non-functional validators GREEN. Coverage 90.53% (target 85%).**

## Story B regression (legacy_simulator_invariants_intact + frozen_golden_v1_intact)

Per 04-validators.yaml `legacy_simulator_invariants_intact`: ALL 6 Story B arch fitness gates STILL GREEN.

| Arch fitness gate | Tests | Status |
|---|---|---|
| `test_simulator_public_api_surface.py` (H9 frozen 7 names) | 1 test | ✅ PASS |
| `test_simulator_no_mirrors_shared.py` (basename collision) | 1 test (loader does not collide with shared) | ✅ PASS |
| `test_simulator_writes_eval_kind_tag.py` (eval_metadata invariants) | 1 test | ✅ PASS |
| `test_eval_simulator_observability_invariants.py` (R5 schema mirror) | 39 tests | ✅ PASS |
| `test_termination_policy_registry_contract.py` (H8) | 18 tests | ✅ PASS |
| `test_schema_migrations_registry_complete.py` (H1 + 2 NEW migrators T-1) | 52 tests | ✅ PASS |
| `test_personas_yaml_completeness.py` (Story C T-2 NEW gate) | 19 tests | ✅ PASS |

**131 architecture tests GREEN.**

`frozen_golden_v1_intact`: `git diff HEAD --name-only -- _fixtures/golden_v1_simulation_result.yaml` → empty (untouched). H10 byte-equal preserved.

`legacy_client_simulator_intact`: not modified; D6 Story B preserved.

## Full simulator suite

`pytest tests/agentic_evals/sales_agent/simulator/ -v --no-header -q` → **204 passed, 12 skipped (Postgres unreachable native, pre-existing), 0 failed.**

## Skills Consulted

Per `.claude/rules/anti-duplication.md` § Step 0 GATE:

| Skill | Why invoked | Decision applied |
|---|---|---|
| `copilot-expert` | Best-effort writes (structlog warning equivalent for graceful-degradation Rule 2) | Loader is genuinely NEW per CONTEXT-BRIEF §7.5 audit. Cross-module grep `load_actor_profile_for_tenant\|personas_loader\|load_personas` returns ZERO. Anti-duplication §0 cardinal cleared. |
| `sales-agent-expert` | tocas `tests/agentic_evals/sales_agent/simulator/_internal/` test-infra | §3 protected surfaces verified NO TOUCH: closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup, personality_profiles.system_instruction. H9 7-name surface (`__init__.py`) untouched (loader lives in `_internal/` per D-AG-2). |
| `tessl__langgraph` | applies cross-cutting | Loader is NOT LangGraph state (returns Pydantic ActorProfile directly, never participates in StateGraph compose). Therefore `from __future__ import annotations` PERMITTED per 05-guidelines.md line 14. |
| `tessl__graceful-degradation` | external read (filesystem yaml parse) | Rule 2 fallback applied: malformed YAML during `_scan_personas_directory` → `structlog.warning` + skip file + continue. OSError also caught for read failures. Other personas remain loadable. Validator `agentic_loader_yaml_parse_error_resilience` covers. |
| `tessl__pytest-api-testing` | new pytest fixtures + parametrize | Function-scoped autouse fixture `_clear_loader_caches` (default scope), `Generator[None, None, None]` return type (mypy strict), `@pytest.mark.no_eval` marker (no LLM calls — pure unit tests), error-path tests assert exception types AND error message content. |
| `claude-api` | not invoked | N/A — loader uses no LLM call. |

## Cross-Module Audit (NO-NEW-LAYER) — completed

```bash
# 1. Cross-codebase loader patterns
grep -rn "load_actor_profile_for_tenant\|personas_loader\|load_personas" backend/ docs/
# Result: ZERO matches. Function genuinely NEW. Story B archive doc D7 references this as "planned" but no impl exists.

# 2. Existing ActorProfile + apply_migrations + ARCHETYPE_DIALECT_MAP
# All three exist; loader REUSES via direct import (no mirror).
```

**Verdict:** loader is genuinely NEW. Three EXTERNAL imports (Story A `tests.fixtures.eval.tenants.loader.ARCHETYPE_DIALECT_MAP`, Story B `simulator.actor_profile.ActorProfile`, Story B `simulator._internal.schema_migrations.{apply_migrations,CURRENT_SCHEMA_VERSIONS}`). All declared in `05-guidelines.md` line 80 cross-module whitelist.

## Architecture decisions applied

Per 06-tickets.yaml T-3 `decisions_applicable`:

| Decision | Where applied | Evidence |
|---|---|---|
| D3 (path layout) | `_PERSONAS_ROOT = _BACKEND_ROOT.parent / "docs/specs/personas/"` | `personas_loader.py:97` |
| D4 (Pydantic ConfigDict frozen=True) | Loader returns existing frozen ActorProfile | `actor_profile.py:41` (Story B) |
| D5 (strict slug fail-fast) | `KeyError` listing valid 5 slugs | `personas_loader.py:230-235` |
| D6 (lru_cache process-scoped) | `@cache` on both `_scan_personas_directory` + `load_actor_profile_for_tenant` | `personas_loader.py:140, 205` |
| D15 (max_turns matriz) | `_MAX_TURNS_BY_PERSONA_KIND` 4-key dict + helper | `personas_loader.py:121-128, 305-329` |
| D-AG-1 (dialect cross-check strict) | `ValueError` BEFORE Pydantic validate when `dialect_code != ARCHETYPE_DIALECT_MAP[slug]` | `personas_loader.py:280-292` |
| D-AG-2 (private surface, NOT exported via `__init__.py`) | Module under `_internal/`, no edit to `simulator/__init__.py` | filesystem |
| D-AG-5 (recursive glob excluding `_legacy/`) | `_PERSONAS_ROOT.rglob("*.yaml")` + `if _LEGACY_DIR_NAME in path.parts: continue` | `personas_loader.py:170-172` |
| D-AG-6 (apply_migrations chain) | `apply_migrations("ActorProfile", raw, target_version)` consuming Story B registry | `personas_loader.py:269-271` |
| D-AG-8 (graceful-degradation Rule 2) | `try/except yaml.YAMLError → log + skip` + OSError handling | `personas_loader.py:174-191` |
| D-AG-10 (loader-only kinds raise KeyError) | `_MAX_TURNS_BY_PERSONA_KIND` excludes edge + negative; `get_max_turns_for_persona_kind` raises | `personas_loader.py:121-128, 318-326` |

## Constraints honored

- **Story B H9 surface frozen 7 names** — `simulator/__init__.py` `__all__` UNTOUCHED. Loader lives in `_internal/`, consumed via direct import.
- **Story B H10 frozen golden v1 byte-equal** — `_fixtures/golden_v1_simulation_result.yaml` UNTOUCHED. Identity migrator (T-1) handles forward-compat.
- **lru_cache identity check** — `test_loader_lru_cache_returns_same_instance` asserts `a is b` (not `==`).
- **ARCHETYPE_DIALECT_MAP strict cross-check** — D-AG-1 enforced via 1 unit test (positive) + 1 unit test (negative ValueError).
- **`from __future__ import annotations`** — PERMITTED per 05-guidelines.md line 14 (loader is NOT in LangGraph runtime introspection chain).
- **YAML safe_load** — `yaml.safe_load` only; no `yaml.load()` (security).
- **Spanish neutro** — error messages, structlog events, comments all in Spanish neutro / English. No voseo.
- **Voseo magic comment** — module docstring includes `# voseo-allowed:` line per `.claude/rules/spanish-text.md` § R25 (technical reference to es-AR archetype, not user-facing string).
- **Tenant isolation** — N/A here (personas catalog is shared, not per-tenant DB). Loader takes `tenant_slug` arg + cross-checks Story A `ARCHETYPE_DIALECT_MAP`.

## Out of scope (explicitly NOT included)

Per 06-tickets.yaml T-3 `out_of_scope`:
- Customer prompt V2 (T-4 — already done, commit `4fb355b7`)
- Customer node V1/V2 dispatch (T-5 — pending)
- Scenarios 5+6 integration (T-6/T-7 — pending)
- Adversarial Scenario 4 (T-8 — pending)

## Post-merge follow-ups

Per 05-guidelines.md line 146 + line 200, post-merge `/pm` MUST:
- Append `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` row to `.claude/rules/auditor-downstream-regression.md` SSoT table → downstream tests `test_personas_loader.py` + `test_simulator_smoke.py` for Stories D/E/F/I consumers.

## Iteration count

**1 iteration** to GREEN (no rework loop). Single shot:
1. RED test file written (18 test functions covering 11 deliverable + 7 defensive)
2. GREEN loader implementation per 03-arch.md §4.1 reference
3. Lint cleanup (UP033 lru_cache→cache, TRY004 ValueError→TypeError, ERA001 commented code, B007 unused loop var, SIM300 yoda condition, RUF003 ambiguous `×`)
4. Mypy strict cleanup (yaml import-untyped, Generator return type, unused arg-type ignores)
5. Format auto-applied
6. jscpd cleanup (refactored 2 duplicated YAML fixtures via `_build_persona_dict` helper — zero clones in T-3 files)

**Skills invoked, cross-module audit completed, R23 mandatory Opus 4.7 honored, anti-duplication cardinal cleared.**

## Last line

```
done -> /home/chris/AISALESHT/docs/product/stories/sales-agent-personas-instrumented-runtime/T-3-result.md
```
