---
globs: "backend/src/modules/offer/domain/*_catalog.py,frontend/src/features/offer-studio/**"
description: Stub — invoca offer-expert / offer-type-preset-expert
---

# Offer Catalogs SSoT

7 catalogs DAG: ExpertBusinessType + OfferValueLevel + SectionCatalog + VariantStructure (base) → OfferArchetype (intermediate) → OfferFormat + OfferLadderHints + OfferTypePreset (composites). 21 sections post-consolidación.

Detalle (DAG, BE→FE flow, hooks por axis, workflow agregar, anti-patterns) en `offer-expert` skill → `references/offer-catalogs.md`. Para presets específicamente: `offer-type-preset-expert`.

**No-skip:**
- ❌ Hardcodear archetype/value-level/format/variant/biz-type labels-icons-suitability en FE
- ❌ Nuevo `*_METADATA` map en FE (arch test bloquea)
- ❌ Bypass wizard value-level step (`is_lead_magnet` derivado, no checkbox)
- ❌ Skip arch test tras catalog edit
- ❌ Hardcodear per-biz-type examples/prices/placeholders (consume `useLadderHint`)
