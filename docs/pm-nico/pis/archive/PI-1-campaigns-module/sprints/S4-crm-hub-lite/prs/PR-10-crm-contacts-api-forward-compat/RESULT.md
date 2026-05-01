# RESULT — PR-10-crm-contacts-api-forward-compat

| Campo | Valor |
|---|---|
| Estado | shipped |
| Cierre | 2026-04-30 |
| PR atómico | commit `c0cad8de` |
| Verdict | PASS (REVIEW.md fallback PM main session) |

## Outcome real vs esperado

✅ API REST forward-compat shipped. UI PR-11 puede consumir 18 canonical filters desde día 1; PI-3 expande UI sin reescribir BE. Cero refactor garantizado por arch test ratchet.

## Surface entregada (consumible por PR-11 + PI-3)

- `GET /api/v1/contacts/` — paginated list con 18 canonical filters PI-3 forward-compat
- `GET /api/v1/contacts/{id}` — detail unified `CustomerProfile + LEFT JOIN Lead`
- `GET /api/v1/contacts/{id}/journey` — 501 deferred PI-3 + Retry-After: PI-3
- `GET /api/v1/contacts/{id}/campaigns` — 501 deferred PI-3 + Retry-After: PI-3
- `GET /api/v1/contacts/_filter-schema` — metadata FE dynamic UI

DTOs Pydantic v2 strict (extra="forbid"):
- `ContactFilterParams` — 18 fields canonical
- `ContactListItem` — subset tabla lite
- `ContactDetail` — schema completo (drawer S4 + page PI-3 reuse)
- `ContactIdentity` — multi-channel
- `DeferredEndpointResponse` — canonical 501 schema
- `FilterSchemaResponse` — metadata endpoint

Service `ContactQueryService` — 2 methods async + 8 helpers.

Cross-module read via `CampaignsLookupPort` batch (PR-8 surface) — 2-step strategy evita N+1.

## Capability lineage (current-state/crm.md update)

```md
### Cap: Listado paginado de contactos con filtros forward-compat
- Introducida: PR-10 (PI-1, S4-crm-hub-lite, commit c0cad8de, 2026-04-30)
- Estado: live
- Operable copilot: pendiente PI-3 (tools wrappean PR-10 API)
- Endpoints: GET /api/v1/contacts (paginated), GET /api/v1/contacts/{id} (detail), GET /api/v1/contacts/_filter-schema (metadata)
- 18 canonical filters declarados forward-compat (UI lite expone subset PR-11)
- 501 stubs deferred PI-3: /journey, /campaigns
- Cross-module read CampaignsLookupPort (PR-8) para has_campaign_engagement
```

## Decisiones tomadas (append decisions.md PI-1)

| ID | Decisión |
|---|---|
| D-48 | NEW endpoint group `/api/v1/contacts/` (no EXTEND legacy `/leads`) — scope distinto + zero breaking |
| D-49 | Source unified: `CustomerProfileModel + LEFT JOIN LeadModel` (CDP pattern) |
| D-50 | 18 canonical filters forward-compat declarados PR-10 (ratchet shrink-only) |
| D-51 | `has_campaign_engagement` strategy: 2-step batch (CampaignsLookupPort) — evita N+1 |
| D-52 | 501 stubs canonical schema `DeferredEndpointResponse` + `Retry-After: PI-3` |
| D-53 | Offset pagination MVP (cursor follow-up post-S4 si telemetría >100ms p95) |
| D-54 | `has_email`: `primary_email IS NOT NULL` (rápido, índice). PI-3 puede expand a `CustomerIdentity` |
| D-55 | Test fixture pattern: header-based tenant dispatch (single override + httpx headers) |
| D-56 | 501 stubs implementados con `JSONResponse` direct (no `response: Response`) |

## Deuda residual aceptada

| Item | Razón | Sprint destino |
|---|---|---|
| Cursor pagination | Offset MVP suficiente | PR follow-up post-S4 si telemetría dice |
| Materialized view contact list | Performance acceptable hoy | PR follow-up si p95 >100ms |
| `has_email` via `CustomerIdentity` table | `primary_email` rápido suficiente lite | PI-3 si telemetría dice |
| `# type: ignore` legacy SQLA `Column[T]` types | Pragmático con `Any` cast | Cleanup post PI-1 (migración a `Mapped[]` ortogonal) |
| Copilot tools wrappean PR-10 API | Capa arriba, no bloquea | PI-3 |

## Métricas PR-10

| Métrica | Cierre |
|---|---|
| Files NEW | 6 |
| Files MODIFY | 1 (main.py mount) |
| Lines added | 2224 |
| Tests verde nativo | 33 (31 integration + 2 arch) |
| Migrations | 0 |
| Endpoints nuevos | 5 |
| DTOs nuevos | 6 |
| Service nuevo | 1 (ContactQueryService) |
| Commits | 1 atomic |
| Auditor verdict | PASS (PM fallback, auditor agent paused) |

---

<!-- @pm: PR-10 cerrado SHIPPED. -->
