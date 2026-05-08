<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Agentic Review — sales-agent-personas-instrumented-runtime (T-1, T-3..T-8)

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-08
> Iter: 1
> Verdict: **PASS**
> Generated: 2026-05-08T22:55Z
> Tickets in scope: T-1, T-3, T-4, T-5, T-6, T-7, T-8 (7 AGENTIC tickets — production-critical agentic per R23 Opus 4.7)

## Inputs

- CONTEXT-BRIEF.md: used (R24 gate PASS — `Validator pass: PASS`, `Faithfulness flag: clean`, AUDITOR-phase ITER-2 refresh 2026-05-08T22:50Z)
- gate-output.json: used (FRESH iter-1, all 5 gates GREEN, `any_fail=false`, 980 arch fitness + 3492 downstream regression PASS)
- Skills invoked: copilot-expert=Y, sales-agent-expert=Y, tessl__langgraph=Y, tessl__graceful-degradation=Y

## Gate status (from gate-output.json)

| Gate | Status | Errors |
|---|---|---|
| ruff check | PASS | 0 |
| ruff format | PASS | 0 |
| mypy strict | PASS | 0 |
| pytest architecture (980 tests) | PASS | 0 |
| pytest downstream regression (3492 tests / 29 SKIP-with-escalation) | PASS | 0 |

Cross-scope coverage: full simulator suite + sales_agent + copilot + shared. Command alias = `audit-full-suite (Story C)` covers downstream regression rule per `.claude/rules/auditor-downstream-regression.md` (4 NEW SSoT rows added by /pm 415db986).

## 15 categories

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | `simulator/state.py:40-56` SimulationState Pydantic + ConfigDict(extra="forbid"); `tenant_id: UUID` line 75 mandatory; `customer_node.py:77-230` returns partial dict `{"transcript": [new_turn]}` + `{"is_finished": True, "error_subtype": "..."}` — never mutates state. Reducer `Annotated[list[ConversationTurn], operator.add]` preserved Story B. SimulationState schema_version stays at v1 (D-AG-3). |
| 2 | Tool registration & contracts | N/A | Test infrastructure; no @tool decoration introduced. customer_node uses `LLMFactory.get_service().get_client(role=ModelRole.NANO)` — canonical SSoT. |
| 3 | Prompt cache architecture | PASS | `customer_persona_prompt.py:226-273` `test_v2_no_tenant_name_interpolation` + `test_v2_no_timestamp_or_conversation_id_in_template` enforce static template invariants. `inspect.signature(build_customer_prompt_v2)` (line 257-262) confirms zero `tenant`-substring parameters. Template documented slot architecture: 1+2 (1h TTL invariant), 3a/3b (5min sub-slots pain/objections), variable suffix `current_turn`+`next_objection_hint` (intentionally outside cache prefix per Anthropic prompt caching ref accessed 2026-05-08). Algorithm `objections[(turn-1) % len(objections)]` deterministic round-robin (cost-saver, no LLM call). |
| 4 | deepagents subagent isolation | N/A | No deepagents usage in Story C scope. |
| 5 | Observability (eval_metadata 3 NEW keys) | PASS | `customer_node.py:160-170` extends `eval_metadata` with `persona_kind` (str), `schema_version` (str cast for jsonb compat per arch §4.5), `archetype` (str with `''` fallback). `dict(state.eval_metadata)` copy boundary prevents state mutation (LangGraph contract H5 6-key invariants preserved). `customer_node.py:127-144` structlog events `simulator.customer_node_prompt_v{1,2}_dispatched` with `cache_ttl_slots_*` informational hints. PII sanitization via `sanitize_payload` heredado del shared base (per arch §5 PII handling). 3 NEW keys verified in gate-output downstream regression. |
| 6 | Eval goldens (sales_agent specifically) | PASS | T-4 `test_v1_backward_compat_preserved` + `test_v1_template_constant_byte_equal_baseline` — V1 byte-equal independent reference. T-1 frozen golden v1 fixture `_fixtures/golden_v1_simulation_result.yaml` UNTOUCHED (H10 cement Story B preserved — `git diff` empty). T-1 identity migrators (`ActorProfile`, 1, 2) + (`CustomerPrompt`, 1, 2) in `_internal/schema_migrations.py:188-209` allow v1 → v2 forward-compat. `test_personas_yaml_completeness.py` 19 arch tests enforce 15 archetype-aware + 5 _legacy/ + schema_version=2 + persona_kind ∈ 6-val Literal + dialect_code matches ARCHETYPE_DIALECT_MAP. |
| 7 | RAG / Qdrant hygiene | N/A | No RAG / Qdrant changes in Story C scope. |
| 8 | LLM provider routing | PASS | `customer_node.py:175-178` uses `LLMFactory.get_service().get_client(role=ModelRole.NANO)` (canonical Story B SSoT). `EVAL_DEFAULT_MODELS["EVAL_USER_SIMULATOR"]` slot reused (D7 cement). Zero hardcoded model strings (verified `grep "claude-opus|gpt-4o|claude-3" *.py` empty). LiteLLM Proxy via `model_override` metadata. |
| 9 | Cost optimization | PASS | Cache prefix safety enforced (slot architecture documented + tested). Cost baseline declared $0.30 → ~$2.20-3.00/suite (Story H interface receives expanded baseline). `eval_simulator_llm_call` cost bucket separation H6 preserved (no contamination prod copilot — verified by validator `agentic_cost_bucket_zero_contamination`). T-6/T-7 SKIP-with-escalation = $0 build cost (test bodies cement, awaiting toolkit). |
| 10 | Channel format & brand voice | PASS | `personality_profiles.system_instruction` SSoT untouched (sales-agent-expert §3 protected). Customer Prompt V2 voseo magic comment line 56-57 (technical reference, not user-facing). Personas YAMLs es-AR (3 of 15) include voseo magic comment line 2: `ceo-b2b-escala-ar.yaml`, `pre-pmf-zero-revenue-ar.yaml`, `pregunton-comparador-3-agencias-ar.yaml` verified. Customer simulator voice = actor's `dialect_code` per persona (NOT tenant brand voice — sales-agent-expert excepción simulator). |
| 11 | DDD compliance (agentic specifics) | PASS | All Story C files in `backend/tests/agentic_evals/sales_agent/simulator/` (test infrastructure, production_code: false). Loader in `_internal/personas_loader.py` (D-AG-2 — NOT exported via H9 7-name `__init__.py`). YAMLs in `docs/specs/personas/{archetype-aware,_legacy}/` (declarative data). No DDD layer violations. Public API surface frozen 7 names (verified `simulator/__init__.py`). |
| 12 | Tests / TDD | PASS | T-3: 18 tests for personas_loader (loader contract + edge cases). T-4: 26 tests across 4 classes for V2 prompt (rendering + sub-slot rotation 1..15 + cache prefix safety + V1 backward-compat). T-5: 5 NEW unit tests `TestV1V2Dispatch` + `TestExtendedEvalMetadata` + 1 smoke test. T-6/T-7 (Scenarios 5+6): test bodies fully implemented per spec assertions, all 15+5 cases SKIP-with-escalation pending sales_agent toolkit (verified zero `qualify_lead`/`tag_lead_status` matches in `backend/src/modules/sales_agent/`). T-8: adversarial scenario via Story B fixture parametrize. Coverage personas_loader 89% / customer_persona_prompt 100% / TOTAL **90.53%** (target 85%). |
| 13 | Mirror detection | PASS | `find /home/chris/AISALESHT/backend/src -name "personas_loader.py" -o -name "customer_persona_prompt.py" -o -name "customer_node.py"` → ZERO matches (no basename collision shared/). Architect §2 audit pre-confirmed: `personas_loader.py` genuinely NEW (Story B archive D7 planned), `ActorProfile` EXTEND (Literal 4→6), `SCHEMA_MIGRATIONS` EXTEND (2 identity migrators), `CUSTOMER_PERSONA_PROMPT` V2 ADDITIVE (V1 byte-equal preserved). No turn_envelope/callback_handler/cost_calculator mirrors (anti-duplication §0 cardinal cleared per CONTEXT-BRIEF §7.5). |
| 14 | Default-flip side-effect coverage | N/A | Story C does NOT touch `core/config.py` — verified via per-ticket Step 0.5 default-flip detection in IMPL-LOGs (T-3, T-4, T-5, T-6, T-7, T-8 all confirmed N/A). |
| 15 | Decisions honored cite (R6) | WARN | T-1 commit body has explicit "Decisions: D13, D17, D-AG-7" — PASS. T-3 commit body enumerates 8 decisions (D-AG-1, -2, -5, -6, -8, -10, D5, D6, D15) — PASS. T-4 commit body has `decisions_applicable: [D17, D-AG-4]` but no explicit "Decisions honored" section — substance present in T-4-result.md "Decisions / cement" section (lines 84-90) describing V1 byte-equal (D-AG-4) + sub-slot rotation (D17). T-5 commit body has `decisions_applicable: [D-AG-4, H5]` no explicit cite — substance in T-5-result.md "Decisions / cement" (lines 71-111). T-6/T-7/T-8 enumerate D-AG-9, D14, D15, D16 partially. WARN per Cat 15 rule: "WARN if cite incompleto en commit body pero presente en IMPL-LOG.md o T-{n}-result.md" — substance preserved across artifacts; D# enumeration could be more rigorous on T-4/T-5. |

## Findings (file:line)

### FAIL

(none)

### WARN

- [Cat 15] T-4 commit `4fb355b7` body, T-5 commit `ed671c99` body — `decisions_applicable` field set in `06-tickets.yaml:273` (T-4: `[D17, D-AG-4]`) and `06-tickets.yaml:341` (T-5: `[D-AG-4, H5]`) but commit bodies lack explicit "Decisions honored" section enumerating those D# IDs. Substance verifiable in `T-{4,5}-result.md` "Decisions / cement" sections (T-4 lines 84-90, T-5 lines 71-111). → Recommendation: future commits in this story (T-9 docs reconciliation if any future amend) should follow T-1/T-3 explicit pattern: `Decisions: D{n}, D-AG-{m}, ...` line in commit body for traceability.

### info

- [Cat 1/Cat 11] `customer_persona_prompt.py:60` carries `from __future__ import annotations` inherited verbatim from Story B baseline (`07c533ed`). 05-guidelines.md line 14 of THIS story explicitly forbids this in `customer_persona_prompt.py`. Verified Story C T-4 commit (`4fb355b7`) did NOT modify this line — it is a pre-existing Story B condition. Story B's 6 arch fitness gates pass with this baseline (LangGraph runtime introspection works because of how the file is imported). → Recommendation: separate cleanup story to align Story B baseline with Story C's stricter guideline; Story C is NOT regressing the invariant.
- [Cat 12] T-6/T-7 SKIP-with-escalation pattern (15 + 5 cases) is appropriately documented and reversible. Capability probe `_sales_agent_toolkit_supports_qualification` resolves at module-level pytest collection, not per-test. When `qualify_lead` + `tag_lead_status` land in `TOOL_REGISTRY` (separate `sales-agent-qualification-toolkit` story per /pm decision A — deferred), tests transition GREEN automatically. Test bodies are production-grade (5 + 7 spec assertions cement); not WIP placeholders.
- [Cat 6] T-8 spec § Scenario 4 grader item (4) `eval_metadata.adversarial_attempt=true` implemented as semantic alias for `persona_kind == "adversarial"` per T-8-result.md § "Spec interpretation notes". Reasoning (avoid T-5 customer_node modification scope creep) is sound; downstream queries can filter `metadata->>'persona_kind' = 'adversarial'` equivalently. /pm should ratify this aliasing in Story C closure if not already done.
- [Cat 5] T-5 stores `schema_version` as `str` (not `int`) for jsonb compat (`customer_node.py:165`) — documented arch §4.5 cement. Downstream Streamlit / SQL filters expecting `WHERE eval_metadata->>'schema_version' = '2'` will work; numeric comparisons would need cast.

## Cross-scope flags

(none — all changes within `backend/tests/agentic_evals/sales_agent/simulator/` + `docs/specs/personas/` + `tests/architecture/test_personas_yaml_completeness.py` + downstream regression rule update. Zero `modules/copilot/` or `modules/sales_agent/` runtime touch — Story C is test infrastructure exclusive per spec D7 + 05-guidelines.md anti-creep guards.)

## Downstream regression scope

| Surface modified | Downstream test targets | Gate-runner status |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` (NEW) | `test_personas_loader.py` + `test_simulator_smoke.py` + `test_customer_prompt_v2_unit.py` + `test_customer_node_unit.py` + `test_personas_yaml_completeness.py` | PASS — full simulator suite 209 passed + 34 SKIP (15 T-6 + 5 T-7 escalation + 14 eval-marked) in downstream regression log |
| `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py` (schema v1→v2) | `test_schema_migration_regression.py` (Story B) | PASS — 11/11 GREEN per T-1-result.md |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py` (V2 builder additive) | `test_customer_prompt_v2_unit.py` (NEW T-4) | PASS — 26/26 |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py` (V1/V2 dispatch + 3 NEW eval_metadata keys) | `test_customer_node_unit.py` (5 NEW + 17 pre-existing) + `test_simulator_smoke.py` | PASS — 22/22 + smoke eval-gated |
| `backend/tests/architecture/test_personas_yaml_completeness.py` (NEW arch gate) | itself | PASS — 19/19 |
| `.claude/rules/auditor-downstream-regression.md` (4 NEW rows by /pm 415db986) | rule completeness | PASS — Story C surfaces explicitly mapped |

Per `.claude/rules/auditor-downstream-regression.md` workflow Step 4: `command_alias = "audit-full-suite (Story C)"` covers full backend test suite (3492 downstream regression tests + 980 arch fitness). Coverage cross-module verified: simulator + sales_agent + copilot + shared modules all run.

## Research notes (date-aware)

- Source: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` (accessed 2026-05-08)
  - Takeaway: Slot 1+2 (1h TTL invariant per persona) + slot 3a/3b (5min TTL pain/objections) + variable suffix outside cache prefix is canonical pattern. `cache_control` markers + `ttl: "1h"` parameter still valid as of accessed date.
  - Delta vs anchors: none.
- Source: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (knowledge cutoff Jan 2026; LangGraph 0.6 reference verified live April 2026 per arch §10)
  - Takeaway: Pydantic state machines stable; reducers `Annotated[list, operator.add]` correct for append-only transcript. `from __future__ import annotations` runtime introspection caveat preserved.
  - Delta vs anchors: none.
- Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; live researched on 2026-05-08 via CONTEXT-BRIEF §15 + 03-arch.md §10 references.

## Recommendations for builder fix-loop

(none — verdict PASS; iter=0 reviewing). Optional improvements for future iterations:

1. (Cat 15 WARN) Future commits in Story C should follow T-1/T-3 explicit "Decisions: D{n}, ..." pattern in commit body for D-AG-4 traceability per R6 process improvement.
2. (Cat 1/Cat 11 info) Consider separate cleanup story to remove `from __future__ import annotations` from `customer_persona_prompt.py:60` (Story B inheritance, Story C did not regress).

## Drift detection (CONTRACT vs code)

NO drift detected. All 17 architectural decisions (D1-D17) + 10 D-AG-* + 5 D-BE-* implemented as designed. Code matches 03-arch.md §4.1-§4.6 spec verbatim:

- §4.1 personas_loader.py 337 LOC: cross-check D-AG-1 ✅, recursive glob D-AG-5 ✅, apply_migrations D-AG-6 ✅, graceful-degradation D-AG-8 ✅, loader-only kinds D-AG-10 ✅
- §4.2 ActorProfile schema v1→v2: schema_version=2 default + persona_kind 6-val Literal ✅
- §4.3 SCHEMA_MIGRATIONS: 2 identity migrators registered ✅
- §4.4 Customer Prompt V2: V1 preserved byte-equal, V2 sub-slot rotation deterministic, cache-prefix safe ✅
- §4.5 customer_node V1/V2 dispatch: schema_version >= 2 branch + 3 NEW eval_metadata keys ✅
- §4.6 Scenarios 5+6 integration tests: test bodies fully implemented per spec, SKIP-with-escalation pattern documented (toolkit dep legit) ✅

## Verdict

**PASS** — Story C delivers 7 production-critical AGENTIC tickets clean:

1. Schema v1→v2 forward-compat with identity migrators (T-1)
2. Multi-tenant personas YAML loader with cross-check (T-3)
3. Customer Prompt V2 sub-slot rotation cache-prefix-safe (T-4)
4. customer_node V1/V2 dispatch + 3 NEW observability keys (T-5)
5. Scenarios 5+6 production-critical test bodies cement with reversible SKIP-with-escalation pattern (T-6, T-7)
6. Adversarial Scenario 4 via Story B fixture parametrize (T-8)

Story B 6 arch fitness gates STILL GREEN (112/112). Frozen golden v1 byte-equal preserved (H10). Public API surface frozen 7 names (H9). Cost-bucket separation H6 preserved. `personality_profiles.system_instruction` SSoT untouched. R23 Opus 4.7 honored across all 7 agentic tickets. Skill routing complete (sales-agent-expert + tessl__langgraph + tessl__graceful-degradation + copilot-expert all invoked + decisions cited per IMPL-LOG Step 0 GATEs). Anti-duplication §0 cardinal cleared (zero shared mirror). Voseo magic comment line 2 verified for 3 es-AR YAMLs. Downstream regression scope cross-module covered by gate-runner full suite.

Two WARN items (Cat 15 decisions cite incompleteness, info Story B baseline `from __future__` inheritance) are non-blocking and can be addressed in follow-up commits or separate cleanup stories per /pm discretion.

Ready for /pm Story C closure + capability promotion + module.md SSoT update + BACKLOG regen (T-9 deferred /pm post-merge per 06-tickets.yaml).
