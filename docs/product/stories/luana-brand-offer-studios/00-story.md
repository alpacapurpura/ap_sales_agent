# Story 5 — Brand Studio + Offer Studio lift

> **Outcome:** luana-platform-migration · **Sequence:** 5/14

## What

Lift studios complejos:

| Module | Destino | Notas |
|---|---|---|
| `brand` | `luana-core-brand-studio` | Form-runtime + extraction orchestrator + PersonalityProfile (3-pillar) + BuyerPersona + StoryBrand + Authority Vault + **voice compiler v2 ELEVATED here** (per ADR-001 §2.4) |
| `offer` | `luana-core-offer-studio` | 7 catalogs DAG + 76 presets + form-runtime + conditional questions + multi-currency wizard |

## Voice compiler elevation (ADR-001 §2.4)

`personality_profiles.system_instruction` compiler vive en `core-brand-studio`. `core-sales-agent` (Story 7) lo consume via `BrandVoicePort.compileSystemInstruction(tenant_id) → str`. Refactor menor pero clean DDD.

## Voice cloning feature flag

`BrandConfig.features.voiceCloning: bool` activa pipeline LLM-distillation desde 50+ chats reales:
- Nicolify: ON
- Comunify: ON
- Vitalia: OFF
- Lupulo: OFF
- (per ADR-001 §2.4)

## Acceptance

- 2 packages publicados v0.0.5-alpha
- Voice compiler v2 funcional en core-brand-studio
- BrandVoicePort definido en core-brand-studio
- Catalog versioning (`_CATALOG_VERSION`) bumpeable post-split
- Form-runtime engine FE refactorizado en `@luana/brand-studio-ui` + `@luana/offer-studio-ui` (separate per OQ4)

## Effort: 14-20 tickets, ~5 días
