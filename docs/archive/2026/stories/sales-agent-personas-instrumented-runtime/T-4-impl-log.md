---
ticket: T-4
title: Customer Prompt V2 — sub-slot pain/objection rotation turn-by-turn (additive)
state: developing
phase: BUILD_T4_INPROGRESS
last_modified: 2026-05-08T21:00:00Z
owner: builder-agentic (Opus 4.7)
depends_on: [T-1]
blocks: [T-5]
---

## Skills Consulted (R23 enforcement — Step 0 GATE)

1. **sales-agent-expert** (`.claude/skills/sales-agent-expert/SKILL.md`)
   - Decisión clave: §3 Protected surfaces — `personality_profiles.system_instruction` SSoT NEVER touched. Story C is test-infra only (`backend/tests/agentic_evals/`), zero contact con sales_agent runtime. Customer Prompt V2 vive en simulator `_internal/`, frozen public API surface (H9 Story B).
   - Decisión clave: §0 Anti-duplication cardinal — `customer_persona_prompt.py` is genuinely test-infra (`tests/agentic_evals/sales_agent/simulator/_internal/`), NOT a candidate for `shared/agent_observability/` lift. V2 is additive EXTEND of existing module, not new layer.

2. **claude-api / Anthropic prompt caching** (canonical https://platform.claude.com/docs/en/build-with-claude/prompt-caching, accessed 2026-05-08)
   - Decisión clave: V2 cache prefix safety — slot 1+2 cacheable invariants (persona id, traits, dialect_code), slot 3a/3b cacheable per-persona (pain/objections), variable section is `current_turn` + `next_objection_hint` ONLY. Zero `{tenant_name}` / timestamps / conversation IDs.
   - Decisión clave: Sub-slot rotation deterministic round-robin — `objections[(current_turn-1) % len(objections)]` — NO LLM call to choose next objection. Cache prefix invariant per persona; variable suffix per turn.

3. **tessl__pytest-api-testing**
   - Decisión clave: `@pytest.mark.parametrize` for exhaustive 1..15 turn rotation testing (single test fn, multiple inputs). Factory helper `_make_actor(*, objections=...)` mirrors test_customer_node_unit.py pattern (DRY + readable).
   - Decisión clave: `pytestmark = pytest.mark.no_eval` — V2 unit tests run on default CI (no `--run-evals` opt-in needed; pure logic test, no LLM call).

## Step 0.5 — Default-flip detection

NO default flip in T-4 scope. ZERO `core/config.py` flag flip. ZERO `USE_OUTBOX_PATTERN_*` / `LITELLM_PROXY_ENABLED` / `USE_DEEPAGENTS_*` touched. Step 0.5 N/A.

## Cross-module audit (NO-NEW-LAYER per anti-duplication.md)

T-4 EDIT additive single file (`customer_persona_prompt.py`) + NEW single test file. Both inside `tests/agentic_evals/sales_agent/simulator/`. No shared abstraction candidate (test-infra only, frozen public API H9). No new layer.

```bash
# Audit grep — confirm V2 builder name not pre-existing
$ grep -rn "build_customer_prompt_v2\|CUSTOMER_PERSONA_PROMPT_V2" /home/chris/AISALESHT/backend/src/ /home/chris/AISALESHT/backend/tests/ 2>/dev/null
# (empty — V2 is genuinely new ADDITIVE)
```

## Iteration log

### Iter 1 — 2026-05-08T21:00Z → 2026-05-08T21:15Z

**Step 1 — RED**: Wrote `test_customer_prompt_v2_unit.py` with 26 tests across 4 classes (TestV2RendersAllSlots / TestV2SubSlotRotation parametrized 1..15 turns / TestV2CachePrefixSafety / TestV1BackwardCompat). Confirmed RED via ImportError on `CUSTOMER_PERSONA_PROMPT_V2`.

**Step 2 — Implement V2 additive**:
- Edited `customer_persona_prompt.py` module docstring to document V2 sub-slot architecture + cache prefix safety invariants
- Preserved `CUSTOMER_PERSONA_PROMPT_V1` + `build_customer_prompt(actor)` byte-equal
- Added `CUSTOMER_PERSONA_PROMPT_V2` template constant per 03-arch.md §4.4 reference
- Added `build_customer_prompt_v2(actor, *, current_turn)` with deterministic round-robin: `objections[(current_turn-1) % len(objections)]` if non-empty + `current_turn >= 1`, else `"ninguna pendiente"`
- Updated `__all__` to export V1+V2 templates and builders

**Step 3 — Lint/format fixups**:
- Removed RUF002 ambiguous `×` (multiplication sign) in test docstring → ASCII `cycle of 4`
- F841 unused `actor` → upgraded test to render real prompts (stronger property — verifies hint appears in rendered output, not just algorithm)
- `ruff format` applied to both files
- mypy --strict CLEAN (Success: no issues found in 2 source files)

**Step 4 — GREEN — all validators T-4 quality_gates**:

| Validator | Status | Evidence |
|---|---|---|
| be_lint (ruff check) | ✅ | All checks passed |
| be_format (ruff format --check) | ✅ | 2 files already formatted |
| be_mypy_strict | ✅ | Success: no issues found in 2 source files |
| customer_prompt_v2_unit | ✅ | 26 passed, 0 failed |
| jscpd_no_duplication | ✅ | Found 0 clones in 43ms |
| be_coverage_loader_module (T-4 portion) | ✅ | 100% coverage on customer_persona_prompt.py (16 stmts, 0 miss) — well above 85% threshold |
| Story B 6 arch fitness gates intact | ✅ | 112 tests passed (test_simulator_public_api_surface + test_simulator_no_mirrors_shared + test_simulator_writes_eval_kind_tag + test_eval_simulator_observability_invariants + test_termination_policy_registry_contract + test_schema_migrations_registry_complete) |
| Full BE arch fitness | ✅ | 980 passed (Story B H9 7-name surface frozen preserved) |
| Downstream V1 callers (test_customer_node_unit) | ✅ | 17 passed (zero V1 regression) |
| Full simulator suite | ✅ | 186 passed, 12 skipped (Postgres-dependent fixtures, unrelated) |

**Step 5 — Acceptance criteria**:

| AC | Validator path | Status |
|---|---|---|
| A1 V1 byte-equal preserved | test_customer_prompt_v2_unit.py::test_v1_backward_compat_preserved | ✅ PASS |
| A2 sub-slot rotation 15 turns | test_customer_prompt_v2_unit.py::test_v2_sub_slot_rotation_exhaustive_15_turns + 15 parametrized | ✅ PASS (16 tests for full rotation surface) |
| A3 cache prefix safety | test_customer_prompt_v2_unit.py::test_v2_no_tenant_name_interpolation + 3 sibling cache safety tests | ✅ PASS |

**Step 6 — Pre-commit hook simulation**: voseo-allowed magic comments preserved (line 56 `# voseo-allowed: actor persona dialect injection — magic comment escape per .claude/rules/spanish-text.md § "Magic comment escape" (R25 2026-05-05)`; line 64 `# voseo-allowed: actor persona dialect injection — see module docstring`; line 135 `# voseo-allowed: V2 customer prompt template — archetype-aware persona dialect AR support`). Hook silent on dry-run. Test file also includes magic comment line 29.

**Iter 1 verdict**: GREEN on first iteration (cap = 3, used = 1).

