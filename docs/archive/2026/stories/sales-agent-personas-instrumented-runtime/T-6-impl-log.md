# T-6 Impl Log — Scenario 5 integration test (qualifies out unqualified lead × 5 archetypes × 3 trials)

> Builder: builder-agentic-opus-4.7 (Claude Opus 4.7)
> State: draft → developing
> Surface: AGENTIC test-infra (production_code: false)
> Estimate: 2h · Started: 2026-05-08T22:30Z
> Depends on: T-3 (personas_loader) ✅ done, T-5 (customer_node V1/V2) ✅ done
> Blocks: T-9

## Skills Consulted (R-step-0 GATE)

| # | Skill | Why invoked | Decision captured |
|---|---|---|---|
| 1 | `sales-agent-expert` | Touching `tests/agentic_evals/sales_agent/simulator/` | §3 protected surfaces verified untouched (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup, personality_profiles.system_instruction, golden v1 fixture). T-6 only edits `test_simulator_smoke.py` (additive append) — Story B 7-name __init__ surface untouched. Anti-duplication §0: no new file created (additive append to Story B test file per D-AG-9). |
| 2 | `tessl__langgraph` | Test exercises `run_simulation` end-to-end via LangGraph state graph (Story B); verify nodes return partial dicts + reducers append-only | T-6 does NOT modify state schema or graph topology; consumes Story B `run_simulation` as-is per D-AG-9. State machine invariants honored (no `from __future__ import annotations` in `test_simulator_smoke.py` per Story B story-wide cement T-4..T-9). |
| 3 | `tessl__pytest-api-testing` | New test fn with parametrize + asyncio + DB session fixtures | Function-scoped `run_id` fixture (UUID4 fresh per test), parametrize cross-product `tenant_slug × trial_n` (5×3=15 cases), `@pytest.mark.eval` auto-skip when `--run-evals` absent (parent conftest gate). DB session via `_get_db_session()` helper Story B. Factory fixture pattern not needed — `load_actor_profile_for_tenant` is the test-time loader. |
| 4 | `tessl__graceful-degradation` | External LLM calls (sales_agent + customer simulator) — Rule 1 timeouts + Rule 2 fallbacks | Real-LLM mode: timeouts already wrapped in `agent_bridge.py` (H7 taxonomy maps `asyncio.TimeoutError` → `AgentErrorSubtype.TIMEOUT` → `TerminationReason.AGENT_ERROR`). Test asserts `termination_reason ≠ AGENT_ERROR` for ≥4/5 archetypes (D16 robustness). Failure mode handled gracefully — no raised exception bubbles. |

**No skill skipped.** All 4 mandatory skills invoked; decisions cited above.

## Diagnosis (Step 0.5 default-flip detection)

T-6 does NOT touch `backend/src/core/config.py` defaults nor flip any feature flag. No default-flip pre-audit needed.

## Scope verification (anti-duplication.md inventory cross-check)

T-6 edits `backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py` — **additive append only**, no new file. Per `06-tickets.yaml § T-6.deliverables`:
- NEW test function `test_qualifies_out_unqualified_lead` (parametrize 5×3 = 15 cases)
- Optional `actor_profile_unqualified_per_archetype` parametrize fixture (omitted — `load_actor_profile_for_tenant(slug, persona_kind="unqualified")` directly per spec D14 pattern; no helper needed since loader is test-time API)
- NO new file under `simulator/_internal/` or `simulator/`
- NO change to public surface (`simulator/__init__.py` 7-name H9 frozen)
- NO change to Story B `run_simulation` topology

Cross-codebase grep before edit:

```bash
grep -rn "test_qualifies_out_unqualified_lead" /home/chris/AISALESHT/backend/ 2>/dev/null
# Result: zero matches — function does not exist yet (RED state correct)

grep -rn "def test_qualifies_out\|def test_unqualified" /home/chris/AISALESHT/backend/ 2>/dev/null
# Result: zero matches
```

No mirror risk; new function is genuinely new.

## Sales_agent toolkit dependency — escalation path triggered

Per spec § Scenario 5 + 05-guidelines.md § Sales_agent toolkit dependency, the test asserts:

- **Forbidden close tools NOT invoked**: `enroll_*`, `send_payment_link`, `confirm_appointment_*`, `schedule_appointment`, `present_offer_ladder` (final close)
- **Required tool invoked**: `qualify_lead` (BANT/MEDDIC heuristic) — at least once

**Pre-build grep of sales_agent runtime TOOL_REGISTRY:**

```bash
grep -rn "qualify_lead\|tag_lead_status" /home/chris/AISALESHT/backend/src/modules/sales_agent/ \
  /home/chris/AISALESHT/backend/src/shared/ 2>/dev/null
# Result: zero matches.
```

`backend/src/modules/sales_agent/application/agents/sales/tools.py:107` `TOOL_REGISTRY` keys:
`send_payment_link, check_schedule, recommend_product, escalate_to_human` + `ENROLLMENT_TOOL_REGISTRY` + `SCHEDULING_TOOL_REGISTRY` + `PAYMENT_TOOL_REGISTRY`.

**Neither `qualify_lead` nor `tag_lead_status` is registered.** Per 05-guidelines.md § "Sales_agent toolkit dependency (escalation path)":

> If at build time these tools don't exist:
> - Builder T-6/T-7 SKIP test with `pytest.skip("requires qualify_lead tool — separate sales_agent toolkit story")` + emit structured warning
> - Builder logs blocker in `T-{6,7}-impl-log.md`
> - /pm decides: spawn separate `sales-agent-qualification-toolkit` story OR accept Scenario 5+6 SKIP for Story C completion

T-6 implements the scenario test BUT gates it behind a **module-level capability probe**: at collection time the test inspects `TOOL_REGISTRY.keys()`; if `qualify_lead` is missing, the test is **`pytest.skip`-ed at module setup** with a structured `structlog.warning` event documenting the missing tool name + escalation reason. The test body itself is fully implemented per spec assertions, so the moment the toolkit lands in sales_agent runtime, the test transitions GREEN automatically without further builder work.

**Escalation to /pm:**

```
@pm — Story C T-6 Scenario 5 integration test SKIPPED at collection time.
Reason: sales_agent runtime TOOL_REGISTRY lacks `qualify_lead` and
`tag_lead_status` tools required for the qualification capability assertion
contract per spec Scenario 5.

Decision needed:
(A) Spawn separate `sales-agent-qualification-toolkit` story (BE work — add
    qualify_lead + tag_lead_status to TOOL_REGISTRY with BANT/MEDDIC
    heuristic implementation, register in STAGE_TOOL_SCOPE, wire through
    ConversationPipeline). Estimate ~6h. Once landed, T-6 test
    transitions GREEN automatically (test body unchanged).

(B) Accept T-6 SKIP for Story C closure. Story C delivers loader + V2
    prompt + 15 personas + Scenarios 1-4 + 6 (nurture) GREEN. Scenario 5
    test scaffold is in place; SKIP marker tracks the escalation. T-6
    `state: developed` (test exists, exits via documented skip path with
    structured warning).

T-6 builder picks (B) by default per 05-guidelines.md guidance — Story C
scope respected, no scope creep, capability-detection skip pattern is
production-grade graceful-degradation. @pm ratifies in checkpoint.md.
```

## Iteration log

### Iteration 1 — 2026-05-08T22:35Z

**Plan:**

1. RED: write test fn `test_qualifies_out_unqualified_lead` with parametrize cross-product `tenant_slug × trial_n` (15 cases). Module-level capability probe via direct import `TOOL_REGISTRY.keys()` from sales_agent runtime → `pytestmark = pytest.mark.skipif(...)`-style gate.
2. Run test — expected SKIP path (toolkit missing). Verify SKIP message cites correct reason + structured warning emitted.
3. Run lint + format + mypy + Story B legacy invariants (H9 surface, arch fitness).

**Actions:**
- Read existing `test_simulator_smoke.py` end-to-end (847 lines) — preserved verbatim.
- Append: imports for `load_actor_profile_for_tenant`, `get_max_turns_for_persona_kind`, `_VALID_TENANT_SLUGS`.
- Append: helper `_sales_agent_toolkit_supports_qualification` — module-level capability probe.
- Append: module-level `_REQUIRED_QUALIFICATION_TOOLS` constant.
- Append: `test_qualifies_out_unqualified_lead` function with parametrize + skipif decorator.
- Run targeted tests + validators.

**Outcome (2026-05-08T22:50Z):**

- Targeted test run: 15 cases SKIPPED with documented escalation reason.
  ✅ Capability probe wired correctly; gates the parametrize cross-product
  cleanly without impacting other tests in the same module.
- `be_lint`: PASS (cleanup of 5 RUF002/RUF003/ERA001 — replaced `×` with
  `x`, replaced bullet `- ` with `* ` to dodge ERA001 false-positive on
  enroll_* line).
- `be_format`: PASS (1 file already formatted).
- `be_mypy_strict` on T-6 file: PASS (1 source file, no issues).
- `legacy_simulator_invariants_intact`: PASS (Story B 6 arch fitness gates
  112/112).
- `customer_prompt_v2_unit`: PASS (26/26 — T-4 surface untouched).
- `be_arch_fitness_full`: PASS (980/980).
- `jscpd_no_duplication`: PASS (14 clones, under 5% threshold; helper
  `_extract_tool_call_signals` extracted to prevent clone density).
- Full simulator suite: 209 passed + 29 skipped (zero failures).

**Iteration cap reached: 1 (out of 3 allowed).** No re-iteration needed.

### Commit log

- **First commit attempt** `c7873887` (2026-05-08T22:44Z): captured
  T-8 parallel session work under T-6 message via R33 BACKLOG hook race
  condition. Files committed: `test_personas_loader.py` (T-8 owned),
  `BACKLOG.{yaml,md}`, `06-tickets.yaml`, `T-8-impl-log.md`,
  `T-8-result.md`. **My T-6 files were NOT in the commit** — staging
  area got overwritten by parallel session somehow.

- **Corrective commit** `0fbe5121` (2026-05-08T22:50Z): re-staged the
  actual T-6 files (`test_simulator_smoke.py`, `T-6-impl-log.md`,
  `checkpoint.md`) and committed cleanly. Pushed to
  `origin/development`. Both commits exist in history; this corrective
  commit is the canonical T-6 attribution.

### Final state

- 06-tickets.yaml T-6: `state: developed` + transitions appended +
  `skip_with_escalation` block.
- checkpoint.md: phase BUILD_T1_T2_PARALLEL → BUILD_T6 (will be bumped
  to BUILD_T7 by T-7 builder when they pick up).
- T-9 unblocked (depends_on T-6 satisfied per `developed` state).
- @pm decision pending (A)/(B) per result file § "Sales_agent toolkit
  dependency — escalation @pm".

