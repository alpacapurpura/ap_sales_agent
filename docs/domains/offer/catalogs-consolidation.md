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

## Phase 11 — OfferLadderHints (Latam mass-market adaptation, 2026-04-18)

Added the 7th catalog: `OfferLadderHints`, a composite keyed by
`(ExpertBusinessType, OfferValueLevel)`.

### Why

The value ladder is universal (5 rungs from Lead Magnet to Venta
Corporativa) but the **language** of each rung changes per business
type. A dentist's "primera compra" is a promotional first
consultation; a gym owner's is a day-pass; a SaaS founder's is a
starter plan. Hardcoding a single set of `examples_es` in
`VALUE_LEVEL_CATALOG` forced either: (a) marketer jargon that alienates
Latam SMB owners, or (b) a single business-archetype-biased set that
feels foreign to the other eight types.

### What shipped (Sprint 8)

1. `src/modules/offer/domain/offer_ladder_hints.py` —
   `OFFER_LADDER_HINTS: dict[tuple[ExpertBusinessType, OfferValueLevel],
   LadderHint]` with 45 frozen records (9 × 5). Each record declares
   `examples_es`, `typical_offer_type_es`, and optional per-type price
   overrides.
2. `src/modules/offer/api/offer_ladder_hints.py` — public cacheable
   endpoint at `GET /api/v1/offer/ladder-hints/catalog` with versioned
   response.
3. Arch test `test_offer_ladder_hints_completeness.py` — 7 gates
   (completeness, no orphans, self-reference, non-empty copy, LM price
   coherence, paired price declarations, ±10x sanity band).
4. Domain unit tests — helpers + monotonic pricing across rungs +
   coverage of every business type.
5. Frontend: `use-offer-ladder-hints.ts` with `useOfferLadderHints`,
   `useLadderHint(businessType, valueLevel)` and
   `useLadderHintsForType(businessType)` memoised indexers.

### Why a separate catalog (not added to `VALUE_LEVEL_CATALOG`)

Evaluated three options:

- **A. Extend `ValueLevelMetadata`** with
  `examples_by_business_type: dict[ExpertBusinessType, ...]`. Breaks
  VL's "pure base" designation and couples the ladder to EBT. Adding
  any future adaptation axis (country, industry, personality) forces a
  cartesian explosion of dicts.
- **B. Separate catalog** keyed by `(EBT, VL)` — chosen. VL stays pure
  base, Hints is a composite like Format. Next adaptation axis is
  additive (new catalog or new column in Hints) rather than modifying
  VL.
- **C. String-keyed dicts** on VL to avoid the import. Loses type
  safety, gains nothing.

### Key decisions (D31-D34, Sprint 8)

- **D31** — `OfferLadderHints` is a composite catalog (depends on two
  axes) not a new axis. No new enum; keys are tuples of existing
  enums.
- **D32** — Per-type prices are **overrides**, not replacements. `None`
  falls back to the universal `VALUE_LEVEL_CATALOG` range. Frontend
  resolves via `hint.typical_price_min_usd ?? valueLevel.typical_price_min_usd`.
- **D33** — Arch test enforces ±10x deviation band against the
  universal VL range. Wider deviation almost always signals rung
  misclassification, not a legitimate tenant-specific adjustment.
- **D34** — Response returns 45 hints flat (not filtered by query
  param). Cache simplicity + React Query deduplication > small bundle
  savings. Frontend indexes via `useMemo` on first render.

### Tradeoffs declared up-front

- Maintenance cost: 45 entries to curate vs 5 in `VALUE_LEVEL_CATALOG`.
  Offset: examples are short, the arch test catches typos, and per-
  type curation is exactly the value the catalog delivers.
- Bundle size: 45 hints × ~6 short strings = ~5KB payload. Trivial.
- Adding a new business type: requires 5 new hints (one per rung). The
  arch test fails fast until they land — no silent missing copy in
  prod.

## Phase 12 — Section catalog pre-sale consolidation (2026-04-18)

Pre-venta del código: se consolida el SectionCatalog para eliminar
duplicación con módulos backend existentes (Scheduling, Connections,
Brand Studio) y redundancia interna entre sections.

### Cambios

**Sections eliminadas (2):**

| Section | Razón | SSoT real |
|---|---|---|
| `METHODOLOGY` | Brand tiene UNA metodología core, ofertas raramente difieren | `brand-studio/schemas/methodology.schema.ts` |
| `CREDENTIALS` | Credenciales son de PERSONAS, viven en team members | `brand-studio/schemas/team.schema.ts` (por miembro) + `brand-studio/schemas/authority.schema.ts` (marca) |

Si una oferta específica necesita override de metodología → se agrega
como campo simple en ``IDENTITY`` sin duplicar el schema completo.
Si una oferta EMITE una certificación propia (ej. bootcamp entrega
Scrum cert) → va como campo en ``PROGRAM_DETAILS.certification_issued``.

**Fields redundantes eliminados:**

| Field | Problema | Fix |
|---|---|---|
| `IDENTITY.internal_sku` | Auto-generable; fricción para microempresario | Backend auto-genera al crear offer |
| `IDENTITY.headline_promise` + `PROMISE.headline_promise` | Mismo path, double-write risk | IDENTITY es SSoT |
| `IDENTITY.primary_outcome` + `PROMISE.primary_outcome` | Idem | IDENTITY es SSoT |
| `KNOWLEDGE.faq` array | Duplicado con la nueva FAQ pública | KNOWLEDGE queda con documents + reference_urls |
| `GALLERY.testimonial_images` | Duplicado con `TESTIMONIALS.author_photo_url` | Eliminado |

**Sections que ahora delegan a módulos externos:**

| Section | Módulo externo | Campo de referencia |
|---|---|---|
| `LOCATION` | `scheduling/` | `scheduling_event_type_id` + `booking_fallback_whatsapp` fallback |
| `PRICING` | `connections/` + `sales_agent.PaymentProvider` | `accepted_payment_providers` |

**Sections enriquecidas en el mismo pass:**

- `PROMISE`: before_state + after_state ahora required; +`measurable_outcomes`.
- `GALLERY`: +`video_demo_url`, +`before_after_pairs[]` (transformational offers).
- `PRICING`: +`tax_included`, +`installments_available` (decisivo Latam).

### Nuevas garantías

1. **Arch test FE↔BE alignment** — `test-section-key-backend-alignment.test.ts`
   falla CI si backend agrega/elimina un SectionKey que frontend no refleja.
2. **Tests unit para los 5 schemas nuevos** (FAQ, TESTIMONIALS, PORTFOLIO,
   LOCATION, PLATFORM_DETAILS). Los 16 originales ya tenían tests.
3. **Hooks con fetchClient respetan arch rule** — `fetchClient` only in
   `api/` directories; los hooks importan de `api/payment-providers-api.ts`
   y `api/scheduling-event-types-api.ts`.

### Gap conocido — endpoint payment-providers

El backend todavía no expone un endpoint dedicado
`/api/v1/connections/payment-providers/enabled`. El hook
`use-available-payment-providers.ts` resuelve combinando:

1. Catálogo estático de 5 providers (mirror de `PaymentProvider` StrEnum).
2. `GET /api/v1/connections/status` para flipear `is_connected` por cada uno.

Cuando se implemente el endpoint dedicado, el hook hace swap sin tocar el
schema ni los consumidores. Gap registrado.

### VariantStructure alignment (Sprint 9)

Los schemas edition-level de `PROGRAM_DETAILS`, `SERVICE_DETAILS` y
`EVENT_DETAILS` asumen variant estructuras `TEMPORAL_*`. Si un PROGRAMA
declara `variant_structure=TIER` (planes gold/platinum en lugar de
cohortes), los campos `start_date` / `end_date` / `schedule` no aplican —
Sprint 9 introducirá `FieldOwnerRule` por `(archetype, variant_structure)`
para dispatchar campos edition-level según estructura. Por ahora los
schemas asumen TEMPORAL.

### Resultado neto

- **Sections totales:** 21 (era 23).
- **Fields duplicados:** 0 (era 5).
- **Refs a módulos externos:** 3 correctas (Scheduling, Connections, Brand).
- **Archivos schemas nuevos (pre-venta):** 5 con tests unit.
- **Arch tests nuevos:** 1 (alignment FE↔BE).
- **Deuda técnica:** 0 según el audit de `.claude/rules/offer-catalogs.md`.
