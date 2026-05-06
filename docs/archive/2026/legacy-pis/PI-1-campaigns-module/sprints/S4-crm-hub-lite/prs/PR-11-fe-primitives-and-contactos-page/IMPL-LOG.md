# IMPL-LOG — PR-11-fe-primitives-and-contactos-page

> Owner: nicolify-frontend (Sonnet) builder + PM main session (Opus 4.7) cierre + fix gates.

## Sub-deliverables shipped

| # | Deliverable | Status | Notes |
|---|---|---|---|
| 1 | `frontend/src/components/shared/data-table/{DataTable,types,index}.tsx` (TanStack headless) | ✅ | NEW shared primitive |
| 2 | `frontend/src/features/crm-hub/types/index.ts` (mirror Pydantic 18 canonical filters) | ✅ | Zod schemas |
| 3 | `features/crm-hub/api/{use-contacts,use-contact-detail,use-filter-schema}-query.ts` | ✅ | React Query hooks |
| 4 | `features/crm-hub/components/{LifecycleStageChip,ScoreBadge,IdentityList}.tsx` | ✅ | Shadcn Badge variants |
| 5 | `features/crm-hub/components/{ContactDetailContent,ContactFiltersPanel,SelectedContactsBar,ContactsPageClient}.tsx` | ✅ | Slot pattern bar |
| 6 | `features/crm-hub/utils/url-state.ts` (parseFiltersFromSearchParams) | ✅ | Deep-link friendly |
| 7 | `app/(main)/[tenantId]/(dashboard)/sales/contactos/page.tsx` (Server Component thin) | ✅ | REPLACE stub |
| 8 | `__tests__/architecture/test_contact_*.test.ts` (4 forward-compat) | ✅ | DataTable shared + ContactDetailContent isolated + FilterParams subset + SelectedContactsBar slot |
| 9 | E2E `e2e/specs/regression/sales/contactos.spec.ts` (1 sanity + 1 test.skip flow) | ✅ | Heredando PR-9 pattern infra gap |
| 10 | `package.json` + `package-lock.json` ADD `@tanstack/react-table@^8.21.3` | ✅ | TanStack headless dep |
| 11 | Vitest tests 9 (DataTable + 6 component + 2 hook) | ✅ | 101 tests verde |

## EXTEND vs NEW decision (CONTRACT § 1)

NEW DataTable shared primitive en `components/shared/data-table/`. Justificación:
- Cross-feature reuse (PR-12 + PI-3 segments + campaigns)
- TanStack headless 10k rows virtualization PI-3 ready (1000 clientes)
- Arch test enforces location

NEW `features/crm-hub/` bounded FSD-Lite. Resto Shadcn primitives REUSE direct.

## Skill consultations

- frontend-expert (FSD-Lite + Server/Client Component patterns)
- tessl__shadcn-ui (Sheet + Dialog + Badge + Command + Slider patterns)
- tessl__tailwind (utility classes + tokens)
- tessl__react-patterns (loading states + memoization)
- tessl__zod (schemas + type inference)

## Bugs resueltos durante implementación

PM main session (Opus 4.7) resolvió tras builder Sonnet killed mid-fix (post E2E):

| # | Bug | Fix |
|---|---|---|
| 1 | DataTable test `Mostrando 1–2 de 2` con override `totalCount={247}` mismatch real render `Mostrando 1–50 de 247` | Fix test expectation a actual output |
| 2 | ContactDetailContent skeleton test query `[data-slot='skeleton']` — Skeleton component NO usa data-slot (solo `className="animate-pulse"`) | Cambio query a `.animate-pulse` |
| 3 | ESLint 68 errors (mostly prettier formatting + 1 import block) | `--fix` autofix resolvió todos. 84 warnings remaining (react-perf JSX inline arrays en tests — acceptable) |
| 4 | E2E spec NO creado por builder (killed antes) | PM creó spec con 1 sanity + 1 test.skip flow (heredando PR-9 pattern) |

## Quality gates locales NATIVE (cd frontend)

| Gate | Result |
|---|---|
| `npx tsc --noEmit` | ✅ exit 0 (0 errors) |
| `npx eslint <PR-11 paths>` | ✅ 0 errors, 84 warnings (react-perf JSX arrays inline tests, acceptable) |
| `npx vitest run <PR-11 paths>` | ✅ 101 passed (32 test files) |
| `npx playwright test --project=smoke contactos.spec.ts` | NOT executed (test.skip pattern, manual gate Chris post-PR-12) |

## Architecture invariants verified

- ✅ FSD-Lite boundaries (DataTable shared, NO en feature crm-hub)
- ✅ TS strict (NO `any`)
- ✅ Tailwind tokens (NO hex hardcoded)
- ✅ Spanish neutro LATAM en UI strings (Suscriptor/Lead/MQL/SQL/Oportunidad/Cliente/Evangelista/Churn + filters labels + empty states)
- ✅ Pydantic mirror exacto: `CONTACT_FILTER_FIELDS` matches BE canonical (arch test enforces)
- ✅ ContactDetailContent host-agnostic (NO Sheet/Dialog imports — arch test enforces)
- ✅ DataTable en shared (NO en features — arch test enforces)
- ✅ SelectedContactsBar slot pattern `actions: ActionDef[]` (arch test enforces)
- ✅ Server Component thin page.tsx + ContactsPageClient
- ✅ React Query hooks (REUSE existing pattern)
- ✅ fetchClient auto X-Tenant-ID

## Surface entregada (consumible por PR-12)

- `SelectedContactsBar.tsx` (PR-11) lista para EXTEND con action "Crear segmento" (PR-12 inyecta via slot)
- Types `Contact`, `ContactDetail`, `ContactFilterParams` en `features/crm-hub/types`
- React Query hooks reusables
- DataTable shared reusable cross-feature

---

<!-- @pm: PR-11 implement done. Builder Sonnet killed mid-fix; PM main session completó (4 bugs resueltos). 101 tests verde + tsc verde + eslint 0 errors. -->
