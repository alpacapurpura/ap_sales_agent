# T-18 result

**Status:** GREEN
**Commit:** `9d497d6` (luana-platform main)
**Validators:** V-AG-1, V-AG-2, V-AG-3, V-AG-4, V-AG-5, V-AG-6, V-AG-7, V-AG-8
**Date:** 2026-05-12

## Summary

8 NEW architectural fitness tests cementing Story 7 invariants. All 26 individual assertions GREEN. §3 protected surfaces sha256 snapshot v1 captured for drift detection on subsequent Story 7+ modifications.

## Tests Created (`core/tests/architecture/`)

| Test | Validator | Assertions | Result |
|---|---|---|---|
| `test_story7_brand_agnostic_engine.py` | V-AG-1 | 4 | GREEN — no `if brand ==`, no brand-slug equality, no Clerk app IDs, no API_KEY/SECRET/TOKEN literals |
| `test_story7_no_forward_module_imports.py` | V-AG-2 | 3 | GREEN — no top-level imports luana_core_{campaigns,advertising,social_media}; scheduling allowed only TYPE_CHECKING / function-local (AST walk) |
| `test_sales_agent_uses_voice_port_no_direct_compiler_import.py` | V-AG-3 (D-T3 cardinal) | 2 | GREEN — zero `PersonalityCompiler` imports/references in `luana-core-sales-agent/src/` |
| `test_voice_port_interface_complete.py` | V-AG-4 | 3 | GREEN — BrandVoicePort Protocol has exactly 2 async methods (compile_system_instruction + get_voice_metadata) |
| `test_no_eval_framework_lifted.py` | V-AG-5 | 3 | GREEN — eval_simulator + agentic_evals NOT in luana-core-sales-agent (Luana v0.2.0 territory) |
| `test_no_mirror_observability_in_sales_agent.py` | V-AG-6 (D-T6 cardinal) | 6 | GREEN — 5 forbidden classes + 1 forbidden function ZERO declarations in sales_agent src/ |
| `test_voice_compiler_ssot_still_intact_story7.py` | V-AG-7 (Story 5 regression) | 2 | GREEN — only `luana-core-brand-studio.domain.personality` declares PersonalityCompiler |
| `test_sales_agent_protected_surfaces_intact.py` | V-AG-8 | 3 | GREEN — §3 13 protected files hash-stable vs snapshot v1 |

## §3 Protected Surfaces Snapshot v1

File `core/tests/architecture/_snapshots/sales_agent_protected_surfaces_v1.json` captures sha256 of 13 canonical §3 files (POST-sed POST-ruff at lift moment). Future Story 7+ modifications to these files require architect ratification + snapshot bump.

Snapshot baseline keys:
- `api/closer_studio.py`, `api/ws.py`, `api/enrollments.py`
- `application/orchestrator/smart_debounce_runner.py`, `application/orchestrator/tool_call_dedup.py`
- `infrastructure/external/output_manager.py`, `infrastructure/external/buffer_service.py`, `infrastructure/external/safety_service.py`
- `infrastructure/ws_manager.py`
- `infrastructure/models/message_model.py`, `infrastructure/models/enrollment_model.py`, `infrastructure/models/prompt_version_model.py`, `infrastructure/models/agent_state_checkpoint_model.py`
- `application/tools/payment/webhook_providers.py`, `application/tools/scheduling/webhook_providers.py`
- `workers/follow_up_engine.py`
- `domain/enrollment.py`

(Adjusted final list = actual lifted paths; `application/services/enrollment_service.py` substituted where ticket spec assumed different name — documented in test docstring.)

## Run

```bash
cd ~/luana-platform && uv run pytest core/tests/architecture/test_story7*.py core/tests/architecture/test_sales_agent*.py core/tests/architecture/test_voice_*.py core/tests/architecture/test_no_*.py -x -q
# 8 passed in <2s
```

## D-T3 + D-T6 Cardinal Cement

- D-T3: V-AG-3 + V-AG-4 + V-AG-7 triple-cement (sales_agent never imports PersonalityCompiler · port frozen at 2 methods · PersonalityCompiler stays in brand-studio domain only)
- D-T6: V-AG-6 cardinal (zero observability mirror — FXResolver, CostCalculator, PricingResolver, BaseObservabilityContext, BaseAgentCallbackHandler ZERO declarations in sales_agent)

## Next

T-19 finalization (lint + AISALESHT untouched + DEFERRED-FILES + README polish + checkpoint state transition developing → developed).
