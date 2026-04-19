# Offer Studio Catalogs — SSoT Rule

**Non-negotiable:** the offer-studio classification data has exactly one
source of truth per axis. The backend owns it; the frontend consumes via
typed React Query hooks. Drift reopens the lead-magnet mis-classification
bug fixed in commit `4083a60f`, breaks the format suitability filter
introduced in Phase 2, and (as of Sprint 7) silently breaks variant-aware
validation for non-temporal offers.

## Section catalog — 21 sections (post-consolidación pre-venta)

Después de la consolidación pre-venta (commit `0f7d276e`), el offer-studio
declara **21 sections** (bajó de 23). Las 2 eliminadas fueron
``METHODOLOGY`` y ``CREDENTIALS`` — duplicaban metadata que ya vive en
brand-studio (``methodology.schema.ts`` y ``team.schema.ts`` respectivamente).
Credenciales de persona se mantienen como atributos de cada miembro del
equipo de la marca; si una oferta emite una certificación propia, se modela
como campo dentro de ``program_details``.

Tres sections refieren explícitamente a módulos externos (no duplican):

| Section | Referencia externa | Campo | Consumer |
|---|---|---|---|
| LOCATION | `scheduling/event-types` | `scheduling_event_type_id` | `scheduling-event-type-picker` custom action |
| PRICING | `connections/status` + `PaymentProvider` enum | `accepted_payment_providers` | `payment-provider-picker` custom action |
| INSTRUCTORS | `brand-studio/team` | `instructors[]` (IDs) | `offer-instructors-picker` |

Estos picker actions viven en `actions/placeholders.tsx` hasta que el
Sprint que los porte los reemplace con la implementación real.

## The eight catalogs

The offer-studio classification system is a **DAG of 8 catalogs**: 4 pure
base axes (no cross-catalog references), 1 intermediate axis that
references base axes via typed FK, and 3 composite catalogs that each
depend on two or three axes.

### Base axes (pure)

| Axis | Backend SSoT | API endpoint | Frontend hook |
|---|---|---|---|
| **ExpertBusinessType** | `backend/src/shared/domain/expert_business_type.py` | `GET /api/v1/brand/expert-business-types/catalog` | `useExpertBusinessTypesCatalog` |
| **OfferValueLevel** | `backend/src/modules/offer/domain/value_level_catalog.py` | `GET /api/v1/offer/value-levels/catalog` | `useValueLevelCatalog` / `useValueLevelMetadata` |
| **SectionCatalog** | `backend/src/modules/offer/domain/section_catalog.py` | `GET /api/v1/offer/archetypes/catalog` (extended) | `useSectionCatalog` / `useSectionMetadata` |
| **VariantStructure** | `backend/src/modules/offer/domain/variant_structure_catalog.py` | `GET /api/v1/offer/variant-structures/catalog` | `useVariantStructureCatalog` / `useVariantStructureMetadata` (Sprint 8) |

### Intermediate axis

| Axis | Backend SSoT | Depends on | API endpoint | Frontend hook |
|---|---|---|---|---|
| **OfferArchetype** | `backend/src/modules/offer/domain/archetype_catalog.py` | `SectionKey` (via `sections: tuple[SectionKey, ...]`); `VariantStructure` from Sprint 8 onward (via `supported_variant_structures`) | `GET /api/v1/offer/archetypes/catalog` | `useArchetypeCatalog` / `useArchetypeCapabilities` / `useArchetypeDisplay` |

### Composite catalogs

| Catalog | Backend SSoT | Depends on | API endpoint | Frontend hook |
|---|---|---|---|---|
| **OfferFormat** | `backend/src/modules/offer/domain/format_catalog.py` | `OfferArchetype` (via `archetype`); `ExpertBusinessType` (via `suitable_for: dict[ExpertBusinessType, float]`) | `GET /api/v1/offer/formats/catalog?archetype=&business_types=` | `useFormatCatalog` / `useFormatMetadata` |
| **OfferLadderHints** | `backend/src/modules/offer/domain/offer_ladder_hints.py` | `ExpertBusinessType` + `OfferValueLevel` (keyed by `tuple[ExpertBusinessType, OfferValueLevel]`) | `GET /api/v1/offer/ladder-hints/catalog` | `useOfferLadderHints` / `useLadderHint` / `useLadderHintsForType` |
| **OfferTypePreset** | `backend/src/modules/offer/domain/offer_type_preset_catalog.py` | `ExpertBusinessType` + `OfferArchetype` + `SectionCatalog` (via `base_sections`) | `GET /api/v1/offer/type-presets/catalog?business_types=` | `useOfferTypePresetCatalog` / `useOfferTypePreset` / `usePresetsByArchetype` |

### Dependency DAG

```
ExpertBusinessType  OfferValueLevel  SectionCatalog  VariantStructure   ← 4 pure base
        │                  │                │                 │
        │                  │                └────────┬────────┘
        │                  │                         ▼
        │                  │                   OfferArchetype            ← 1 intermediate
        │                  │                         │
        │                  │        ┌────────────────┤
        │                  │        │                │
        │                  ▼        ▼                ▼
        ├───── OfferLadderHints ────┤         OfferFormat               ← composites
        │                           │
        └───── OfferTypePreset ─────┘                                   ← 7th composite
               (EBT × Arch × Sec)
```

All FK are typed Python fields (enums or frozen metadata records) — never
duplicated data. `OfferFormat.suitable_for` scores (0.0..1.0) drive the
wizard's per-tenant filtering: > 0 includes, 0.0/absent hides. Every
archetype ships a `*_custom` escape-hatch format (all business types at
1.0) so the wizard always has an option.

`OfferFormat.delivery_model` intentionally duplicates
`OfferArchetype.default_delivery` semantically — format is the
**refinement**, archetype the default propagated at offer creation.
Required because `programa_evergreen` is `DIY` under an archetype whose
default is `DWY`.

`VariantStructure` is the bottom of the DAG: it has **zero outbound FK**.
The coupling flows into it (`ArchetypeCapabilities.supported_variant_structures`
from Sprint 8; `SectionMetadata` MIXED ownership rules from Sprint 9),
never out. This keeps the catalog stable across the downstream rework of
Experts / Sections / Formats.

## Mandatory workflow when adding a new record

1. **Edit the backend catalog** (the only place the record lives).
2. **Bump the catalog's `_CATALOG_VERSION`** in the matching API module
   so clients evict cached copies.
3. **Run the architecture tests** for the affected catalog — they verify
   enum ↔ catalog alignment and per-catalog invariants:

   ```bash
   cd backend && .venv/bin/pytest tests/architecture/ -x -q
   ```
4. **Run the frontend anti-drift test**:

   ```bash
   cd frontend && npx vitest run src/__tests__/architecture/test-no-catalog-duplicates.test.ts
   ```
5. **Add new icons to the Lucide map** in
   `frontend/src/features/offer-studio/lib/icon-name-resolver.ts` if the
   entry's `icon_name` is not yet registered.

## Forbidden patterns

- ❌ Hardcoding archetype, value-level, format, variant-structure, or
  business-type labels, icons, descriptions or suitability maps in any
  frontend component. Consume the hook instead.
- ❌ Adding a new `*_METADATA` map (e.g. `ARCHETYPE_METADATA`,
  `LEVEL_RICH_INFO`, `VALUE_LEVEL_LABELS`, `FORMAT_PRESETS`,
  `VARIANT_STRUCTURE_LABELS`). The arch test
  `test-no-catalog-duplicates.test.ts` fails CI immediately.
- ❌ Bypassing the wizard's explicit value-level step. `is_lead_magnet`
  is derived from `value_level === LEAD_MAGNET`; never expose a lateral
  checkbox that could fall out of sync.
- ❌ Skipping the backend arch test after a catalog edit. Enum changes
  without catalog updates (or vice versa) fail fast — don't `# noqa` it.
- ❌ Importing another catalog from `variant_structure_catalog.py`. It is
  a pure base axis; the arch test
  `test_variant_structure_catalog_purity.py` AST-parses the module and
  blocks any outbound reference.
- ❌ Hardcoding per-business-type examples, prices or offer-type
  placeholders in the Offer Studio wizard/dashboard. Consume
  `useLadderHint(businessType, valueLevel)` and fall back to the
  universal `useValueLevelMetadata(valueLevel)` when the tenant has not
  declared `business_types`. The wizard's "¿qué tipo de X vas a crear?"
  placeholder is driven by `typical_offer_type_es`.

## Extending the system

### When to add a new axis

Add a new catalog when a classification dimension is **orthogonal** to
the existing six — i.e. cannot be derived by joining existing axes.
Test: can you express a valid combination that doesn't fit today's axes?
If yes, new axis justified. VariantStructure was added because the same
archetype can host multiple structures and the same structure spans
archetypes — a pure many-to-many that no existing axis expressed.

Candidates evaluated and not (yet) added:

- **PricingModel** (one-time / subscription / installments /
  pay-what-you-want) — today implicit in archetype (MEMBRESIA ⇒
  subscription) and in `VariantStructure.TIER` for tiered plans. Add
  when pricing grows beyond single-price + subscription + tier.
- **FulfillmentType** — exists as enum in `offer/domain/enums.py`,
  consumed via `archetype.default_fulfillment`. Promote to catalog when
  it needs rich metadata (integrations, provisioning hints).

### Where to place a new axis

- `shared/domain/` iff ≥2 bounded contexts consume it (forecast doesn't
  count — wait for the real 2nd consumer).
- `{module}/domain/` otherwise.

`SectionCatalog` sits in `offer/domain/` today despite generic keys
(`IDENTITY`, `STRATEGY`, `PROMISE`…) because its concrete consumer is
only the offer-studio editor. When buyer-persona-studio or brand-studio
adopt `form-runtime`, extract the runtime **mechanics** (section scopes,
owner dispatch) to `shared/`, but each studio keeps its own
`*_catalog.py` with its own keys. Don't preemptively share the catalog.

`VariantStructure` sits in `offer/domain/` because offers are the only
consumers. Any secondary studio that eventually needs a "variants of a
thing" concept (hypothetical: playbook variants in brand-studio?) gets
its own pure-base catalog, not a share.

### Required artifacts per new axis

1. Enum in the relevant `domain/enums.py` (or `shared/domain/`).
2. Frozen `@dataclass(frozen=True, slots=True)` metadata record.
3. `{AXIS}_CATALOG: dict[{Enum}, {Metadata}]` keyed by enum.
4. Architecture test `test_{axis}_catalog_completeness.py` asserting
   every enum value has an entry + no orphans + `meta.{key} is enum_value`.
5. Versioned API endpoint emitting the catalog as JSON with
   `_CATALOG_VERSION`.
6. Typed React Query hook consuming the endpoint.
7. Frontend icon-name resolver update if new Lucide icon used.
8. **For pure base axes:** `test_{axis}_catalog_purity.py` asserting
   zero outbound catalog imports (mirrors
   `test_variant_structure_catalog_purity.py`).

Meta-guard arch test ("every `*_catalog.py` has a matching
`test_{name}_catalog_completeness.py`") is intentionally deferred:
6 catalogs with the pattern uniformly applied don't justify the
indirection. Add it when a 7th catalog is introduced without test.

## Forbidden patterns (preset catalog additions)

- ❌ Hardcoding preset metadata, labels, descriptions or examples in any
  frontend component or wizard step. Consume `useOfferTypePresetCatalog`.
- ❌ Showing `OfferArchetype` labels ("Servicio", "Programa") in wizard
  UX after the preset layer lands. The archetype is an internal tag —
  tenants choose presets by name, not archetype.
- ❌ Duplicating the `ConditionalQuestion` registry in the frontend.
  Questions arrive as part of the catalog response; never redeclare them
  client-side.
- ❌ Adding a preset that already exists semantically under a different
  `preset_id`. Before adding, review the existing 76 entries per
  `business_type` — if the new idea collapses into an existing preset
  via a conditional question, prefer that over a new preset.
- ❌ Bifurcating presets to "fix" archetype bleed. If the new preset
  would map to a different archetype than an existing near-identical
  preset, document the bifurcation decision in
  `docs/domains/offer/offer-type-preset-catalog.md` under D26+ so future
  Claude understands the intent.

## Full design documents

- `docs/domains/offer/catalogs-consolidation.md` — phase-by-phase history
  of the first 5 axes, commits, decisions D1–D25.
- `docs/domains/offer/variant-structure-catalog.md` — full design of the
  6th axis (VariantStructure), decisions D26–D30, extension rules.
- `docs/domains/offer/offer-type-preset-catalog.md` — full design of the
  7th axis (OfferTypePreset), decisions D26–D35, composition rules,
  skill reference.
