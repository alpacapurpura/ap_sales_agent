# crm — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Sales |
| Estado | activo |
| Última actualización | 2026-04-30 (PR-10 BE + PR-11 FE shipped — vista lite contactos operativa) |
| Doc técnico | `docs/domains/module_crm.md` |

## Qué hace por el user
CDP (Customer Data Platform) interno. Almacena contactos, eventos del journey, pipeline ventas. Le permite al user ver TODOS sus leads/clientes/customers cross-canal en un solo lugar. Identidad unificada (multi-canal, deduplicación).

## Capacidades actuales
- Tabla contactos con identidad multi-canal (email, phone, IG handle, etc)
- IdentityType enum (3-tabla pattern)
- Journey events (touch points lifecycle)
- Pipeline ventas (etapas)
- Lifecycle scoring
- Soft delete (`deleted_at`)
- Tenant aislado UUID
- Listado / filtrado / búsqueda

### Cap: Listado paginado de contactos con filtros forward-compat (BE)
- Introducida: PR-10 (PI-1, S4-crm-hub-lite, commit `c0cad8de`, 2026-04-30)
- Estado: live
- Operable copilot: pendiente PI-3 (tools `crm_search_contacts(filters)` + `crm_get_contact_summary(id)` wrappean PR-10 API)
- Endpoints: `GET /api/v1/contacts` (paginated), `GET /api/v1/contacts/{id}` (detail unified Profile+Lead), `GET /api/v1/contacts/_filter-schema` (metadata FE dynamic UI)
- 18 canonical filters PI-3 declarados forward-compat (UI lite expone subset PR-11)
- 501 stubs deferred PI-3: `/contacts/{id}/journey`, `/contacts/{id}/campaigns` (consumir cuando 200)
- Cross-module read CampaignsLookupPort (PR-8) para `has_campaign_engagement` filter (90d window)
- Tests: 33 verde nativo (31 integration sin mocks + 2 arch test ratchet)
- 0 migrations

### Cap: Vista lite contactos /sales/contactos (FE)
- Introducida: PR-11 (PI-1, S4-crm-hub-lite, commit `87b3fa3e`, 2026-04-30)
- Estado: live (UI consume PR-10 API)
- Operable copilot: pendiente PI-3 (cards copilot capa arriba)
- Page: `/[tenantId]/sales/contactos` (Server Component thin + ContactsPageClient)
- DataTable shared cross-feature en `components/shared/data-table/` (TanStack headless — 1000 clientes virtualization PI-3 ready)
- features/crm-hub/ FSD-Lite bounded context: 7 components + 3 React Query hooks + Zod types mirror Pydantic 18 filters
- ContactDetailContent host-agnostic (drawer S4 + página completa PI-3 reuse)
- SelectedContactsBar slot pattern `actions: ActionDef[]` (PR-12 inyecta "Crear segmento", PI-3 más)
- URL state filters debounced 300ms (deep-link, browser-back, shareable)
- Drawer detail (Shadcn Sheet) responsive 4 breakpoints xl/lg/md/sm
- 4 arch tests forward-compat + 1 E2E sanity + 101 Vitest verde
- ADD dep `@tanstack/react-table@^8.21.3`

## Capacidades operables desde copilot
- Buscar contacto (parcial)
- Ver pipeline conversacionalmente (parcial)
- **Gap:** crear/modificar contacto vía copilot
- **Gap:** segmentación dinámica conversacional

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Contactos + identidad | sólido | CDP pattern 3-tabla |
| Journey events | activo | |
| Pipeline | activo | |
| UI dashboard | sólido | |
| Segmentación avanzada | placeholder | |

## Conexiones cross-módulo
- **Lee de:** offer
- **Lo lee:** sales_agent, copilot, scheduling, analytics, offer

## Dolor user / oportunidades detectadas
_Pendiente. Probablemente input para PI-1 campaigns (segmentos)._

## PIs históricos
_Sin tracked aún._

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| _inicial_ | CDP pattern 3-tabla (contacts + identities + events) | Soporte multi-canal sin duplicar |
