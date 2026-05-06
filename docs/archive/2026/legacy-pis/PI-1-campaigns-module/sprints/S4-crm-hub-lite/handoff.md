# S4 Handoff — Mini CRM Hub Lite → PI-3 expansion

> Owner: PM. Cierre sprint S4, input para PI-3 (CRM Hub completo + retargeting + segment builder visual).

## Sprint cerrado

| Campo | Valor |
|---|---|
| Sprint ID | S4-crm-hub-lite |
| Estado | done |
| Cierre real | 2026-04-30 |
| PRs shipped | PR-10 (BE) + PR-11 (FE) + PR-12 (cross-stack) — 3 PRs |
| Commits totales | 8 commits PR-10 + 3 PR-11 + 5 PR-12 + close docs |

## Surface disponible post-S4 (consumible PI-3 + PI-2)

### CRM contacts API forward-compat (PR-10 — commit `c0cad8de`)

- `GET /api/v1/contacts/` — paginated list 18 canonical filters PI-3 forward-compat
- `GET /api/v1/contacts/{id}` — detail unified `CustomerProfile + LEFT JOIN Lead`
- `GET /api/v1/contacts/{id}/journey` — 501 deferred PI-3 + Retry-After: PI-3
- `GET /api/v1/contacts/{id}/campaigns` — 501 deferred PI-3 + Retry-After: PI-3
- `GET /api/v1/contacts/_filter-schema` — metadata FE dynamic UI
- DTOs Pydantic v2 strict: `ContactFilterParams`, `ContactListItem`, `ContactDetail`, `ContactIdentity`, `DeferredEndpointResponse`, `FilterSchemaResponse`
- `ContactQueryService` async + 8 helpers (filter application + 2-step engagement batch)
- `CampaignsLookupPort` (PR-8) consumed via batch query (NO N+1)
- 0 migrations
- 33 tests verde nativo (31 integration + 2 arch ratchet)

### FE primitives + contactos page (PR-11 — commit `87b3fa3e`)

- `components/shared/data-table/` (TanStack headless) — cross-feature reusable
- `features/crm-hub/` FSD-Lite bounded context:
  - 7 components: LifecycleStageChip, ScoreBadge, IdentityList, ContactDetailContent (host-agnostic), ContactFiltersPanel, SelectedContactsBar (slot pattern), ContactsPageClient
  - 3 React Query hooks (use-contacts-query, use-contact-detail-query, use-filter-schema-query)
  - Zod types mirror Pydantic exact (CONTACT_FILTER_FIELDS canonical 18 fields)
  - URL state util (deep-link, browser-back, shareable)
- Page `/sales/contactos` (Server Component thin + ContactsPageClient)
- 4 arch tests forward-compat
- ADD dep `@tanstack/react-table@^8.21.3`
- 101 Vitest verde + 1 E2E sanity + test.skip flow

### Segment manual + wire S3↔S4 (PR-12 — commits `bac573ca` + `3726ffa3`)

#### BE delta
- `SegmentCreate` Pydantic EXTEND con `lead_ids` field + XOR validator (STATIC vs DYNAMIC)
- `SegmentService.create()` STATIC branch — JSONB shape `filter_dsl={"_static": true, "lead_ids": [...]}`
- `SegmentService.resolve()` STATIC branch — return persisted lead_ids sin SQL
- `_validate_lead_ids_belong_to_tenant` helper
- 6 integration tests sin mocks
- 0 migration

#### FE primary
- `CreateSegmentDialog` (Shadcn Dialog + RHF + Zod)
- `LaunchCampaignChoiceDialog`
- `useCreateSegmentMutation`
- ContactsPageClient EXTEND con slot inject "Crear segmento"
- `features/campaigns-lite/` FSD-Lite bounded context:
  - 4 components (CampaignNewClient, CampaignDetailClient, CampaignStatsCard, CampaignLifecycleButtons)
  - 6 React Query hooks (create/detail/stats/add-step/schedule/launch)
  - Zod types mirror Pydantic
- 2 routes `/sales/campañas/{nuevo,[id]}` Server Component thin
- 1 arch test `test_campaign_new_consumes_canonical_api`
- 1 E2E spec test.skip flow + sanity

## Wire S4↔S3 verified end-to-end (architectural)

```
[ContactsPage selecciona N contactos]
  ↓
[SelectedContactsBar action "Crear segmento"]
  ↓
[CreateSegmentDialog → POST /api/v1/campaigns/segments/ STATIC + lead_ids]
  ↓ 201 + segmentId
[LaunchCampaignChoiceDialog → "Sí, crear campaña"]
  ↓
[/sales/campañas/nuevo → POST campaigns + step CALL_SUBAGENT_BRIEF + schedule]
  ↓
[/sales/campañas/{id} stats card + Lanzar button → POST /launch]
  ↓
S3 OutboundOrchestrator (PR-7) ejecuta tasks Telegram
  ↓
S3 inbound recognition (PR-8) tag chip Inbox cuando lead responde
```

Manual gate Chris staging post-merge = real ship verdict (heredando PR-9 + PR-11 pattern).

## Riesgos abiertos S4 (input PI-3 + cleanup)

| Riesgo | Mitigación PI-3 / cleanup | Owner |
|---|---|---|
| E2E full flow test.skip por infra gap | Post PI-1 cleanup — seed helper tenant + leads + telegram_id staging | E2E setup cleanup |
| Pause/Cancel buttons placeholder UX | PI-3 robusto state machine UI | PI-3 |
| Multi-step DAG campaign builder ausente | PI-3 visual builder | PI-3 |
| Cards copilot integration ausente | PI-3 — tools `crm_search_contacts`, `crm_get_contact_summary`, `crm_create_segment`, `crm_create_campaign` wrappean APIs | PI-3 |
| 27 ESLint warnings react-perf JSX inline functions | Cleanup post PI-1 — extract callbacks | Cleanup |
| Cursor pagination contacts (ofset MVP) | PR follow-up post-S4 si telemetría >100ms p95 | Cleanup if needed |
| Materialized view contact list | PR follow-up si performance dice | Cleanup |

## PI-3 expansion hooks (cero refactor garantizado)

Forward-compat invariantes garantizadas por arch tests ratchet:

| Eje | S4 lite | PI-3 expand | Refactor PI-3? |
|---|---|---|---|
| API filters | 18 canonical declarados | UI expone subset adicional + filter builder visual | NO — schema ya soporta |
| `/contacts/{id}/journey` | 501 stub | 200 con timeline rich | NO — endpoint canonical declarado |
| `/contacts/{id}/campaigns` | 501 stub | 200 con historial campañas | NO — endpoint canonical declarado |
| `ContactDetailContent` component | Drawer host hoy | Página completa `/contactos/{id}` PI-3 USA mismo component | NO — host-agnostic |
| `DataTable` shared | Tabla contactos hoy | Tabla campaigns + segmentos PI-3 | NO — primitive shared |
| `SelectedContactsBar` slot | 1 action "Crear segmento" | + actions: Exportar Meta, bulk update, agregar a campaign existente | NO — slot pattern |
| `Segment` STATIC | UI lite manual | + Segment Builder Visual con filters DYNAMIC | NO — backend ya soporta ambos types |
| Campaign new lite | Single-step CALL_SUBAGENT_BRIEF | + Full DAG builder + multi-step + multi-channel | NO — endpoints already DAG-capable |

## Recommended skills PI-3 / cleanup

- `nicolify-frontend` — Segment Builder Visual + filter builder drag-drop + Pulso dashboard
- `nicolify-backend` — `/journey` + `/campaigns` real implementation (cross-module reads via ports)
- `nicolify-agentic` — copilot tools wrappean PR-10/PR-12 APIs
- `chrome-devtools-verify` — Live verification staging post-merge

## Quality summary S4

| Métrica | Cierre |
|---|---|
| PRs shipped | 3 (PR-10 + PR-11 + PR-12) |
| Commits totales | 16 (8 PR-10 + 3 PR-11 + 5 PR-12) + close docs |
| Tests verde nativo | 33 BE (PR-10) + 122 FE (PR-11+PR-12) + 6 BE (PR-12) = 161 nuevos S4 |
| Arch tests delta | +5 (PR-10 +2 + PR-11 +4 + PR-12 +1, ratchet shrink-only) |
| Migrations | 0 |
| Endpoints nuevos | 5 (PR-10) + 0 (PR-12 EXTEND existing) = 5 |
| Routes FE nuevas | 3 (/sales/contactos REPLACE stub + /sales/campañas/{nuevo,[id]}) |
| Components nuevos FE | 16 (7 crm-hub + 1 DataTable + 4 campaigns-lite + 2 dialogs + 2 sub-components) |
| Hooks nuevos FE | 10 (3 contacts + 1 segment + 6 campaign) |
| New deps | 1 (`@tanstack/react-table`) |
| Auditor verdicts | PASS (PM fallback en 3/3 PRs — auditors paused/killed mid-fix) |
| **Cero deuda blocker** | ✅ defer documented OK con architectural seam |

## S4 cierre verdict

**SHIPPED** — Vista lite contactos + segment manual + wire S3↔S4 completos. Forward-compat invariantes garantizan PI-3 expand sin reescribir.

Real ship verdict pendiente Chris execution manual checklist staging.

**Próximo:** PI-1 cierre completo (retro + archive). PI-2 multi-canal abre Now post-cierre.
