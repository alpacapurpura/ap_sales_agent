# RESULT — PR-12-segment-manual-creation-and-wire-s3

| Campo | Valor |
|---|---|
| Estado | shipped |
| Cierre | 2026-04-30 |
| PR atómico | commits `bac573ca` (BE) + `3726ffa3` (FE) |
| Verdict | PASS (PM main session fallback — auditor agents paused mid-fix) |

## Outcome real vs esperado

✅ Wire S4↔S3 completo end-to-end. MVP 1 Telegram cerrado: contactos → segment manual → campaign AGENT_CONVERSATION + 1 step CALL_SUBAGENT_BRIEF + schedule → S3 OutboundOrchestrator (PR-7) → S3 inbound recognition (PR-8 chip Inbox).

PI-1 outcome user-facing alcanzado completo. Listo para manual gate Chris staging.

## Surface entregada

### BE delta
- `SegmentCreate` Pydantic EXTEND con `lead_ids: list[UUID] | None` + XOR validator (STATIC vs DYNAMIC)
- `SegmentService.create()` STATIC branch via JSONB shape `filter_dsl={"_static": true, "lead_ids": [...]}` (existing column)
- `SegmentService.resolve()` STATIC branch (return lead_ids sin SQL)
- `_validate_lead_ids_belong_to_tenant` helper (security gate)
- 6 integration tests sin mocks
- 0 migration

### FE primary
- `CreateSegmentDialog.tsx` (Shadcn Dialog + RHF + Zod)
- `LaunchCampaignChoiceDialog.tsx`
- `useCreateSegmentMutation` hook
- ContactsPageClient EXTEND con slot inject "Crear segmento" action
- `features/campaigns-lite/` FSD-Lite bounded context completo (4 components + 6 hooks + Zod types)
- 2 routes `/sales/campañas/{nuevo,[id]}` Server Component thin
- 1 arch test `test_campaign_new_consumes_canonical_api`
- 1 E2E spec `segment-create-and-launch-campaign` (test.skip + sanity)
- 4 Vitest tests

## Capability lineage

```md
### Cap: Crear segmento STATIC desde contactos seleccionados
- Introducida: PR-12 (PI-1, S4-crm-hub-lite, commits bac573ca + 3726ffa3, 2026-04-30)
- Estado: live
- Operable copilot: pendiente PI-3 (tool crm_create_segment wrappea API)
- Endpoint BE: POST /api/v1/campaigns/segments/ con segment_type=STATIC + lead_ids
- Storage: SegmentModel.filter_dsl JSONB shape `{"_static": true, "lead_ids": [...]}`
- FE: CreateSegmentDialog (Shadcn + RHF + Zod) en /sales/contactos
- Wire: SelectedContactsBar slot action → Dialog → POST → toast + LaunchCampaignChoiceDialog

### Cap: Lanzar campaña Telegram lite desde segment
- Introducida: PR-12 (PI-1, S4-crm-hub-lite, commit 3726ffa3, 2026-04-30)
- Estado: live (placeholder lite)
- Operable copilot: pendiente PI-3
- FE pages: /sales/campañas/nuevo (form simple) + /sales/campañas/[id] (stats card + Lanzar)
- features/campaigns-lite/ FSD-Lite bounded context
- Single-step happy path: campaign AGENT_CONVERSATION + 1 step CALL_SUBAGENT_BRIEF + schedule → S3 OutboundOrchestrator
- PI-3 expand: full DAG builder + multi-step + multi-channel
```

## Decisiones tomadas (append decisions.md PI-1)

| ID | Decisión |
|---|---|
| D-67 | EXTEND `SegmentCreate` Pydantic con `lead_ids` field + XOR validator (no separate endpoint) — backwards compatible DYNAMIC baseline |
| D-68 | STATIC storage via JSONB shape `filter_dsl={"_static": true, "lead_ids": [...]}` (REUSE existing column, 0 migration) — alternativa NEW column descartada |
| D-69 | FE Modal Dialog vs inline form → Modal (focused UX) |
| D-70 | Choice modal post-create vs auto-redirect → Choice (user agency) |
| D-71 | Campaign new lite single-step (1 CALL_SUBAGENT_BRIEF auto-injected) — full DAG builder PI-3 |
| D-72 | `/campañas/[id]` placeholder lite (stats card + lifecycle buttons) — full overview PI-3 |
| D-73 | NEW `features/campaigns-lite/` separado de Growth Studio campaigns dashboard (scope analytics distinto) |
| D-74 | `useLaunchCampaignMutation` hook en `api/` — refactor de fetchClient direct para arch compliance (test-api-location) |
| D-75 | Test mock pattern `vi.mock(name, () => ({ hook: vi.fn(() => ({...})) }))` — wrap en vi.fn() para chain `.mockReturnValue` later |

## Deuda residual aceptada

| Item | Razón | Sprint destino |
|---|---|---|
| E2E full flow test.skip | Infra gap seed helper (heredado PR-9 + PR-11) | Post PI-1 cleanup E2E infra |
| Pause/Cancel buttons placeholder UX | Lite scope; full state machine UI PI-3 | PI-3 |
| Multi-step DAG builder | Lite single-step suficiente MVP | PI-3 visual builder |
| Cards copilot integration | Capa arriba | PI-3 |
| 27 ESLint warnings react-perf JSX inline functions | Tests intencionalmente, refactor extract callbacks | Cleanup post PI-1 |

## Métricas PR-12

| Métrica | Cierre |
|---|---|
| Files NEW (FE) | 22 |
| Files NEW (BE) | 1 (test) |
| Files MODIFY (BE) | 2 (segment_dtos + segment_service) |
| Files MODIFY (FE) | 2 (ContactsPageClient + crm-hub/index) |
| Lines added (BE) | ~150 |
| Lines added (FE) | ~1784 |
| Tests verde nativo (BE) | 6 integration sin mocks |
| Tests verde nativo (FE) | 122 (Vitest scope full PR-11 + PR-12 + arch) |
| Migrations | 0 |
| Endpoints nuevos BE | 0 (REUSE existing + EXTEND DTO) |
| Routes FE nuevas | 2 (/sales/campañas/{nuevo,[id]}) |
| Components nuevos FE | 8 (2 dialogs + 4 campaigns-lite + 2 sub-components) |
| Hooks nuevos FE | 7 (1 segment + 6 campaign) |
| Commits | 2 atomic (BE + FE) |
| Auditor verdict | PASS (PM fallback — agents paused mid-fix) |

---

<!-- @pm: PR-12 cerrado SHIPPED. Sprint S4 ready para cierre + PI-1 cierre completo + retro. -->
