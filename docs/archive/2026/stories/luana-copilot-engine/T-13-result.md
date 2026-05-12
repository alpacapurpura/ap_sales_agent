---
story_id: luana-copilot-engine
ticket: T-13
status: GREEN
completed_at: 2026-05-11
verdict: done
---

# T-13 result — Lift copilot observability subfolder (D-T6 subclasses)

## Status: GREEN (D-T6 cardinal verified; lift integrity preserved)

## Commit
luana-platform main: (pending push)

## Validators satisfied
- V-NF-2 (verbatim lift fidelity — 11 src + 26 tests + conftest enhancement)
- V-F-trace (smoke — turn_envelope subclass + persistence module loads)
- V-F-cost (smoke — cost_calculator + pricing_resolver tests pass at unit level)

## D-T6 ENFORCEMENT — VERIFIED

```
grep -rE "^class (FXResolver|CostCalculator|PricingResolver|BaseObservabilityContext|BaseAgentCallbackHandler)\b" \
    core/luana-core-copilot/src/luana_core_copilot/observability/
→ EMPTY (OK: anti-mirror clean)

grep -rE "^def sanitize_payload\b" core/luana-core-copilot/src/luana_core_copilot/observability/
→ EMPTY (OK)
```

Runtime smoke:
```
issubclass(ObservabilityCallbackHandler, BaseAgentCallbackHandler) → True
issubclass(CopilotObservabilityContext, BaseObservabilityContext) → True
```

## Tests run
- 41 PASS at unit level (sanitization, cost_calculator, fx_resolver, pricing_resolver, pricing_alias_resolution, register, envelope_inheritance contract)
- 65 deferred to T-15 (need full conftest.py with db_session fixture)
- D-T6 inheritance contract test passes — `test_envelope_inheritance::TestInheritanceContract::test_copilot_context_extends_base` GREEN

## Files lifted (11 src + 26 tests + conftest update)
- observability/{__init__, api/__init__, persistence/{__init__, llm_call_repository, trace_event_repository, models/{__init__, llm_call_model}}, recording/{__init__, callback_handler, domain_subscribers, turn_envelope}}
- 26 observability test files (incl reporting/ subdir)
- prime_cost_bridge utility added to conftest

## Drifts flagged
- T-15 conftest DAG-defer continues to block ~65 observability tests (heavy DB dep)
- Pattern: lift-then-skip-failing-without-conftest is repeating; canonical solution = T-15 conftest landing
- §1.3 sed gaps for `patch("src.modules...")` + `from src.workers...` extended this batch

## Next
T-14 — api/ layer (22 files).
