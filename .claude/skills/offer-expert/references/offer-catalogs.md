# Offer Studio Catalogs — SSoT Rule

**Non-negotiable:** offer-studio classification = one source truth per axis. BE owns, FE consumes via typed React Query hooks. Drift reopens lead-magnet bug (`4083a60f`), breaks format suitability filter (Phase 2), silently breaks variant validation (Sprint 7).

## Section catalog — 21 sections (post pre-venta)

Post consolidación (commit `0f7d276e`): **21 sections** (bajó de 23). Eliminadas: `METHODOLOGY`, `CREDENTIALS` — duplicaban brand-studio (`methodology.schema.ts`, `team.schema.ts`). Credenciales persona = atributos del team de marca. Certificación oferta = campo en `program_details`.

3 sections referencian módulos externos:

| Section | Referencia | Campo | Consumer |
|---|---|---|---|
| LOCATION | `scheduling/event-types` | `scheduling_event_type_id` | `scheduling-event-type-picker` |
| PRICING | `connections/status` + `PaymentProvider` | `accepted_payment_providers` | `payment-provider-picker` |
| INSTRUCTORS | `brand-studio/team` | `instructors[]` | `offer-instructors-picker` |

Pickers en `actions/placeholders.tsx` hasta Sprint port.

## 8 catalogs (DAG)

4 pure base, 1 intermediate, 3 composite.

### Base axes (pure)

| Axis | BE SSoT | API | FE hook |
|---|---|---|---|
| **ExpertBusinessType** | `backend/src/shared/domain/expert_business_type.py` | `GET /api/v1/catalogs/business-types` | `useBusinessTypesCatalog` (features/tenant-profile) |
| **OfferValueLevel** | `backend/src/modules/offer/domain/value_level_catalog.py` | `GET /api/v1/offer/value-levels/catalog` | `useValueLevelCatalog` / `useValueLevelMetadata` |
| **SectionCatalog** | `backend/src/modules/offer/domain/section_catalog.py` | `GET /api/v1/offer/archetypes/catalog` (extended) | `useSectionCatalog` / `useSectionMetadata` |
| **VariantStructure** | `backend/src/modules/offer/domain/variant_structure_catalog.py` | `GET /api/v1/offer/variant-structures/catalog` | `useVariantStructureCatalog` / `useVariantStructureMetadata` |

> `business_types` NO vive en `BrandIdentity` desde 2026-04-20. Vive en `tenant_profile` BC. Leer via port `src.shared.links.ports.tenant_profile` o hook `useTenantProfile`. Docs: `docs/domains/tenant-profile/`.

### Intermediate

| Axis | BE SSoT | Depende | API | FE hook |
|---|---|---|---|---|
| **OfferArchetype** | `backend/src/modules/offer/domain/archetype_catalog.py` | `SectionKey`; `VariantStructure` (Sprint 8+) | `GET /api/v1/offer/archetypes/catalog` | `useArchetypeCatalog` / `useArchetypeCapabilities` / `useArchetypeDisplay` |

### Composite

| Catalog | BE SSoT | Depende | API | FE hook |
|---|---|---|---|---|
| **OfferFormat** | `backend/src/modules/offer/domain/format_catalog.py` | `OfferArchetype`; `ExpertBusinessType` (`suitable_for: dict[EBT, float]`) | `GET /api/v1/offer/formats/catalog?archetype=&business_types=` | `useFormatCatalog` / `useFormatMetadata` |
| **OfferLadderHints** | `backend/src/modules/offer/domain/offer_ladder_hints.py` | `EBT` + `OfferValueLevel` (tuple key) | `GET /api/v1/offer/ladder-hints/catalog` | `useOfferLadderHints` / `useLadderHint` / `useLadderHintsForType` |
| **OfferTypePreset** | `backend/src/modules/offer/domain/offer_type_preset_catalog.py` | `EBT` + `OfferArchetype` + `SectionCatalog` | `GET /api/v1/offer/type-presets/catalog?business_types=` | `useOfferTypePresetCatalog` / `useOfferTypePreset` / `usePresetsByArchetype` |

### DAG

```
ExpertBusinessType  OfferValueLevel  SectionCatalog  VariantStructure   ← base
        │                  │                │                 │
        │                  │                └────────┬────────┘
        │                  │                         ▼
        │                  │                   OfferArchetype            ← intermediate
        │                  │                         │
        │                  │        ┌────────────────┤
        │                  ▼        ▼                ▼
        ├───── OfferLadderHints ────┤         OfferFormat               ← composites
        │                           │
        └───── OfferTypePreset ─────┘
```

FK typed Python (enums/frozen records), never duplicated. `OfferFormat.suitable_for` 0.0..1.0 drives wizard filter (>0 incluye, 0.0/absent oculta). Cada archetype tiene `*_custom` escape (all biz @1.0).

`OfferFormat.delivery_model` duplica `OfferArchetype.default_delivery` semánticamente — format = refinement, archetype = default. Required: `programa_evergreen` es `DIY` bajo archetype con default `DWY`.

`VariantStructure` = bottom DAG, zero FK outbound. Arch test `test_variant_structure_catalog_purity.py` bloquea outbound refs.

## Workflow agregar record

1. Edit backend catalog.
2. Bump `_CATALOG_VERSION` en API module → evict caches.
3. Arch tests:
   ```bash
   cd backend && .venv/bin/pytest tests/architecture/ -x -q
   ```
4. FE anti-drift:
   ```bash
   cd frontend && npx vitest run src/__tests__/architecture/test-no-catalog-duplicates.test.ts
   ```
5. Nuevo icon → registrar en `frontend/src/features/offer-studio/lib/icon-name-resolver.ts`.

## Forbidden

- ❌ Hardcodear archetype/value-level/format/variant-structure/business-type labels/icons/descriptions/suitability en FE. Consume hook.
- ❌ Nuevo `*_METADATA` map (`ARCHETYPE_METADATA`, `LEVEL_RICH_INFO`, `VALUE_LEVEL_LABELS`, `FORMAT_PRESETS`, `VARIANT_STRUCTURE_LABELS`). Arch test falla CI.
- ❌ Bypass wizard value-level step. `is_lead_magnet` derivado de `value_level === LEAD_MAGNET`. No checkbox lateral.
- ❌ Skip arch test tras catalog edit. No `# noqa`.
- ❌ Import otro catalog desde `variant_structure_catalog.py` (pure base). Arch test AST-parse bloquea.
- ❌ Hardcodear per-biz-type examples/prices/placeholders en Offer wizard/dashboard. Consume `useLadderHint(bt, vl)`, fallback `useValueLevelMetadata(vl)` si tenant sin `business_types`. Placeholder "¿qué tipo de X?" = `typical_offer_type_es`.

## Extender

### Cuándo agregar axis
Cuando dimensión **ortogonal** — no derivable joining existentes. VariantStructure added por many-to-many puro (archetype host multiple structures, structure spans archetypes).

No agregados (aún):
- **PricingModel** (one-time/subscription/installments/PWYW) — implícito en archetype (MEMBRESIA ⇒ subscription) + `VariantStructure.TIER`. Agregar si crece más allá.
- **FulfillmentType** — enum en `offer/domain/enums.py`, consumido via `archetype.default_fulfillment`. Promover a catalog si necesita rich metadata.

### Dónde
- `shared/domain/` si ≥2 BCs consumen (forecast no cuenta — esperar 2ndo real).
- `{module}/domain/` otherwise.

`SectionCatalog` en `offer/domain/` aunque keys genéricas (`IDENTITY`, `STRATEGY`…) — consumer único = offer-studio editor. Cuando buyer-persona/brand adopten `form-runtime`, extraer mecánicas (scopes, dispatch) a `shared/`, cada studio mantiene su `*_catalog.py`. No preemptively share.

`VariantStructure` en `offer/domain/` — only offers consume. Secondary studio que necesite "variants" → own pure-base catalog.

### Artifacts per axis

1. Enum en `domain/enums.py` o `shared/domain/`.
2. `@dataclass(frozen=True, slots=True)` metadata.
3. `{AXIS}_CATALOG: dict[{Enum}, {Meta}]` keyed by enum.
4. Arch test `test_{axis}_catalog_completeness.py` — every enum has entry + no orphans + `meta.{key} is enum_value`.
5. Versioned API endpoint con `_CATALOG_VERSION`.
6. Typed React Query hook.
7. FE icon resolver update si nuevo Lucide.
8. Pure base axes: `test_{axis}_catalog_purity.py` (mirror `test_variant_structure_catalog_purity.py`).

Meta-guard ("every `*_catalog.py` has matching completeness test") deferred — agregar cuando 7mo catalog introduced sin test.

## Forbidden (preset catalog)

- ❌ Hardcodear preset metadata/labels/descripciones/examples en FE. Consume `useOfferTypePresetCatalog`.
- ❌ Mostrar `OfferArchetype` labels ("Servicio", "Programa") en wizard post preset layer. Archetype = internal tag.
- ❌ Duplicar `ConditionalQuestion` registry en FE. Llegan en catalog response.
- ❌ Preset duplicado semánticamente bajo `preset_id` diferente. Antes agregar, revisar 76 existentes per biz_type — si colapsa via conditional question, preferir.
- ❌ Bifurcar presets para "fix" archetype bleed. Si nuevo preset mapea archetype diferente que near-identical existente, documentar en `docs/domains/offer/offer-type-preset-catalog.md` bajo D26+.

## Design docs

- `docs/domains/offer/catalogs-consolidation.md` — first 5 axes, D1–D25.
- `docs/domains/offer/variant-structure-catalog.md` — 6th axis, D26–D30.
- `docs/domains/offer/offer-type-preset-catalog.md` — 7th axis, D26–D35, skill reference.
