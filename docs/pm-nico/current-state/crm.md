# crm — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Sales |
| Estado | activo |
| Última actualización | 2026-04-30 (PR-10 contacts API forward-compat shipped) |
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

### Cap: Listado paginado de contactos con filtros forward-compat
- Introducida: PR-10 (PI-1, S4-crm-hub-lite, commit `c0cad8de`, 2026-04-30)
- Estado: live
- Operable copilot: pendiente PI-3 (tools `crm_search_contacts(filters)` + `crm_get_contact_summary(id)` wrappean PR-10 API)
- Endpoints: `GET /api/v1/contacts` (paginated), `GET /api/v1/contacts/{id}` (detail unified Profile+Lead), `GET /api/v1/contacts/_filter-schema` (metadata FE dynamic UI)
- 18 canonical filters PI-3 declarados forward-compat (UI lite expone subset PR-11)
- 501 stubs deferred PI-3: `/contacts/{id}/journey`, `/contacts/{id}/campaigns` (consumir cuando 200)
- Cross-module read CampaignsLookupPort (PR-8) para `has_campaign_engagement` filter (90d window)
- Tests: 33 verde nativo (31 integration sin mocks + 2 arch test ratchet)
- 0 migrations

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
