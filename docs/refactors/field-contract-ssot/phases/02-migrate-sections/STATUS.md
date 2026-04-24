---
status: done
opened_at: 2026-04-24
closed_at: 2026-04-24
baseline_green_commit: b826928b
last_green_commit: 08c96b4a
---

# Fase 02 — Status (closed)

## Resumen

Fase 02 cerrada. Allowlist `KNOWN_UNRESOLVED_PATHS` pasó de 56 → 21
(35 paths cerrados). Cap actual `expect(ALLOWLIST_CAP).toBeLessThanOrEqual(21)`.
Los 21 restantes son cross-module federated → Fase 05.

## Bloques ejecutados

| Bloque | Paths | Commit | Notas |
|---|---|---|---|
| Open (SPEC + ACCEPTANCE) | — | `20f8e257` | — |
| A · Authority | 2 | `13432b9b` | migration 063 |
| B · Value-stack anchor | 2 | `0f36174e` | migration 064 |
| C · Program narratives | 2 | `4f1322fd` | JSONB (no migration) |
| D · SubscriptionDetails | 7 | `3b4626ba` | migration 065 (JSONB rename) |
| E · ServiceDetails | 3 | `262b6593` | JSONB |
| F · ProductDetails | 5 | `119e0015` | JSONB |
| G · PlatformDetails composable | 14 | `08c96b4a` | migration 066 + ADR-010 |

**Total**: 7 commits de bloque + 1 open = 8 commits (+ el close commit I
que cerrará docs + bumps STATE). Allowlist: 56 → 54 → 52 → 50 → 43 → 40
→ 35 → 21.

## Deliverables

- 4 migraciones idempotentes (063-066).
- `field_contract.py` registry creció 6 → 42 entries (sectiones
  pricing + instructors + value_stack + program_details +
  subscription_details + service_details + product_details +
  platform_details).
- Codegen JSON + TS pasó de 126 → 160 paths.
- FE schema `platform-details.schema.ts` migrado a paths anidados
  `platform_details.X`.
- `generate_offer_field_paths.py` extendido a walk `PlatformDetails`.
- ADR-010 documentado (composable vs polymorphic decision).

## Verificación

- BE arch 425 passed (pre/post).
- FE arch 37 passed (pre/post).
- FE TSC 0 errors.
- Pytest arch + offer + copilot 1098 passed, 4 skipped.
- Ruff módulo offer clean (`# noqa` warning preexistente no bloqueante).

## Out of scope (cerrado)

- Cross-module federated paths (Fase 05).
- `OFFER_FIELDS_BY_FE_SECTION` cleanup (Fase 04).
- FE consumir section catalog (Fase 03).
- LLM extraction prompts para campos nuevos (deferred → Fase 05).
- `OfferArchetype.PLATFORM` archetype (defer indefinido por ADR-010).
