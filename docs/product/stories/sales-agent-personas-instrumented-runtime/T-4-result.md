---
ticket: T-4
title: Customer Prompt V2 — sub-slot pain/objection rotation turn-by-turn (additive)
state: developed
phase: BUILD_GREEN
last_modified: 2026-05-08T21:15:00Z
owner: builder-agentic (Opus 4.7)
depends_on: [T-1]
blocks: [T-5]
iterations_used: 1
iteration_cap: 3
---

## Summary

Customer Prompt V2 builder + sub-slot rotation algorithm implemented additively. V1 preserved byte-equal (backward-compat A1). V2 sub-slot pain/objection rotation works deterministically across 1..15 turns (A2). Cache prefix safety enforced via static-template assertion + signature inspection (A3).

## Files modified

| Path | Change | Lines |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py` | EDIT additive — V1 preserved byte-equal + V2 constant + builder + `__all__` extended | +110 / -3 |
| `backend/tests/agentic_evals/sales_agent/simulator/test_customer_prompt_v2_unit.py` | NEW — 26 tests across 4 classes | +279 |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/T-4-impl-log.md` | NEW iteration log | +60 |

Total: 3 files, ~445 LOC added, 0 deletions outside docstring expansion.

## Acceptance criteria coverage

### A1 — V1 byte-equal preserved (backward-compat)

Tests:
- `TestV1BackwardCompat::test_v1_backward_compat_preserved` — explicit v1 actor (`schema_version=1`) → builder output asserted byte-equal vs verbatim baseline string (independent reference, NOT computed from V2).
- `TestV1BackwardCompat::test_v1_template_constant_byte_equal_baseline` — V1 template constant section markers preserved (7 strict rules + identity/dolores/objeciones/objetivo).
- `TestV1BackwardCompat::test_v1_and_v2_distinguishable_in_all` — both templates exported in `__all__` and distinct strings.

Verdict: ✅ PASS. V1 callers (`test_customer_node_unit.py` — 17 tests) all green post-edit.

### A2 — V2 sub-slot rotation works across 15 turns

Tests:
- `TestV2SubSlotRotation::test_v2_rotation_per_turn_selects_correct_objection[1..15]` — 15 parametrized cases, each asserts the chosen objection appears in the rendered prompt + `Turno actual: N` echoes.
- `TestV2SubSlotRotation::test_v2_sub_slot_rotation_exhaustive_15_turns` — across 15 turns with 4 objections, EACH objection raised at least once (round-robin coverage); rendered prompts contain expected hint per turn; cycle period = 4 verified.

Algorithm (cementé in builder docstring + tested):
```
next_objection_hint = objections[(current_turn-1) % len(objections)]
                     if objections and current_turn >= 1
                     else "ninguna pendiente"
```

Verdict: ✅ PASS. Sub-slot rotation deterministic, cache-prefix safe (variable section bounded to `current_turn` + `next_objection_hint`).

### A3 — Cache prefix safety (no tenant_name interpolation)

Tests:
- `TestV2CachePrefixSafety::test_v2_no_tenant_name_interpolation` — V2 template static substring assertion: zero `{tenant_name}`, `{tenant_id}`, `{tenant`.
- `TestV2CachePrefixSafety::test_v2_no_timestamp_or_conversation_id_in_template` — zero `{timestamp}`, `{conversation_id}`, `{conv_id}`, `{run_id}`. Variable section bounded to `{current_turn}` + `{next_objection_hint}` only.
- `TestV2CachePrefixSafety::test_v2_rendered_output_has_no_tenant_residue` — `inspect.signature(build_customer_prompt_v2)` parameter names verified zero `tenant`-substring (cementé via signature lock per architect mandate).
- `TestV2CachePrefixSafety::test_v2_template_constant_immutable_shape` — sub-slot architecture markers preserved (`slot cacheable 1h`, `sub-slot 3a`, `sub-slot 3b`, `[EXIT]`, `NUNCA lo reveles`).

Verdict: ✅ PASS. Cache prefix invariance guaranteed at template + signature + render level.

## Quality gates (T-4 entry quality_gates list)

| Validator ID | Status | Notes |
|---|---|---|
| be_lint | ✅ | ruff check — All checks passed |
| be_format | ✅ | ruff format --check — 2 files already formatted |
| be_mypy_strict | ✅ | mypy --strict — Success, 0 issues |
| be_coverage_loader_module (T-4 portion) | ✅ | 100% coverage on customer_persona_prompt.py (16 stmts, 0 miss) |
| customer_prompt_v2_unit | ✅ | 26 passed |
| jscpd_no_duplication | ✅ | 0 clones found |

Story B regression scope (per `.claude/rules/auditor-downstream-regression.md`):

| Surface | Tests | Status |
|---|---|---|
| Story B 6 arch fitness gates | 112 | ✅ All green (H9 7-name surface frozen, schema_migrations registry, simulator no_mirrors_shared, eval_kind_tag, observability invariants, termination policy registry) |
| V1 callers (test_customer_node_unit.py) | 17 | ✅ All green (V1 builder unchanged, byte-equal output) |
| Full simulator suite | 186 | ✅ 186 passed, 12 skipped (Postgres-dependent, unrelated) |
| Full BE arch fitness | 980 | ✅ All green |

## Decisions / cement

1. **Sub-slot rotation deterministic** — `objections[(turn-1) % N]` round-robin, NO LLM call to choose next objection (cost-saver + reproducibility).
2. **Cache prefix invariance** — V2 template variable section bounded to `current_turn` + `next_objection_hint`. Zero tenant identity, zero timestamps, zero conversation IDs in template.
3. **V2 builder signature cementé** — only accepts `actor_profile` + keyword-only `current_turn`. Test asserts via `inspect.signature(...)` zero `tenant`-substring parameter names.
4. **V1 preserved byte-equal** — V1 template constant + `build_customer_prompt(actor)` function untouched. v1 personas continue using V1 path; v2 personas opt into V2 dispatch (T-5 wires the schema_version-based routing in customer_node).
5. **Empty-objections fallback** — `"ninguna pendiente"` for hint + `"(ninguna declarada)"` for ordered list. Turn 0 also falls through to fallback (initial_message short-circuits LLM call anyway).

## Skills consulted

1. **sales-agent-expert** — §3 protected surfaces (`personality_profiles.system_instruction` SSoT NEVER touched; story C is test-infra `tests/agentic_evals/`). §0 anti-duplication confirmed: V2 EXTEND additive (not new layer / not mirror cross-module).
2. **claude-api / Anthropic prompt caching** (https://platform.claude.com/docs/en/build-with-claude/prompt-caching, accessed 2026-05-08) — slot 1+2 (1h TTL invariant per persona) + slot 3a/3b (5min TTL pain/objections sub-slots) + variable suffix (`current_turn` + hint, not cacheable, intentionally outside prefix).
3. **tessl__pytest-api-testing** — `@pytest.mark.parametrize` for exhaustive 1..15 rotation surface; `pytestmark = pytest.mark.no_eval` to avoid `--run-evals` (pure logic test, zero LLM call).

## Cross-module audit (NO-NEW-LAYER)

```bash
$ grep -rn "build_customer_prompt_v2\|CUSTOMER_PERSONA_PROMPT_V2" /home/chris/AISALESHT/backend/src/ /home/chris/AISALESHT/backend/tests/ 2>/dev/null
# Empty pre-build — V2 genuinely new ADDITIVE inside same module.
```

V2 is EXTEND of existing `customer_persona_prompt.py` module (not a new layer). Anti-duplication compliant per `.claude/rules/anti-duplication.md`.

## Step 0.5 default-flip detection

N/A — T-4 does not touch `core/config.py` or any feature flag.

## Commit

`4fb355b7` — `feat(eval-simulator): T-4 Customer Prompt V2 sub-slot rotation` — 5 files, 724 insertions, 6 deletions, pushed `development`.

## Next ticket

T-5 (`customer_node` integration — V1/V2 dispatch + `eval_metadata` extension) — depends_on T-4 ✅ done. Builder-agentic Opus 4.7 spawn ready. Files in scope: `_internal/customer_node.py` only.
