# tenant_profile — Migration Journey (2026-04-20)

**Status:** complete. Collapsed 3-phase plan into one session per user directive.

## Why

`business_types` was stored on `BrandIdentity` as part of the Brand Studio
settings blob (`tenants.config_json['brand_settings']['identity']['business_types']`).
Conceptually it is operational tenant classification, not brand identity:

- It drives the Offer Studio preset filter.
- It drives format suitability scores.
- It drives offer ladder hints.
- It drives sales-agent prompt grounding.
- It drives landing page template defaults.

Classification that affects every studio does not belong inside one of them.
Creating a dedicated `tenant_profile` bounded context re-establishes the SSoT,
removes a cross-feature FSD violation (`OfferStudioView` importing from
`features/brand-studio/components/business-types/`), and opens room for future
tenant-wide fields (sector, company_size, stage, goals) without blowing up the
brand schema.

## Scope

| Aspect | Before | After |
|---|---|---|
| Storage | JSONB nested 3 levels under tenants | `tenant_profiles` table with GIN index |
| Writable from | `PATCH /api/v1/brand/settings` | `PATCH /api/v1/tenant/profile` only |
| Readable from | `GET /api/v1/brand/settings` (mixed payload) | `GET /api/v1/tenant/profile` (dedicated DTO) |
| Catalog endpoint | `/api/v1/brand/expert-business-types/catalog` | `/api/v1/catalogs/business-types` |
| Cross-module access | direct import from `offer-studio`, `brand-studio` | port `shared/links/ports/tenant_profile.py` only |
| UI edit surface | Brand Studio onboarding dialog | Onboarding route + Settings sub-section |
| Global visibility | `OfferStudioView` header chip only | Global app shell chip bar via `components/shared/app-header/TenantContextBar.tsx` |
| Gating | none (wizard would show empty results) | Server Component redirect until `profile.is_complete` |

## Business rules (CONTRACT §8)

- **Min:** 1. **Max:** 2 (tunable via `BUSINESS_TYPES_MAX`).
- **Rate limit:** one change every 30 days after the first declaration.
  First-time declaration is never rate-limited.
- **Idempotence:** writing the same set is a no-op and does not reset the rate
  clock.
- **Effect on existing offers:** none. Ofertas existentes mantienen su preset.
  Only future offers use the new classification.

## The three collapsed phases

### Phase A — Backend BC + port + migration 052

- `backend/src/modules/tenant_profile/` full DDD stack.
- Alembic 052 creates table + GIN index + backfills from the JSONB blob.
- `shared/links/ports/tenant_profile.py` with `get_tenant_business_types` and
  `is_tenant_profile_complete`.

### Phase B — Frontend cutover

- `features/tenant-profile/` slice (api, hooks, types, components, utils).
- New routes `/onboarding/perfil-negocio` + `/settings/perfil-negocio`.
- Gating middleware at `app/(main)/[tenantId]/layout.tsx`.
- Global `TenantContextBar` in shared header.
- Offer-studio consumers rewired (`useTenantProfile` replaces
  `settings.identity.business_types`).
- Brand-studio business-types directory deleted.

### Phase C — Hard cutover + migration 053

- `BrandIdentity` field removed from the Pydantic model + legacy validator.
- Brand API PATCH returns 400 when `identity.business_types` is present.
- Legacy catalog endpoint `brand/api/expert_business_types.py` deleted.
- Alembic 053 strips `business_types` from the JSONB blob via `jsonb_set`.
- Architecture test `test_business_types_ssot.py` enforces the SSoT going
  forward (AST-based ratchet, empty allowlist).

## Post-migration invariants

- **One table owns the data.** `tenant_profiles`.
- **One port reads it cross-module.** `shared/links/ports/tenant_profile.py`.
- **One endpoint writes it.** `PATCH /api/v1/tenant/profile`.
- **One UI flow edits it.** `/settings/perfil-negocio` (plus the one-time
  `/onboarding/perfil-negocio`).
- **Catalog lives with the type itself.** `/api/v1/catalogs/business-types`.
- **Zero shims.** The brand API does not shadow the field; attempting to write
  it returns 400 with a hint.

## Out of scope (flagged as debt)

- **Frontend ESLint warnings inside new code:** 20 warnings (sonarjs/no-nested-conditional,
  react-perf/jsx-no-new-function-as-prop). Non-blocking. Can be cleaned up
  incrementally without breaking the contract.
- **Async SQLAlchemy:** the BC uses sync `Session` to be consistent with the 49
  sibling repositories. Project-wide async migration is its own sprint (rule
  `.claude/rules/backend-ddd.md` § "AsyncSession" acknowledges the transition).
- **Event bus wiring:** `BusinessTypesChanged` currently logs. Next sprint
  wires it to the in-process bus and emits a WebSocket broadcast to invalidate
  React Query caches on other connected tabs.
- **Analytics event forwarding:** `TenantProfileInitialized` is not yet sent
  to analytics providers. Planned for the analytics onboarding sprint.

## Rollback plan

If a critical bug emerges after deploy, rollback order:

1. Frontend revert — ship a commit that reverts the `features/tenant-profile/`
   slice and routes, re-introduces the brand-studio business-types directory
   from git history, and re-points consumers to `settings.identity.business_types`.
2. Backend alembic `downgrade 051_launch_editions_variant_structure_default` —
   table drop is safe because 053 cleaned the JSONB blob; the backfill in 052
   preserved the tenant data but the source of truth is now `tenant_profiles`.
   **Caveat:** any PATCH between the cutover and the rollback would be lost,
   since the brand API rejected those writes by design. Users whose
   `business_types` changed post-cutover would have to re-declare after rollback.
3. Manual data restore: if step 2 data loss is unacceptable, copy
   `tenant_profiles` rows back into `tenants.config_json.brand_settings.identity.business_types`
   via one-off SQL before running the downgrade.

## Verification checklist

- [x] 356/356 backend architecture tests pass (including new `test_business_types_ssot.py`).
- [x] 54 new unit tests for the BC (32 domain / 4 service / 10 repo / 8 API).
- [x] Alembic upgrade/downgrade/re-upgrade cycle verified against dev DB.
- [x] 11 existing tenants backfilled without data loss.
- [x] JSONB strip verified — 0 tenants retain `business_types` in the legacy path.
- [x] Frontend TypeScript: 0 errors.
- [x] Frontend tests: 32/32 new tenant-profile tests pass.
- [x] Frontend architecture tests: 15/15 pass (including updated
  `test-no-catalog-duplicates` allowlist).

## Referenced artefacts

- CONTRACT: `docs/domains/tenant-profile/CONTRACT.md`
- Backend module: `backend/src/modules/tenant_profile/`
- Port: `backend/src/shared/links/ports/tenant_profile.py`
- Migrations: `backend/alembic/versions/052_create_tenant_profiles.py`,
  `backend/alembic/versions/053_strip_business_types_from_brand_settings.py`
- Frontend slice: `frontend/src/features/tenant-profile/`
- Routes: `frontend/src/app/(main)/[tenantId]/onboarding/perfil-negocio/`,
  `frontend/src/app/(main)/[tenantId]/(dashboard)/settings/perfil-negocio/`
- Gating: `frontend/src/app/(main)/[tenantId]/layout.tsx`
- SSoT arch test: `backend/tests/architecture/test_business_types_ssot.py`
