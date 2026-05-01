# PR-11-fe-primitives-and-contactos-page

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-11-fe-primitives-and-contactos-page |
| Sprint padre | S4-crm-hub-lite |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | feature |
| Esfuerzo | L |
| Owner PM | /pm |
| Surface | frontend — `frontend/src/components/shared/` + `frontend/src/features/crm-hub/` + `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/contactos/` |
| Builder | `nicolify-frontend` (Sonnet) |
| Auditor | `nicolify-frontend-auditor` (Opus) |

## Problema (user-facing)

User abre `/sales/contactos` → ve "Próximamente" stub. PR-10 entrega API; PR-11 entrega UI consumiendo ese contract. JTBD: "Quiero ver mis contactos en una tabla potente con filtros, búsqueda y selección múltiple para decidir a quién contactar."

## Outcome esperado

Página `/sales/contactos` operativa con:
- Tabla paginada con DataTable shared (reusable cross-feature: contactos hoy, campañas/segmentos PI-3)
- Panel filters lateral (subset de los 18 filters PI-3 declarados — UI lite expone esenciales)
- Drawer detail al click row (Sheet Shadcn)
- Selección múltiple → SelectedContactsBar bottom (slot pattern PI-3 expansion)
- Search bar con debounce 300ms

**Forward-compat**: ContactDetailContent component aislado → drawer hoy + página completa PI-3 reusan. DataTable en `components/shared/` (no en feature). FilterParams TS schema mirror exacto Pydantic.

## Walking skeleton

| # | Capa | Entregable |
|---|---|---|
| 1 | shared primitive | `components/shared/data-table/` — DataTable wrapper Shadcn Table genérico |
| 2 | feature scaffolding | `features/crm-hub/{api,components,hooks,types,utils}/` |
| 3 | API client | `features/crm-hub/api/use-contacts-query.ts` + `use-contact-detail-query.ts` (React Query) |
| 4 | Types | `features/crm-hub/types/index.ts` — mirror Pydantic DTOs (Contact, ContactDetail, ContactFilterParams, FilterSchemaResponse) |
| 5 | Components | ContactFiltersPanel + ContactDetailContent + IdentityList + ScoreBadge + LifecycleStageChip + SelectedContactsBar |
| 6 | Page | `/sales/contactos/page.tsx` (Server Component thin) + `ContactsPageClient.tsx` (Client) |
| 7 | E2E | `frontend/e2e/specs/regression/sales/contactos.spec.ts` smoke |
| 8 | Arch tests | 4 tests forward-compat |

## Soluciones consideradas

| Eje | Opción | Veredicto |
|---|---|---|
| **DataTable abstraction** | A — TanStack Table headless wrapper (handles 10k rows virtualization PI-3) | **ELEGIDA** (1000 clientes lens — no refactor PI-3) |
| | B — Custom Shadcn-only | descartada (refactor garantizado PI-3) |
| **Detail UI** | A — Drawer (Sheet) S4 + page route PI-3, shared `ContactDetailContent` | **ELEGIDA** (forward-compat) |
| | B — Drawer only, page reescribe PI-3 | descartada (re-write deuda) |
| **Filters state** | A — URL state (Next searchParams) → React Query queryKey | **ELEGIDA** (deep-link, browser-back, shareable, 1000 clientes friendly) |
| | B — Zustand local | descartada (no shareable, no deep-link) |
| **SelectedContactsBar API** | A — Slot prop `actions: ActionDef[]` | **ELEGIDA** (PI-3 agrega más actions sin tocar bar) |
| | B — Children render-prop | descartada (peor DX cross-feature) |
| **Search debounce** | A — 300ms | **ELEGIDA** (UX 1000 clientes balanced) |

## Validación técnica preliminar

- Modules afectados: `frontend/src/components/shared/data-table/` (NEW), `frontend/src/features/crm-hub/` (NEW), `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/contactos/page.tsx` (REPLACE stub)
- Dependencias FSD-Lite: `feature:crm-hub` consume `shared/data-table` + `ui/*` (Shadcn) + `lib/http-client`
- TanStack Table dep: verificar si ya existe en package.json — sino agregar `@tanstack/react-table`
- API consumida: PR-10 endpoints (asumir merged antes de iniciar PR-11 builder)
- Schema vivo:
  - `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` (pattern reference Shadcn Badge link)
  - `frontend/src/components/ui/{table,sheet,checkbox,badge,input,popover,command,sonner,dialog}.tsx` (existing primitives)
  - `frontend/src/lib/http-client.ts::fetchClient` (auto-injects X-Tenant-ID)
- Migrations: 0
- Estimated: 1 architect (UI-SPEC) + 1 builder + auto-audit

## Existing systems audit (architect-mandatory)

Subsystems: `data table primitive`, `react query hooks`, `filters URL state`.

Architect ejecuta:
- `find frontend/src/components/shared -type d` (ya existe `app-header`, `layout`, `navigation` — DataTable NEW)
- `grep -rn "TanStack\|@tanstack/react-table" frontend/` (verificar dep existence)
- `grep -rn "DataTable\|data-table" frontend/src/` (verificar duplicates)
- `grep -rn "useQuery\|@tanstack/react-query" frontend/src/features/` (existing query hooks pattern)
- `find frontend/src/features/closer-studio -type f -name "*.tsx"` (FE pattern reference)

EXTEND vs NEW decisions:
- DataTable: **NEW** en `components/shared/data-table/` — no existe primitive cross-feature reusable
- React Query patterns: **REUSE** existing hooks pattern from features (closer-studio uses React Query)
- Sheet (drawer): **REUSE** existing Shadcn `components/ui/sheet.tsx`

## Decisiones diferidas

- **TanStack Table column resizing**: NO en PR-11 (PI-3 bulk view enhancements)
- **Filter builder visual drag-drop**: NO (PI-3 segment-builder)
- **Página completa `/sales/contactos/{id}`**: NO (PI-3; drawer cubre 80% lite)
- **Cards copilot related**: NO (PI-3)
- **CSV export**: NO

## Out of scope

- Crear/editar/eliminar contactos (PR-11 read-only, BE no expone POST/PUT/DELETE)
- Notes/tags UI
- Timeline rich (501 stub BE)
- Bulk actions (excepto "Crear segmento" = PR-12)

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? **Sí (parcial)** — copilot tools `crm_search_contacts(filters)` se agregan PI-3 wrappeando PR-10 API
- [ ] Tools nuevos PR-11: NO (PI-3 los agrega)
- [ ] Cards/UI nueva: NO (PI-3 cards en chat copilot)
- Razón scope: PR-11 = web UI primero. Copilot integration capa arriba.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Pre-flight | `nicolify-context-builder` (Haiku, opcional para FE M+) | `prompts/00-context-prep.md` | `CONTEXT-BRIEF.md` |
| UX | `ux-flow-architect` (skill) | PM ad-hoc | `UI-SPEC.md` (PM completa con UX session input) |
| Pre-design | `nicolify-architect` (Opus) | `prompts/01-architect-start.md` | `CONTRACT.md` (TS types contract — mirror Pydantic) |
| Implementation | `nicolify-frontend` (Sonnet) | `prompts/02-builder-start.md` | code + tests + `IMPL-LOG.md` |
| Audit | `nicolify-frontend-auditor` (Opus) auto-spawned | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/crm.md` update |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Shared primitive | `frontend/src/components/shared/data-table/{DataTable.tsx,types.ts,index.ts}` | NEW |
| Feature dir | `frontend/src/features/crm-hub/` | NEW (api/, components/, hooks/, types/, utils/) |
| Component | `crm-hub/components/{ContactFiltersPanel,ContactDetailContent,IdentityList,ScoreBadge,LifecycleStageChip,SelectedContactsBar,ContactsPageClient}.tsx` | NEW |
| API hooks | `crm-hub/api/{use-contacts-query,use-contact-detail-query,use-filter-schema-query}.ts` | NEW |
| Types | `crm-hub/types/index.ts` (mirror Pydantic DTOs) | NEW |
| Page | `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/contactos/page.tsx` | REPLACE stub |
| E2E | `frontend/e2e/specs/regression/sales/contactos.spec.ts` | NEW |
| Arch tests | `frontend/src/__tests__/architecture/` 4 tests | NEW |
| current-state | `docs/pm-nico/current-state/crm.md` | append capability lineage |

## Tests requeridos

### Vitest (component + hook)
- `crm-hub/components/__tests__/ContactFiltersPanel.test.tsx` — render, change filter → onChange called with new params
- `crm-hub/components/__tests__/ContactDetailContent.test.tsx` — render with detail prop → all fields visible (drawer + page reuse)
- `crm-hub/components/__tests__/SelectedContactsBar.test.tsx` — show when ≥1 selected; hide when empty; render slot actions
- `crm-hub/components/__tests__/ScoreBadge.test.tsx` — variant per range
- `crm-hub/components/__tests__/LifecycleStageChip.test.tsx` — variant per stage
- `crm-hub/components/__tests__/IdentityList.test.tsx` — render multi-channel identities
- `components/shared/data-table/__tests__/DataTable.test.tsx` — pagination + sorting + selection callbacks
- `crm-hub/api/__tests__/use-contacts-query.test.ts` — fetchClient call + URL params correct + cache key
- `crm-hub/api/__tests__/use-contact-detail-query.test.ts`

### Playwright E2E
- `frontend/e2e/specs/regression/sales/contactos.spec.ts`:
  - Smoke nav `/sales/contactos` → tabla render con seed data
  - Apply filter `lifecycle_stage=MQL` → results filter applied
  - Click row → drawer opens with detail
  - Search `q=juan` → results filtered
  - Check 2 rows → SelectedContactsBar visible con count="2 contactos"
  - Pagination next page

### Arch tests (Vitest)
- `__tests__/architecture/test_contact_detail_content_isolated.test.ts` — verify `ContactDetailContent` exports without drawer-specific deps (drawer + future page reusan)
- `__tests__/architecture/test_data_table_in_components_shared.test.ts` — DataTable vive en `components/shared/`, NO en `features/crm-hub/`
- `__tests__/architecture/test_filter_params_subset.test.ts` — TS FilterParams type tiene mismos keys que Pydantic ContactFilterParams (mirror canonical fields list)
- `__tests__/architecture/test_selected_contacts_bar_slot_pattern.test.ts` — Bar accepts `actions: SelectedContactsBarAction[]` prop (slot pattern PI-3)

## Aceptación

- [ ] CONTRACT.md ready (architect — TS types mirror Pydantic)
- [ ] UI-SPEC.md ready (component tree + interactions + responsive)
- [ ] Code + tests + IMPL-LOG (builder Sonnet)
- [ ] gate-output.json overall.any_fail = false
- [ ] REVIEW.md verdict PASS (auditor Opus)
- [ ] tsc strict 0 errors. ESLint 0 errors. Vitest verde
- [ ] FSD-Lite boundaries respected (DataTable shared, no en feature)
- [ ] Tailwind tokens (no hardcoded colors)
- [ ] Spanish neutro LATAM en UI strings
- [ ] 4 arch tests forward-compat verde
- [ ] E2E smoke verde (o documented test.skip si infra gap como PR-9)
- [ ] RESULT.md + current-state/crm.md update

## Riesgos

| Riesgo | Mitigación |
|---|---|
| TanStack Table dep nueva vs custom | Architect verifica package.json; si ya existe REUSE; sino agregar dep documentado |
| `ContactDetailContent` accidentalmente acoplado a Sheet | Arch test `test_contact_detail_content_isolated` enforces isolation |
| `DataTable` en feature en vez de shared | Arch test `test_data_table_in_components_shared` enforces |
| FilterParams TS drift vs Pydantic | Arch test `test_filter_params_subset` checks mirror |
| URL state explosion con 18 filters | Encoder `searchParams` usa pattern compact (e.g. `lifecycle_stage_in=MQL,SQL` comma-list) |
| E2E flaky por seed data | Mock API responses pattern de PR-9 (Growth Studio mocks) |
| API PR-10 not merged yet | Builder PR-11 spera PR-10 ship before iniciar (sequential dependency) — PM coordina |
