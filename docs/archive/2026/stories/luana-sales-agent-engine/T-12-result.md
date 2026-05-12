# T-12 Result

**Status:** GREEN
**Commit (luana-platform):** `6f52ace`
**Date:** 2026-05-12

## Summary

Lifted application/services (14 src) + application/services/closer_studio (4 src) + application/event_bus + application/payment_event_handlers + application/scheduling_event_handlers — 22 src files total from AISALESHT to luana-platform with mechanical sed (§1.4).

★ **D-T3 audit:** Re-confirmed knowledge_builder.build_brand_voice does NOT call PersonalityCompiler directly — it consumes `BrandDataPort.get_brand_knowledge` (hexagonal port). NO refactor needed. T-11's `compose_prompt(voice_port=...)` is the canonical D-T3 entry point. Legacy chat.py → state["brand_voice"] flow preserved verbatim for byte-equal back-compat.

Dependency: added `fastembed>=0.2.0` for semantic_router intent classification.

Sed extension: applied to test file `patch("src.modules.X")` string literals beyond §1.4 import statements.

## Validators

| Validator | Status | Evidence |
|---|---|---|
| V-NF-2 | ✅ | Zero `from src.*` / `import src.*` leaks in 22 T-12 src files |
| V-F-intent prep | ✅ | semantic_router lifted + fastembed installed |
| V-AG-3 prep | ✅ | Zero direct PersonalityCompiler imports; only 2 brand_studio imports both inside TYPE_CHECKING (BrandVoicePort + StyleAnchorStore) |

## Tests

- ✅ 19/19 T-12 module import smoke
- ✅ 4/4 TestBrandVoiceSlot5 PASS (D-T3 surface — build_brand_voice returns PersonalityProfile.system_instruction)
- ✅ 29/49 service tests overall pass
- ⚠️ 20 pre-existing failures categorized as Story 4 luana-core-platform tech debt (CRM LeadModel.messages FK mismatch + `from src.modules.social_proof` leak in `links/ports/social_proof.py`) + T-7 batch 2 tech debt (`infrastructure/prompts/base.py` templates_dir absolute path). Documented in impl-log § D-4 with scope assignment.

## D-T3 Architecture clarification (for ratification by /pm)

Original ticket prompt suggested knowledge_builder voice_port refactor. Audit revealed AISALESHT architecture was already D-T3 compliant via existing BrandDataPort. T-11 established the canonical D-T3 entry point at `compose_prompt`. Two paths now coexist for slot 5 BRAND_VOICE source:

1. **Legacy path (preserved verbatim):** `chat.py → ConversationPipeline.build_brand_voice → knowledge_builder.build_brand_voice → brand_port.get_brand_knowledge → state["brand_voice"]` consumed by `build_specialist_system_prompt`.
2. **NEW D-T3 path (canonical):** `compose_prompt(voice_port=...) → await voice_port.compile_system_instruction(tenant_id)` consumed inline.

Both paths produce identical content (PersonalityProfile.system_instruction). T-13+ may migrate orchestrator callers from legacy to new path; not in T-12 scope.

## Cardinal invariants honored

- ★ AISALESHT UNTOUCHED (V-NF-4)
- ★ Story 5 SSoT cement intact
- ★ D-T3 hexagonal cement (zero PersonalityCompiler imports)
- ★ §3 protected surfaces preserved (closer_studio.py API + WS NOT lifted — T-13 territory; closer_studio_service.py façade lifted verbatim)
- ★ Scheduling deferred imports per §9.2 (meeting_state_service inside TYPE_CHECKING)
