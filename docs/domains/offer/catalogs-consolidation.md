# Offer Studio Catalogs — Consolidation Design

> Status: **Complete** (all 8 phases shipped 2026-04-17).
> Owner: Chris. Reviewer: audit-ready architecture.

## Why this document exists

Offer creation mixes **three orthogonal classification axes**. Each had its own
source of truth (or lack thereof), leading to drift, silent fallbacks, and the
lead-magnet mis-classification bug fixed in commit `4083a60f`.

This refactor consolidates all three axes into backend-authoritative catalogs,
exposed via cacheable API endpoints, consumed by typed frontend hooks, enforced
by architecture fitness tests.

## The three axes

| Axis | Meaning | Backend SSoT |
|---|---|---|
| **OfferArchetype** | Structural kind of thing being sold | `offer/domain/archetype_catalog.py` (exists) |
| **OfferValueLevel** | Role in the value ladder / funnel | `offer/domain/value_level_catalog.py` (new) |
| **OfferFormat** | Descriptive "flavor" inside an archetype | `offer/domain/format_catalog.py` (new) |

Plus a fourth axis that filters formats by business fit:

| Axis | Meaning | Backend SSoT |
|---|---|---|
| **ExpertBusinessType** | What kind of expert business the tenant runs | `shared/domain/expert_business_type.py` (new) |

## Design invariants

1. Every catalog is a frozen Python dataclass dict keyed by an enum.
   Mutation at runtime is impossible (frozen + slots).
2. Every catalog has a matching architecture test that verifies every enum
   value has a catalog entry. Drift fails CI.
3. Every catalog is exposed via a versioned, cacheable API endpoint.
   Clients cache forever, cache-bust on version bump.
4. Frontend consumes via typed React Query hooks. No hardcoded labels in
   components. Icons resolved via a `iconName → Lucide component` map.
5. `suggested_value_level` is **removed** from formats — value level is
   decided independently by the user.
6. Format suitability to business types is scored:
   `suitable_for: dict[ExpertBusinessType, float]`. 0.0 = hidden,
   0.5 = secondary (show with "menos común" badge), 1.0 = primary.
7. Formats do NOT gate or lock the editor. Editor behavior is driven by
   the polymorphic details model (product/program/service/subscription/event)
   tied to the archetype, not the format.

## Execution phases

| Phase | Scope | Commit |
|---|---|---|
| 0 | ExpertBusinessType enum + BrandIdentity.business_types field + DTO + tests (no Alembic — JSON blob) | c35b18e8 |
| 1 | ValueLevel catalog (domain + API + arch test) | 73bf7294 |
| 2 | Format catalog (domain + API + arch test, with `suitable_for` scores) | 1ada67ef |
| 3 | Frontend hooks: useArchetypeCatalog (existed), useValueLevelCatalog, useFormatCatalog, useExpertBusinessTypesCatalog | 75fc63d5 |
| 4 | Migrate 7 dashboard/editor consumers to hooks. Backend archetype catalog gains subtitle_es + examples_es | 2ab444cd |
| 5 | Wizard redesign: archetype → value level → format (scored) → name+price → editions → promise. Configs deleted | 5e6b019f |
| 6 | Editor polymorphic labels already flow through the catalog via EditionsOptIn + wizard copy | (incidental) |
| 7 | First-time full-screen onboarding dialog for business_types + settings editor | 00655f65 |
| 8 | Anti-drift arch test + docs | (this commit) |

## Key decisions (DX series, captured 2026-04-17)

- D1 — `suggested_value_level` removed from format catalog.
- D2 — `delivery_model` stays in format as informative only; not gating.
- D3 — Formats filtered by business types (score-based).
- D4 — Editor labels migrate to archetype catalog (included in Phase 6).
- D5 — `archetype-metadata.ts` deleted; all consumers migrate.
- D6 — Enum name: `ExpertBusinessType`.
- D7 — 9 types: consultor_asesor, coach_mentor, educador_infoproductor,
  agencia_dfy, host_comunidad, host_experiencia, creador_contenido,
  product_maker, saas_founder.
- D8 — Multi-select.
- D9 — `industry` free-text field on BrandIdentity stays (sub-niche).
  Complements, does not replace, business_types.
- D10 — Score-based suitability, not binary.
- D11 — First-ingreso full-screen wizard captures business_types.
  Editable anytime in Settings.

## Non-goals

- No DB schema changes to the `offers` table itself. This is a code-reorg,
  not a data migration.
- `specific_details_defaults` population per format is deferred — wave 2.
- No breaking change to offer creation endpoints — DTOs stay stable.

## Phase 10 — VariantStructure (Sprint 7, 2026-04-18)

Added the 6th axis: `VariantStructure` + `VARIANT_STRUCTURE_CATALOG`.

### Why

The edition concept was hard-coded to three temporal patterns (cohort,
single-date, recurring). Real offers fragment along non-temporal
dimensions too: subscription tiers (gold / platinum), product SKUs
(size / color), regional variants, modality, language. These cases can
live in `launch_editions` with the same lifecycle primitives but need
structure-specific validation and storage.

### What shipped (Sprint 7)

1. `src/modules/offer/domain/enums.py` — `VariantStructure` StrEnum
   (8 values: `TEMPORAL_COHORT`, `TEMPORAL_SINGLE_DATE`,
   `RECURRING_INTAKE`, `TIER`, `SKU_VARIANT`, `REGIONAL`, `MODALITY`,
   `LANGUAGE`) + `FieldOwner` StrEnum (used by Sprint 9 MIXED section
   ownership).
2. `src/modules/offer/domain/variant_structure_catalog.py` —
   `VARIANT_STRUCTURE_CATALOG` with frozen `VariantStructureMetadata`
   records + `VariantCardinality` + `CloneCopyPolicy` helper enums.
   Pure base axis: zero outbound catalog imports.
3. Migration `049_variant_structure` — adds `variant_structure TEXT
   NOT NULL`, `structure_data JSONB NOT NULL DEFAULT '{}'`,
   `sort_rank INTEGER` to `launch_editions`. Backfills
   `variant_structure` from parent offer's archetype. Three new indexes
   (composite btree, GIN on structure_data, partial btree on sort_rank).
4. `LaunchEditionModel` — 3 new columns mirror the migration.
5. `src/modules/offer/api/variant_structures.py` — public cacheable
   endpoint at `GET /api/v1/offer/variant-structures/catalog` with
   versioned response.
6. Arch tests:
   - `test_variant_structure_catalog_completeness.py` — 10 gates
     (enum alignment, Spanish copy, icon PascalCase, policy validity,
     temporal anchor invariants, forbidden-column guard rails).
   - `test_variant_structure_catalog_purity.py` — AST-parse gate
     rejecting any import from sibling catalogs or
     `expert_business_type`.
7. Domain unit tests
   (`tests/modules/offer/domain/test_variant_structure_catalog.py`) —
   26 tests covering temporal semantics, sort_rank support,
   structure-specific payload contracts, clone policy assignments,
   cardinality hints, wizard surfacing.

### Taxonomy update

Catalog system is now a **DAG of 6 axes**:

- **4 pure base axes:** `ExpertBusinessType`, `OfferValueLevel`,
  `SectionCatalog`, `VariantStructure`. No cross-catalog FKs.
- **1 intermediate axis:** `OfferArchetype` — will depend on 2 axes
  from Sprint 8 onward (adds `supported_variant_structures`).
- **1 composite axis:** `OfferFormat` — depends on `OfferArchetype` +
  `ExpertBusinessType`.

### Key decisions (D26-D30, Sprint 7)

- **D26** — `VariantStructure` is a separate axis, not a field on
  `ArchetypeCapabilities`. Orthogonality test passes: same archetype
  supports multiple structures, same structure spans archetypes.
- **D27** — Pure base, zero outbound FK, AST-enforced. Survives the
  upcoming catalog rework of Experts / Sections / Formats without churn.
- **D28** — Hybrid storage: indexable columns for common fields,
  typed JSONB (`structure_data`) for structure-specific payload.
  Validation at service layer against
  `required_structure_data_fields`.
- **D29** — `forbidden_base_fields` declared in catalog, enforced at
  service layer. Non-temporal structures forbid date columns;
  arch-test guards typos.
- **D30** — `CloneCopyPolicy` enum in metadata so clone endpoint
  (Sprint 11) dispatches on policy without hard-coded
  `if structure == X` chains.

### What's next (after Sprint 7)

- **User catalog rework checkpoint:** before Sprint 9, the user will
  rework Experts, Sections, Formats, and Archetype metadata (names,
  groupings, icon/copy polish). `VariantStructure` is designed to
  survive this without modification — the arch purity test guarantees
  no coupling leaks.
- **Sprint 8:** `ArchetypeCapabilities.supported_variant_structures`
  wired. Frontend hook lands.
- **Sprint 9:** MIXED section `FieldOwnerRule` refactor consults
  `VariantStructure`. Form-runtime dispatches per-field saves.
- **Sprint 10+:** TIER / SKU_VARIANT / REGIONAL / MODALITY / LANGUAGE
  piloted end-to-end per product priority.

See `docs/domains/offer/variant-structure-catalog.md` for the full
design.
