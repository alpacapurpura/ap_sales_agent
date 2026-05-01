# PR-10-crm-contacts-api-forward-compat

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-10-crm-contacts-api-forward-compat |
| Sprint padre | S4-crm-hub-lite |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | feature |
| Esfuerzo | M |
| Owner PM | /pm |
| Surface | backend (negocio) — `modules/crm/` |
| Builder | `nicolify-backend` (Sonnet) |
| Auditor | `nicolify-backend-auditor` (Opus) |

## Problema (user-facing)

User abre `/sales/contactos` → stub vacío. No puede ver leads/customers en un solo lugar para filtrar, buscar, segmentar, lanzar campaña outbound. JTBD: "Quiero ver TODA mi base de contactos con filtros poderosos para decidir a quién contactar hoy."

## Outcome esperado

API REST forward-compat completa: lista paginada + detalle rico de contactos con TODOS los filters PI-3 declarados desde día 1. UI lite (PR-11) consume subset hoy. PI-3 agrega componentes/queries sin reescribir API. **Cero refactor entre S4 y PI-3.**

## Walking skeleton (mínimo viable cohesivo)

5 endpoints REST en `modules/crm/api/contacts.py`:

| # | Endpoint | Estado | Uso lite | Uso PI-3 |
|---|---|---|---|---|
| 1 | `GET /api/v1/contacts` | live | tabla principal | tabla + segment-builder preview |
| 2 | `GET /api/v1/contacts/{id}` | live | drawer detail | página completa detail |
| 3 | `GET /api/v1/contacts/{id}/journey` | **501** documented | — | timeline rico |
| 4 | `GET /api/v1/contacts/{id}/campaigns` | **501** documented | — | historial campañas |
| 5 | `GET /api/v1/contacts/_filter-schema` | live | metadata filters | mismo |

**FilterParams Pydantic schema soporta TODOS los filters PI-3 desde día 1.** UI lite expone subset; PI-3 expande UI sin tocar BE.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — FilterParams flat (todos PI-3 declarados como query params opcionales)** | API simple, deep-linkable, server-side validable, PI-3 expand UI sin tocar BE, 1000 clientes friendly | Schema grande pero documentado vía OpenAPI | **ELEGIDA** |
| B — FilterParams nested (POST body con filters tree) | Schema agrupado | POST listar = no shareable URL, no browser cache | descartada |
| C — Subset filters lite + PI-3 endpoint nuevo `/contacts-advanced` | Simple ahora | Refactor garantizado PI-3 + duplicate path = drift | descartada |
| D — GraphQL | Flexibilidad | No existe stack GQL en Nicolify, costoso adopción | descartada |

## Validación técnica preliminar (Technical Sanity Check)

- Modules afectados: `modules/crm/` (api + application + dto)
- Cross-module reads: `CampaignsLookupPort` (PR-8) para `has_campaign_engagement` filter — usar puerto, NO import directo
- Schema vivo: `LeadModel` + `CustomerProfileModel` (`shared/infrastructure/models/crm.py`)
- Blockers conocidos: ninguno (Lead/Customer schemas estables)
- Tiempo estimado: 1 ejecución architect + 1 ejecución builder con auto-audit
- Migrations: **0** (queries sobre schema existente)

## Existing systems audit (architect-mandatory)

Subsistemas tocados: `crm contacts query`, `pagination`, `cross-module campaigns lookup`, `cross-module crm port`.

Architect ejecuta:
- `grep -rn "GET /contacts\|get_contacts\|list_contacts\|@router.get" backend/src/modules/crm/`
- `grep -rn "PaginatedResponse\|PaginationParams" backend/src/modules/`
- `grep -rn "from src.shared.links.ports.campaigns\|from src.shared.links.ports.crm_repos" backend/src/`
- `find backend/src/modules/crm -name "*.py"`

Esperado encontrar:
- `modules/crm/api/leads.py` (lista de leads — verificar EXTEND vs NEW endpoint paralelo)
- `modules/crm/api/cdp.py` (CDP contacts — verificar overlap)
- `modules/crm/copilot_provider/` (existe — read access, no toca)
- `PaginatedResponse` pattern de PR-3/PR-4 campaigns (REUSE)
- `CampaignsLookupPort` PR-8 — extender si requiere `has_campaign_engagement` batch lookup

**Decisión EXTEND vs NEW** la toma architect en CONTRACT.md § Existing Systems Audit citando paths reales.

## Decisiones diferidas (explícitas)

- **Cursor pagination**: ship offset MVP. Cursor-based si telemetría muestra offset>1000 leads tenant. Follow-up PR post-S4.
- **`/journey` + `/campaigns` 501 stubs**: con `Retry-After: PI-3` header + OpenAPI description "Deferred PI-3". Declara contract canonical.
- **RFM/lookalike filters**: NO incluidos (PI-3 expansion).
- **Notes y tags filters**: NO incluidos (out of scope S4 + mid-priority PI-3).

## Out of scope

- POST/PUT/DELETE contacts (read-only API)
- Notes, tags, manual stage override (PI-3)
- Timeline events (501 stub)
- Bulk export CSV
- Computed RFM segment lookup
- Cualquier UI (eso es PR-11)

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? **Sí (parcial)** — copilot ya tiene `crm/copilot_provider/`. PR-10 NO bloquea integration: PI-3 wrappea API en tools.
- [ ] Tools nuevos PR-10: NO. PI-3 agrega `crm_search_contacts(filters)` + `crm_get_contact_summary(id)`.
- [ ] Cards/UI nueva: NO en PR-10. PR-11 trae UI; PI-3 trae cards copilot.
- Razón scope: PR-10 = API foundation. Copilot integration capa arriba (no bloquea ni se beneficia de PR-10 inmediato — telemetría PI-3 dirá).

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Pre-flight | `nicolify-context-builder` (Haiku) | `prompts/00-context-prep.md` | `CONTEXT-BRIEF.md` |
| Pre-design | `nicolify-architect` (Opus) | `prompts/01-architect-start.md` | `CONTRACT.md` |
| Implementation | `nicolify-backend` (Sonnet) | `prompts/02-builder-start.md` | code + tests + `IMPL-LOG.md` |
| Audit (auto-spawned) | `nicolify-backend-auditor` (Opus) | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/crm.md` update |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| API endpoint | `backend/src/modules/crm/api/contacts.py` | NEW |
| API DTOs | `backend/src/modules/crm/api/dto/contacts.py` | NEW |
| Service | `backend/src/modules/crm/application/services/contact_query_service.py` | NEW |
| Filter schema | `backend/src/modules/crm/api/dto/contact_filters.py` | NEW |
| Cross-module port | `backend/src/shared/links/ports/campaigns.py` | EXTEND si necesario para `has_campaign_engagement` batch |
| Router mount | `backend/src/main.py` | Mount `/api/v1/contacts/` |
| Tests integration | `backend/tests/modules/crm/test_contacts_api.py` | NEW |
| Tests arch | `backend/tests/architecture/test_contacts_filter_params_forward_compat.py` | NEW |
| current-state | `docs/pm-nico/current-state/crm.md` | append capability lineage |

## Tests requeridos (TDD strict)

- `test_contacts_api.py` — integration sin mocks (real DB fixture):
  - Tenant isolation: tenant A NO ve contactos tenant B (cross-tenant leak gate)
  - Filter `lifecycle_stage_in=[MQL,SQL]` retorna solo MQL+SQL
  - Filter `score_min=40&score_max=80` retorna dentro rango
  - Filter `has_telegram_id=true` retorna solo con `telegram_id`
  - Filter `has_email=true` retorna solo con email
  - Filter `has_phone=true` retorna solo con phone
  - Filter `created_after=2026-04-01` filtra correcto
  - Filter `has_campaign_engagement=true` retorna leads con CampaignTask SENT (consume `CampaignsLookupPort`)
  - Search `q=juan` matchea name + email + phone
  - Pagination `page=2&size=10` retorna correct slice + total count
  - Detail `GET /{id}` retorna fields completos + 404 si tenant otro
  - Stub 501 `/journey` retorna `Retry-After: PI-3` + descriptive body
  - Stub 501 `/campaigns` mismo pattern
  - response_model strict: validator rechaza fields no declarados
- `test_contacts_filter_params_forward_compat.py` — arch test:
  - FilterParams schema MUST include hardcoded list de todos PI-3 filters
  - Ratchet shrink-only (futuro adds OK, removes FAIL test)

## Aceptación

- [ ] CONTEXT-BRIEF.md ready (Haiku)
- [ ] CONTRACT.md ready (architect Opus, EXTEND-vs-NEW decided)
- [ ] Code + tests + IMPL-LOG (builder Sonnet)
- [ ] gate-output.json overall.any_fail = false
- [ ] REVIEW.md verdict PASS (auditor Opus)
- [ ] Tenant isolation verified en cada query (incl. detail)
- [ ] response_model en cada endpoint (PII rule)
- [ ] FilterParams schema soporta TODOS PI-3 filters listed
- [ ] 501 stubs `/journey` + `/campaigns` documentados OpenAPI
- [ ] Arch test forward-compat verde
- [ ] RESULT.md + current-state/crm.md update con lineage
- [ ] Decisiones registradas en `decisions.md` PI

## Riesgos

| Riesgo | Mitigación |
|---|---|
| `has_campaign_engagement` filter requiere N+1 query | Architect diseña batch lookup en `CampaignsLookupPort`; service usa subquery EXISTS |
| FilterParams schema crece sin control PI-3 | Arch test shrink-only force update list cuando add filter |
| `LeadModel` vs `CustomerProfileModel` overlap → qué tabla query | Architect lee schema vivo + decide en CONTRACT (1 source of truth) |
| Offset pagination escalabilidad 1000+ leads | Documented defer cursor follow-up post-S4 |
| Cross-module port leak (importar campaigns directo) | Builder usa SOLO `CampaignsLookupPort`; auditor cross-module import gate |
