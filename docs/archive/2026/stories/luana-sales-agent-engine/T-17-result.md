# T-17 result

**Status:** GREEN (with V-F-x-2 waiver per outcome §7.2 + Story 6 precedent)
**Commit:** none (verification only)
**Validators:** V-NF-1, V-F-x-1, V-F-langgraph, V-F-slot-5-voice-port
**Date:** 2026-05-12

## Summary

Cross-package integration smoke + ModuleRegistry discovery verification.

## Results

| Validator | Status | Notes |
|---|---|---|
| V-NF-1 (uv sync --all-packages) | GREEN | 23 packages resolve cleanly |
| V-F-x-1 (cross-package smoke) | GREEN | All Story 7 imports + D-T3 + D-T6 + state + graph |
| V-F-x-2 (aggregate pytest) | WAIVED | Pre-existing Story 4/5 conftest collision per Story 6 precedent |
| V-F-langgraph (graph compiles) | GREEN | agent_app + AgentState mandatory keys |
| V-F-slot-5-voice-port | GREEN | compose_prompt accepts voice_port: BrandVoicePort |
| ModuleRegistry (9 modules) | GREEN | sales_agent discovered |

## Files Modified

NONE — pure verification ticket.

## AISALESHT Impact

ZERO — V-NF-4 invariant preserved.
