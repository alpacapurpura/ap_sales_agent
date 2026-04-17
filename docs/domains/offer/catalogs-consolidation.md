# Offer Studio Catalogs — Consolidation Design

> Status: In progress. Started 2026-04-17.
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
| 0 | ExpertBusinessType enum + BrandIdentity.business_types field + Alembic migration + DTO + tests | pending |
| 1 | ValueLevel catalog (domain + API + arch test) | pending |
| 2 | Format catalog (domain + API + arch test, with `suitable_for` scores) | pending |
| 3 | Frontend hooks: useArchetypeCatalog, useValueLevelCatalog, useFormatCatalog | pending |
| 4 | Migrate 10 consumers to hooks. Delete archetype-metadata.ts, format-presets.ts | pending |
| 5 | Wizard redesign: archetype → value level → format (scored) → name+price → editions → promise | pending |
| 6 | Editor polymorphic labels migrate to archetype catalog (label_es, edition_noun_es) | pending |
| 7 | First-time full-screen onboarding wizard for business_types + settings editor | pending |
| 8 | Anti-drift arch tests + domain docs | pending |

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
