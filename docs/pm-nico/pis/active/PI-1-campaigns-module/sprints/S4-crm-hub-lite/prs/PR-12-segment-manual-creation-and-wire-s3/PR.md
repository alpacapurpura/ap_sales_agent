# PR-12-segment-manual-creation-and-wire-s3

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-12-segment-manual-creation-and-wire-s3 |
| Sprint padre | S4-crm-hub-lite |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | feature |
| Esfuerzo | M |
| Owner PM | /pm |
| Surface | cross-stack — verify BE existing endpoints (segments + campaigns) + new FE pages/modals |
| Builder | `nicolify-frontend` (Sonnet) primario + `nicolify-backend` (Sonnet) si segments endpoint EXTEND necesario |
| Auditor | `nicolify-frontend-auditor` + `nicolify-backend-auditor` (si BE touched) |

## Problema (user-facing)

Después de PR-11, user puede ver/seleccionar contactos pero NO puede actuar sobre ellos. JTBD: "Quiero seleccionar contactos, agruparlos en segmento, y lanzar campaña Telegram inmediatamente." Wire S4 ↔ S3.

## Outcome esperado

End-to-end MVP 1 completo:
1. `/sales/contactos` → seleccionar N contactos → click "Crear segmento" en SelectedContactsBar
2. Modal Dialog form (RHF + Zod) → name + description + lead_ids preseed → POST `/api/v1/segments` (existing S1 PR-3) con `type=STATIC` + `lead_ids`
3. Toast success → modal "¿Lanzar campaña Telegram ahora?" choice
4. Choice "Sí" → navigate `/campañas/nuevo?segment_id={id}` → form simple (name, description, type=AGENT_CONVERSATION, segment_id pre-seeded) → POST `/api/v1/campaigns` + 1 step `CALL_SUBAGENT_BRIEF` + schedule
5. `/campañas/{id}` placeholder con stats card (consume PR-8 stats + GET campaign) + buttons Lanzar/Pausar

**Wire S3↔S4 completo**: contactos → segment → campaign → Telegram outbound (PR-7) → inbound recognition (PR-8).

## Walking skeleton

| # | Layer | Entregable |
|---|---|---|
| 1 | BE verify | Confirmar `POST /api/v1/segments` existing soporta `{type: "STATIC", lead_ids: [UUID...]}` (S1 PR-3 surface). Si gap → mini extend (architect decide) |
| 2 | FE modal | `crm-hub/components/CreateSegmentDialog.tsx` Shadcn Dialog + RHF+Zod |
| 3 | FE wire 1 | SelectedContactsBar action "Crear segmento" abre Dialog |
| 4 | FE post-create | Toast + secondary modal "Lanzar campaña Telegram?" Dialog |
| 5 | FE route 1 | `/sales/campañas/nuevo/page.tsx` Server thin + `CampaignNewClient.tsx` form |
| 6 | FE route 2 | `/sales/campañas/[id]/page.tsx` placeholder (stats card + lifecycle buttons) |
| 7 | E2E | smoke flow contactos → segment → campaign → schedule |
| 8 | Arch test | 1 test consume canonical API only |

## Soluciones consideradas

| Eje | Opción | Veredicto |
|---|---|---|
| **Modal vs inline form** | A — Modal Dialog focused | **ELEGIDA** (focused, less clutter) |
| | B — Inline | descartada (peor UX selección) |
| **Auto-redirect vs choice** | A — Choice modal "Lanzar campaña?" | **ELEGIDA** (user agency) |
| | B — Auto-redirect | descartada (forces flow) |
| **Campaign new lite** | A — Single-step happy path (1 step CALL_SUBAGENT_BRIEF auto-injected) | **ELEGIDA** (S4 lite scope) |
| | B — Full DAG builder | descartada (PI-3 scope) |
| **`/campañas/[id]` page** | A — Placeholder stats card + lifecycle buttons | **ELEGIDA** (S4 lite + reuse PR-8 stats) |
| | B — Empty placeholder | descartada (CampaignTag chips de PR-8 dejan a 404) |

## Validación técnica preliminar

- BE existing endpoints (verify):
  - `POST /api/v1/segments` (S1 PR-3) — verificar `body: {name, description, type: STATIC, lead_ids: list[UUID]}`
  - `POST /api/v1/campaigns` (S1 PR-4) — verificar `body: {name, description, type: AGENT_CONVERSATION, segment_id, ...}`
  - `POST /api/v1/campaigns/{id}/steps` o body steps inline — verificar pattern create campaign con 1 step
  - `GET /api/v1/campaigns/{id}` (S1 PR-4) — campaign detail
  - `GET /api/v1/campaigns/{id}/stats` (PR-8) — stats response
  - Schedule mechanism: `POST /api/v1/campaigns/{id}/schedule` o status transition
- FE schema vivo:
  - `frontend/src/components/ui/dialog.tsx` (Shadcn Dialog + Form integration)
  - `frontend/src/components/ui/sonner.tsx` (toast)
  - RHF + Zod existing patterns: buscar grep `useForm.*zodResolver` para ejemplos
- Migrations: 0
- Estimated: 1 architect + 1 builder cross-stack (paralelo BE check + FE) + auto-audit

## Existing systems audit (architect-mandatory)

Subsystems: `segment create`, `campaign create + schedule`, `dialog form pattern`, `routes campañas`.

Architect ejecuta:
- `grep -rn "POST /segments\|create_segment\|@router.post.*segment" backend/src/modules/campaigns/`
- `grep -rn "create_campaign\|@router.post.*campaign\|schedule_campaign" backend/src/modules/campaigns/`
- `grep -rn "useForm\|zodResolver\|FormSchema" frontend/src/features/` (FE form pattern reference)
- `find frontend/src/app/(main)/[tenantId]/(dashboard) -name "page.tsx" -path "*campañas*"` (route pattern)
- `find frontend/src/features/closer-studio -type f` (FE form/modal patterns)

EXTEND vs NEW:
- Segments POST: **VERIFY existing** (S1 PR-3 spec). NEW solo si gap real.
- Campaigns POST: **VERIFY existing** (S1 PR-4). Likely ready.
- Schedule: **VERIFY existing** (S1 PR-4 + S2 PR-5 orchestrator).

## Decisiones diferidas

- **Full campaign DAG builder**: PI-3 visual builder
- **Pause/resume mid-execution UX**: lite buttons en `/campañas/[id]`; PI-3 robusto state machine UI
- **Campaign step types diversos**: hoy solo `CALL_SUBAGENT_BRIEF`; PI-3 multi-step flows

## Out of scope

- Multi-step DAG campaign builder
- Campaign analytics dashboard rich (PR-8 stats card minimal OK)
- Edit campaign post-launch
- Bulk launch campaigns

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? **Sí (parcial)** — copilot tool `crm_create_campaign(segment, channel, template)` capa arriba PI-3
- [ ] Tools nuevos PR-12: NO
- [ ] Cards/UI nueva: NO
- Razón scope: PR-12 = web UI MVP 1 closure. Copilot integration PI-3.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Pre-flight | `nicolify-context-builder` (Haiku) | `prompts/00-context-prep.md` | `CONTEXT-BRIEF.md` |
| Pre-design | `nicolify-architect` (Opus) | `prompts/01-architect-start.md` | `CONTRACT.md` (BE verify + FE TS contract) |
| Implementation | `nicolify-frontend` (Sonnet) primary + `nicolify-backend` (Sonnet) si BE extend | `prompts/02-builder-start.md` | code + tests + `IMPL-LOG.md` |
| Audit | `nicolify-frontend-auditor` + `nicolify-backend-auditor` (si BE) auto-spawned | `prompts/03-auditor-start.md` | `REVIEW-frontend.md` + `REVIEW-backend.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/{crm,campaigns}.md` updates |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| FE modal | `frontend/src/features/crm-hub/components/CreateSegmentDialog.tsx` | NEW |
| FE modal | `frontend/src/features/crm-hub/components/LaunchCampaignChoiceDialog.tsx` | NEW |
| FE wire | `frontend/src/features/crm-hub/components/SelectedContactsBar.tsx` (PR-11) | EXTEND con action "Crear segmento" |
| FE API | `frontend/src/features/crm-hub/api/use-create-segment-mutation.ts` | NEW |
| FE API | `frontend/src/features/crm-hub/api/use-create-campaign-mutation.ts` | NEW |
| FE page | `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/nuevo/page.tsx` | NEW Server + `CampaignNewClient.tsx` |
| FE page | `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/[id]/page.tsx` | NEW Server + `CampaignDetailClient.tsx` |
| FE feature dir | `frontend/src/features/campaigns-lite/` | NEW (campaign-related lite components) |
| BE | `modules/campaigns/api/routers/segments_router.py` | VERIFY (no edit if STATIC + lead_ids ready); EXTEND si necesario |
| Tests | `frontend/src/features/crm-hub/components/__tests__/CreateSegmentDialog.test.tsx` | NEW |
| Tests | `frontend/src/features/campaigns-lite/components/__tests__/CampaignNewClient.test.tsx` | NEW |
| E2E | `frontend/e2e/specs/regression/sales/segment-create-and-launch-campaign.spec.ts` | NEW |
| Arch test | `frontend/src/__tests__/architecture/test_campaign_new_consumes_canonical_api.test.ts` | NEW |
| current-state | `docs/pm-nico/current-state/{crm,campaigns}.md` | append |

## Tests requeridos

### Vitest
- `CreateSegmentDialog.test.tsx` — render with selected lead_ids → submit form → mutation called with type=STATIC + correct lead_ids
- `LaunchCampaignChoiceDialog.test.tsx` — choice "Sí" → navigate; choice "Más tarde" → close
- `CampaignNewClient.test.tsx` — form submit POST campaign with segment_id pre-seeded + 1 step
- `CampaignDetailClient.test.tsx` — render stats card + Lanzar button when DRAFT

### Playwright E2E
- `segment-create-and-launch-campaign.spec.ts`:
  - Nav `/sales/contactos` → seed 3 contactos
  - Select 3 → SelectedContactsBar click "Crear segmento"
  - Dialog opens → fill name="Test segment" → submit
  - Toast success → choice modal opens
  - Click "Sí, lanzar" → navigate `/sales/campañas/nuevo?segment_id={id}`
  - Form: name="Test campaign Telegram" → submit
  - Navigate `/sales/campañas/{id}` → stats card visible (sent_count=0)
  - Click "Lanzar" → status RUNNING (mock or real)

### Arch test (Vitest TS)
- `test_campaign_new_consumes_canonical_api.test.ts` — `CampaignNewClient.tsx` import paths consume `lib/api/campaigns` + `lib/api/segments` only (no FE-fabricated endpoints)

## Aceptación

- [ ] CONTRACT.md ready (BE verify + FE TS contract)
- [ ] BE segments + campaigns POST endpoints verified ready (no edit ideal)
- [ ] Code + tests + IMPL-LOG (builder)
- [ ] gate-output.json overall.any_fail = false (FE + BE if touched)
- [ ] REVIEW-frontend.md + REVIEW-backend.md (si BE) PASS
- [ ] tsc strict 0. ESLint 0. Vitest verde
- [ ] FSD-Lite respected (campaigns-lite feature isolated)
- [ ] Tailwind tokens, Spanish neutro LATAM
- [ ] E2E smoke verde (o documented test.skip si infra gap; gate manual checklist Chris similar PR-9)
- [ ] Arch test verde
- [ ] RESULT.md + current-state/{crm,campaigns}.md updates

## Riesgos

| Riesgo | Mitigación |
|---|---|
| `POST /segments` STATIC + lead_ids no soporta validation completa | Architect VERIFY first; si extend → mini BE delta documented |
| `POST /campaigns` con 1 step inline vs separate POST step | Architect VERIFY pattern; CONTRACT decide endpoint shape |
| Schedule mechanism unclear (transition vs separate POST) | Architect VERIFY S1 PR-4 + S2 PR-5 orchestrator |
| E2E flaky por scheduler tick | Mock pattern PR-9 (Telegram bot mock); gate manual Chris staging |
| Routes `/sales/campañas/*` collision con `/growth-studio/campañas/` | Verify FE app structure — separate paths different studios |
| Form Zod schema drift Pydantic | Same pattern PR-11 mirror |
