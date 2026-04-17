# Offer Studio Catalogs — SSoT Rule

**Non-negotiable:** the offer-studio classification data has exactly one
source of truth per axis. The backend owns it; the frontend consumes via
typed React Query hooks. Drift reopens the lead-magnet mis-classification
bug fixed in commit `4083a60f` and breaks the format suitability filter
introduced in Phase 2.

## The four axes

| Axis | Backend SSoT | API endpoint | Frontend hook |
|---|---|---|---|
| **OfferArchetype** | `backend/src/modules/offer/domain/archetype_catalog.py` | `GET /api/v1/offer/archetypes/catalog` | `useArchetypeCatalog` / `useArchetypeCapabilities` / `useArchetypeDisplay` |
| **OfferValueLevel** | `backend/src/modules/offer/domain/value_level_catalog.py` | `GET /api/v1/offer/value-levels/catalog` | `useValueLevelCatalog` / `useValueLevelMetadata` |
| **OfferFormat** | `backend/src/modules/offer/domain/format_catalog.py` | `GET /api/v1/offer/formats/catalog?archetype=&business_types=` | `useFormatCatalog` / `useFormatMetadata` |
| **ExpertBusinessType** | `backend/src/shared/domain/expert_business_type.py` | `GET /api/v1/brand/expert-business-types/catalog` | `useExpertBusinessTypesCatalog` |

`OfferFormat.suitable_for: dict[ExpertBusinessType, float]` (0.0..1.0) is
what drives the wizard's per-tenant filtering. Scores > 0 include the
format; 0.0/absent hides it. Every archetype ships a `*_custom` format
with all business types at 1.0 so the escape hatch is always visible.

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

- ❌ Hardcoding archetype, value-level, format, or business-type labels,
  icons, descriptions or suitability maps in any frontend component.
  Consume the hook instead.
- ❌ Adding a new `*_METADATA` map (e.g. `ARCHETYPE_METADATA`,
  `LEVEL_RICH_INFO`, `VALUE_LEVEL_LABELS`, `FORMAT_PRESETS`). The arch
  test `test-no-catalog-duplicates.test.ts` fails CI immediately.
- ❌ Bypassing the wizard's explicit value-level step. `is_lead_magnet`
  is derived from `value_level === LEAD_MAGNET`; never expose a lateral
  checkbox that could fall out of sync.
- ❌ Skipping the backend arch test after a catalog edit. Enum changes
  without catalog updates (or vice versa) fail fast — don't `# noqa` it.

## Full design document

`docs/domains/offer/catalogs-consolidation.md` — phase-by-phase history,
commits, and per-decision rationale (D1–D11).
