# Story 14 — Brand voice compiler elevation

> **Outcome:** luana-platform-migration · **Sequence:** 14/14 · **Parallel-safe**

## Why

Per ADR-001 §2.4, decision Q2: voz **es** identidad de marca. `core-brand-studio` debe poseer el voice compiler v2 + PersonalityProfile + voice cloning pipeline. `core-sales-agent` consume via `BrandVoicePort` (port pattern DDD limpio).

Story 5 ya hace el lift inicial. Story 14 es **cleanup post-merge** — refactor que asegura SSoT real, ports cleanly defined, y voice cloning feature flag flexible per brand.

## What

1. Audit final: confirmar `personality_profiles.system_instruction` compiler vive 100% en `core-brand-studio`
2. `BrandVoicePort` interface formal en `core-brand-studio/links/ports/brand_voice.py`
3. `core-sales-agent` consume via port — verify ZERO direct imports a `core-brand-studio` internal
4. Voice cloning feature flag end-to-end:
   - `BrandConfig.features.voiceCloning: bool` declarativo
   - UI en `@luana/brand-studio-ui` muestra/oculta upload "Sube 50+ chats reales"
   - Pipeline LLM-distillation gated by flag
5. Tests:
   - Comunify: voice cloning ON → distillation pipeline runs
   - Vitalia: voice cloning OFF → distillation pipeline blocked
   - Both consume voice via port equally
6. Documentation update: `core-brand-studio/docs/voice-architecture.md`

## Acceptance

- BrandVoicePort defined + tested
- Sales agent only imports from `core-brand-studio.links.ports`
- Voice cloning feature flag toggleable per brand
- 4 brands behave per ADR-001 §2.4 spec
- Arch fitness test: ban direct imports `core-sales-agent → core-brand-studio.internal`

## Effort: 8-12 tickets, ~3 días Opus
