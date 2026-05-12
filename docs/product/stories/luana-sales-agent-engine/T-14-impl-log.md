# T-14 Implementation Log

**Ticket:** Lift sales_agent observability subfolder (D-T6 subclass pattern — EXCLUDE eval_simulator)
**Owner:** builder-agentic Opus 4.7 (R23 mandatory)
**Date:** 2026-05-12
**Status:** GREEN
**Commit (luana-platform):** `84c3377`

## Skills Consulted

- **copilot-expert** — Anti-duplication cardinal §0. Confirmed sales_agent observability/recording/callback_handler.py + turn_envelope.py must SUBCLASS from luana_core_observability.recording (shared base lives in luana-core-observability per Story 2). NEVER mirror.
- **sales-agent-expert** — §0 anti-duplication cardinal: "LIFT-TO-SHARED" pattern. Surfaces compartidas con copilot inventory cross-referenced — SalesAgentCallbackHandler extends BaseAgentCallbackHandler.
- **.claude/rules/anti-duplication.md** — Cross-checked inventory: 5 forbidden classes (FXResolver/CostCalculator/PricingResolver/BaseObservabilityContext/BaseAgentCallbackHandler) must NOT be declared in luana-core-sales-agent src/.
- **.claude/rules/copilot-observability.md** — module-scoped repos (LlmCallRepository, TraceEventRepository, RoutingLogRepository) implement structural Protocols from luana-core-observability; persistence/models/ store SalesAgent-specific schema mirrors.

## Workflow

1. **cp -r per-subfolder explicit** per §1.6 — `__init__.py` + 4 subfolders (recording, persistence, workers, domain_events). DELIBERATELY SKIPPED `eval_simulator/`.
2. **Verified eval_simulator NOT lifted** — `test -d .../eval_simulator` returns false. V-AG-5 prep complete.
3. **sed import path rewrites** per §1.4:
   - Self: `from src.modules.sales_agent.` → `from luana_core_sales_agent.`
   - Stories 2-6 modules
   - Channels FIRST (specific) before agent_observability fallback
   - All shared.* per §1.4 mapping
4. **Verified zero leaks** — grep `(from src\.|import src\.)` over observability/ = empty.
5. **Ruff check passed** — no formatting drift.
6. **Verified D-T6 subclass invariant** via 3 layers:
   - grep `class SalesAgentCallbackHandler` confirms subclass declaration: `class SalesAgentCallbackHandler(BaseAgentCallbackHandler):`
   - grep `class SalesAgentObservabilityContext` confirms: `class SalesAgentObservabilityContext(BaseObservabilityContext):`
   - Anti-mirror sweep: 5 forbidden classes (FXResolver/CostCalculator/PricingResolver/BaseObservabilityContext/BaseAgentCallbackHandler) ZERO declarations in luana-core-sales-agent src/
   - Runtime smoke test: `issubclass(SalesAgentCallbackHandler, BaseAgentCallbackHandler)` + `issubclass(SalesAgentObservabilityContext, BaseObservabilityContext)` both PASS
7. **Copied tests** — 7 files including __init__.py (excluded eval simulator tests).
8. **Sed tests** — same patterns + patch() string literal handling per T-12 learning.
9. **Ran pytest** — 26 passed + 10 failed. The 10 fail are inherited Story 4 luana-core-platform tech debt (LeadModel.messages FK references MessageModel.lead_id column that does not exist).
10. **Verified AISALESHT untouched + eval_simulator absent** + committed luana-platform side.

## Verification matrix

| Check | Status | Evidence |
|---|---|---|
| AISALESHT untouched | OK | `git diff HEAD --name-only \| grep sales_agent` empty |
| eval_simulator NOT lifted | OK | `test -d .../observability/eval_simulator` returns false |
| Zero `src.*` leaks | OK | grep `(from src\.\|import src\.)` over observability/ = 0 |
| D-T6 subclass — SalesAgentCallbackHandler | OK | `class SalesAgentCallbackHandler(BaseAgentCallbackHandler):` |
| D-T6 subclass — SalesAgentObservabilityContext | OK | `class SalesAgentObservabilityContext(BaseObservabilityContext):` |
| D-T6 anti-mirror (5 forbidden classes) | OK | Zero declarations of FXResolver/CostCalculator/PricingResolver/BaseObservabilityContext/BaseAgentCallbackHandler |
| Runtime issubclass smoke | OK | Both assertions pass |
| Ruff clean | OK | All checks passed |
| Tests collection succeeds | OK | 36 tests collected |
| Tests passing | 26/36 | 26 pass; 10 pre-existing Story 4 SQLA tech debt (LeadModel.messages FK) |

## Test execution

```
26 passed, 10 failed in 137.52s
```

10 fail breakdown: all of them are blocked by `LeadModel.messages = relationship(MessageModel, foreign_keys="MessageModel.lead_id")` — Story 4 luana-core-platform CRM has this relationship declared, but `MessageModel.lead_id` column does not exist on the model. Any test that triggers SQLA registry init (test_observability_context, test_real_trace_persistence, test_repositories) hits this. Inherited from T-12 documented tech debt.

## Cardinal invariants honored

- ★ AISALESHT UNTOUCHED (V-NF-4 cardinal)
- ★ eval_simulator NOT lifted (Luana v0.2.0 territory)
- ★ tests/agentic_evals NOT lifted (Luana v0.2.0 territory)
- ★ D-T6 anti-mirror: ZERO declarations of FXResolver/CostCalculator/PricingResolver/BaseObservabilityContext/BaseAgentCallbackHandler in luana-core-sales-agent src/
- ★ SalesAgentCallbackHandler + SalesAgentObservabilityContext correctly SUBCLASS the shared bases from luana-core-observability (Story 2 cement preserved)
- ★ D-T3 cardinal preserved: zero PersonalityCompiler imports in lifted observability files

## Notes

- 6 tests pass cleanly including `TestInheritance::test_handler_inherits_base_agent_callback_handler` — D-T6 invariant covered by both runtime smoke + dedicated unit test
- Persistence/models/ subfolder is sales-agent-scoped storage of SalesAgent-specific schema mirrors (e.g., `sales_agent_llm_call`, `sales_agent_trace_event`, `sales_agent_routing_log`) — NOT mirrors of shared base classes; they represent agent-specific columns appended to the cost-bucket-separated tables
- `recording/factory.py` uses imports `from luana_core_observability.cost.fx_resolver import FXResolver` + `from luana_core_observability.pricing.resolver import PricingResolver` — consuming shared abstractions, not declaring them
