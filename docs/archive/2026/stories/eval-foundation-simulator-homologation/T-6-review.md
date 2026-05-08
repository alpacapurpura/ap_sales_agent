<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — T-6 Customer node + persona prompt v1 + EVAL_LLM_ROLES + concurrency

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-08
> Iter: 1
> Verdict: **APPROVED**
> Generated: 2026-05-08T22:00:00Z

## Inputs
- CONTEXT-BRIEF.md: used (validator APPROVED, faithfulness clean)
- gate-output.json (full suite): used; T-6-scope GREEN per impl-log (17/17 ticket tests + 79/79 simulator + 5/5 arch smoke)
- Skills invoked: copilot-expert=N (T-6 is sales_agent test-infra), sales-agent-expert=Y, tessl__langgraph=Y, tessl__graceful-degradation=Y (LLM call wrapped)

## Gate status (T-6 scope)
| Gate | Status | Errors |
|---|---|---|
| ruff | PASS (4 fixes) | 0 |
| ruff-format | PASS | 0 |
| mypy --strict | PASS 5/5 | 0 |
| pytest (T-6 ticket-tests, 17/17) | PASS | 0 |
| full simulator suite (79/79) | PASS | 0 |
| arch fitness smoke (no_new_sales_agent_module_imports + copilot_anchors, 5/5) | PASS | 0 |

## 15 categories
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | `_internal/customer_node.py:76-181` — async node returns partial state dict (`{"transcript": [new_turn]}` or `{"is_finished": True, "error_subtype": "..."}`), NEVER mutates. Honors `Annotated[list, operator.add]` reducer declared on `SimulationState.transcript`. NO `from __future__ import annotations` in customer_node.py. |
| 2 | Tool registration | PASS | n/a |
| 3 | **Prompt cache architecture** | **PASS (anchor of ticket — cache prefix safety)** | `_internal/customer_persona_prompt.py:52-78` — `CUSTOMER_PERSONA_PROMPT_V1` constant frozen. Build function signature `build_customer_prompt(actor_profile: ActorProfile)` accepts NO `tenant_id`/`tenant_name` (cement via type signature — line 89-119). Module docstring §"Cache-prefix safety" §"Voice constraints" explicitly forbid `{tenant_name}` mid-block + timestamps + conversation IDs. H1 versioning honored (V1 frozen — bumps register migrator). |
| 4 | deepagents subagent isolation | PASS | n/a |
| 5 | Observability | PASS | `_internal/customer_node.py:130-141` — propagates `eval_metadata` (state.eval_metadata) into LLM `config={"metadata": ...}` so callback handler subclass (T-5) writes the 6-key invariant per row. |
| 6 | Eval goldens | PASS | n/a — T-9 owns frozen golden. |
| 7 | RAG / Qdrant hygiene | PASS | n/a |
| 8 | LLM provider routing | PASS | `_internal/customer_node.py:126-128` — uses `LLMFactory.get_service().get_client(role=ModelRole.NANO, temperature=0.8)` canonical shared dispatch. NO hardcoded model wire-name in customer_node — `model_override=EVAL_DEFAULT_MODELS["EVAL_USER_SIMULATOR"]` resolved via `_internal/llm_roles.py:54-56` registry. |
| 9 | Cost optimization | PASS | `_internal/concurrency.py:45-65` — `EVAL_SIMULATOR_SEMAPHORE = asyncio.Semaphore(EVAL_SIMULATOR_MAX_CONCURRENCY)` cap default 10, env override `EVAL_SIMULATOR_MAX_CONCURRENCY`. Wraps ONLY rate-limited resource (LLM ainvoke), per `tessl__graceful-degradation` Rule 5 (per-dependency error isolation). |
| 10 | **Channel format & brand voice** | **PASS** | `_internal/customer_persona_prompt.py:52-78` — actor persona dialect injection respects `actor.dialect_code` (BCP-47). Magic comment escape `# voseo-allowed: actor persona dialect injection — magic comment escape per .claude/rules/spanish-text.md § "Magic comment escape" (R25 2026-05-05)` line 43-45. Customer LLM emits actor-persona voice (NOT tenant brand voice — this is the simulator-only excepción documented in `sales-agent-brand-voice.md` § Excepción simulator). Agent runtime continues to compile brand voice from personality_profile (heredado, NOT overridden). |
| 11 | DDD compliance | PASS | All files under `tests/agentic_evals/sales_agent/simulator/_internal/`. No production code touched. |
| 12 | Tests / TDD | PASS | 17 ticket tests in `test_customer_node_unit.py` — A1 (initial-turn-zero, dialect injection `test_dialect_es_ar_voseo`, no-tenant-leak, pain-points/objections rendering, template-v1 shape), A2 (semaphore acquired during LLM call, module singleton, default cap 10), A3 (eval registry isolation from production SSoT). |
| 13 | Mirror detection | PASS | `_internal/llm_roles.py:1-31` — module docstring justifies WHY EVAL_LLM_ROLES is separate from `LLM_ROLE_BY_SITE` (5 reasons documented). `_internal/concurrency.py` introduces module-singleton semaphore (no parallel layer). Step 0 grep evidence in impl-log. |
| 14 | Default-flip side-effect coverage | NA | T-6 touches zero `core/config.py` defaults. |
| 15 | Decisions honored cite (R6) | WARN | Ticket `decisions_applicable: [D3, H1, H4]` (06-tickets.yaml:373). D3 (eval-only registry) + H1 (versioned prompt) + H4 (semaphore cap) all visible in code + commit `07c533ed` body inline; no formal "## Decisions honored" section. |

## D3 verification (production SSoT clean)
```bash
grep -rn "EVAL_USER_SIMULATOR\|EVAL_LLM_ROLES" backend/src/
# → cero matches. SSoT untouched. ✓
```

## Findings (file:line)

### FAIL
None.

### WARN
- [Cat 15] `06-tickets.yaml:373` declares `decisions_applicable: [D3, H1, H4]` → commit body cites inline but no formal "## Decisions honored" R6 section.

### info
- [Cat 9] `_internal/concurrency.py:14-28` — module docstring documents "per-worker" semantics (module-level binding lives in worker process; pytest -n / CI shards each get own semaphore). Matches `OutboundRateLimiter` design philosophy. Excellent design clarity.
- [Cat 10] `_internal/customer_persona_prompt.py:71-78` — strict 7-rule list embedded in prompt: dialect respect, short messages, [EXIT] token, no-personaje-roto, no-emojis-excesivos, solo-mensaje. Defense-in-depth H10 against persona breaking out of role.
- [Cat 1] `_internal/customer_node.py:104-112` — Turn 0 short-circuit: emits `actor_profile.initial_message` verbatim WITHOUT semaphore acquire (rate-limited resource untouched). Smart concurrency optimization.
- [Cat 5] `_internal/customer_node.py:144-152` — empty response → `{"is_finished": True, "error_subtype": "http_error"}` graceful degradation (H7 taxonomy). structlog warning emitted with `simulation_id` breadcrumb.

## Cross-scope flags
None.

## Research notes
- Source: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` + `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` (accessed 2026-05-08)
- Takeaway: Customer prompt v1 honors anti-pattern "NO {tenant_name} interpolation mid-cacheable-block" via type signature cement.

## Recommendations for builder fix-loop
None.

## Drift detection
NO drift. T-6 deliverables map literal to `06-tickets.yaml:382-386`.

## Verdict
APPROVED

## Findings
- 0 FAIL / 1 WARN (Cat 15 R6 cite trivial) / 4 info

## Cited paths
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py`
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py`
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py`
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py`
- `backend/tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py`
- `docs/product/stories/eval-foundation-simulator-homologation/T-6-impl-log.md`

<!-- @pm: T-6-review.md ready (verdict=APPROVED). Cache-prefix safety + actor dialect handling exemplary. -->
