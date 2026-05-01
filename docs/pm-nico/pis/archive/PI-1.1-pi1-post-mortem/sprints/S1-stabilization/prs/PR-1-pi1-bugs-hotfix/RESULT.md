# PR-1-pi1-bugs-hotfix — RESULT

## Meta cierre

| Campo | Valor |
|---|---|
| PR ID | PR-1-pi1-bugs-hotfix |
| Estado final | shipped (scope reduced) |
| Fecha cierre | 2026-05-01 |
| Owner cierre | /pm |
| Commits relevantes | `9acac22b` FE fix · `1417362d` REVIEW-FE · `5fd1f5ca` BE fix · `89c6a323` REVIEW-BE · `b0700be9` chore agents maxTurns · `03f5462c` revert WIP agentic |

## Outcome real vs esperado

### Bugs SHIPPED ✅

| Bug | Síntoma | Fix shipped | Verificación |
|---|---|---|---|
| **#1 — `/sales/contactos` 404** | UI tabla vacía + toast "No pudimos cargar contactos" | BE `crm/api/contacts.py` dual-decorator `@router.get("")` + `@router.get("/")` matching `brand/buyer_personas.py:46-47`. **Real RCA: CloudFlare Tunnel strip trailing slash.** FE `use-contacts-query.ts:26` añadió `/` antes `?` (no era el bug raíz pero coexiste sin daño) | `curl /api/v1/contacts` → 401 (no 404). `curl /api/v1/contacts/` → 401. Verified live via chrome-devtools |
| **#4 — `/sales/campañas/*` 404 + sidebar orfana** | Next.js 16 dev no compila folder con `ñ` + sidebar no linkea | FE rename folder `campañas` → `campanas` + sidebar entry "Campañas" añadida en `AppSidebar.tsx` + refs internos updated | Sidebar muestra link Campañas en visionarias tenant. URL slug ASCII coincide con `growth-studio/campanas` convention |

### Bugs DEFERRED a PR-2 🔄

| Bug | Severidad | Razón defer | Owner |
|---|---|---|---|
| **#2 — Sales agent observability traces 0 rows globalmente** | CRÍTICO | WIP agentic builder duplicó pattern copilot `turn_envelope.py` en `modules/sales_agent/observability/recording/` en vez de extraer a `shared/agent_observability/recording/`. Chris flagged anti-pattern. Reverted commit `73ae51d2` para abrir scope correcto en PR-2 con architect-driven shared abstraction | `PR-2-shared-agent-observability` |
| **#7 — `PersonalityProfileModel` sin `model_dump`** | CRÍTICO | Discovered runtime via Telegram smoke. SQLA ORM treated as Pydantic en `brand/application/services/brand_data_adapter.py:46`. Out-of-scope este PR (módulo brand) | Bug aislado backend negocio — abrir PR dedicado |
| **#8 — `FXResolver()` sin `http_client_factory`** | CRÍTICO | `factory.py:116, 168` instancian `FXResolver()` sin arg requerido. Causa real `sales_agent_observability_context_factory_failed`. Forms part of PR-2 shared scope | `PR-2-shared-agent-observability` |
| **#9 — LiteLLM container exited (mount config.yaml dir/file)** | CRÍTICO infra | Docker compose mount conflict, paralelo PI-5 quizás. Out-of-scope este PR | Infra dedicated PR |
| **#5 — Maximum update depth (FE)** | a investigar | No reproducido post-fix #1+#4. Si recurre → ticket dedicado | TBD |
| **#6 — Tenant switch non-persist** | medio (UX) | Clerk publicMetadata.tenant_id stale post-dropdown. `(main)/page.tsx:21` redirect to stale → bouncing. Investigation completed (RCA documented). Defer fix | PR dedicado FE Clerk session |

### Bugs descartados (no son bugs)

| Bug | Razón |
|---|---|
| **#3 — Streamlit user_id confusion** | Chris vio `copilot_trace_event` (4260 rows) en `trazas.py`, asumió era sales_agent. UX confusion, no bug técnico. Defer mejora UX a PI-3 sales-agent-improvement |

## Anti-pattern auto-detectado (post-mortem)

**Duplicación de código `turn_envelope.py` agentic builder.** PM proceso falló en 5 puntos (audit detallado en `process-learnings.md`):

1. PM marcó "Existing systems audit" PR.md como completo SIN ejecutar grep cross-module obligatorio del template
2. PM skipeó architect Opus por "scope hotfix" — incorrecto cuando scope expand a shared infra
3. Builder agentic prompt sin Step 0 grep gate obligatorio
4. Auditor iter 1 vio `copilot-expert (envelope precedent)` en skills usados, NO flagged como duplication
5. PM no validó "¿es nueva infra o extensión?" en Walking Skeleton

**Acciones correctivas tomadas (commits separados — ver `PR-2-shared-agent-observability`):**
- Nueva rule `rules/anti-duplication.md` con inventario canónico shared abstractions
- PR.md template — bloque "Existing systems audit" convertido a mandatory con paths grepped + line numbers
- Builder prompts template — Step 0 grep gate obligatorio
- Auditor agents — Cat 12 mirror detection FAIL severity
- Skills `copilot-expert` + `sales-agent-expert` — warning shared abstractions inventory
- `process-learnings.md` — case study este PR como cautionary tale

## Surface entregada (final)

### FE

- `frontend/src/features/crm-hub/api/use-contacts-query.ts` line 26 — added trailing `/`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/` → renamed to `campanas/` (ASCII)
- `frontend/src/components/shared/layout/AppSidebar.tsx` — added "Campañas" entry under Closer Studio
- `frontend/src/features/campaigns-lite/components/CampaignNewClient.tsx` — refs updated
- `frontend/src/features/crm-hub/components/LaunchCampaignChoiceDialog.tsx` — refs updated
- `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` — refs updated
- `frontend/e2e/specs/smoke/sales-campaigns-route.spec.ts` — new E2E smoke
- `frontend/src/features/crm-hub/api/__tests__/use-contacts-query.test.ts` — regression test trailing slash

### BE

- `backend/src/modules/crm/api/contacts.py` — dual-decorator pattern `("")` + `("/")` matching brand precedent
- `backend/tests/modules/crm/test_contacts_api.py` — 2 regression tests (no-slash + with-slash returns 200/auth-required)

### docs/pm-nico

- `docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/` (new mini-PI for post-mortem hotfixes)
- `IMPL-LOG-fe.md`, `IMPL-LOG-be.md`, `REVIEW-frontend.md`, `REVIEW-backend.md`, `gate-output.json`
- `RESULT.md` (this file)

## Métricas cierre

| Métrica | Target | Real |
|---|---|---|
| Bugs FE+BE shipped | #1+#4 | ✅ ambos |
| Bugs deferred docs ok | todos #2/#5/#6/#7/#8/#9 | ✅ documentados con owner |
| Real persistence test verde sales_agent | ≥1 row trace | ❌ deferred PR-2 |
| Live verify chrome-devtools `/sales/contactos` | render 15 leads | ⚠️ blocked Bug #6 sticky redirect — verified vía DB+API curl 401 instead |
| Real Telegram message → trace | ≥1 row | ❌ deferred — runtime errors Bug #7+#8+#9 cascaded |
| Cero refactor cross-module pollution | 0 archivos copilot tocados desde mi PR | ✅ |
| Cero `--no-verify` commits | 0 | ✅ |

## Lineage update current-state

`docs/pm-nico/current-state/campaigns.md`:
- Cap "CRM Contacts list endpoint": added lineage `PR-1-pi1-bugs-hotfix (PI-1.1, commit 5fd1f5ca, 2026-05-01) — fixed CF tunnel slash + dual decorator`
- Cap "Sales Campañas wizard route": added lineage `PR-1-pi1-bugs-hotfix (PI-1.1, commit 9acac22b, 2026-05-01) — folder rename ASCII + sidebar entry added`

`docs/pm-nico/current-state/sales_agent.md`:
- Cap "Observability traces persistence": status changed `live → broken (deferred PR-2)`
- New section "Known issues" — Bugs #7+#8+#9 listed con paths + owners

## Decisiones registradas

→ `pis/active/PI-1.1-pi1-post-mortem/decisions.md`:
- D-1: PI-1 cerrado prematuramente sin manual gate Chris staging — PR-1 hotfix retroactivo
- D-2: Bug #2 deferred a PR-2 shared-agent-observability con architect mandatory
- D-3: PM process gaps documented — preventive measures committed separately

## Riesgos identificados

| Riesgo | Mitigación |
|---|---|
| Bugs #7+#8+#9 cascade en producción | Manual gate Chris staging real obligatorio antes prod deploy. Bug #8 specifically blocks sales_agent observability — no regression risk vs current state (always 0 traces) but no improvement either |
| Refactor PR-2 large scope crash | Architect-driven workflow obligatorio. Builder Step 0 grep gate. Auditor Cat 12. Process redundancy |
| Cross-session collision PI-5 PR-2 | PI-5 PR-2 modifies copilot/. PR-2 shared-observability tocará copilot Y sales_agent. Coordination: PI-5 PR-2 mergea primero, luego PR-2 shared |

## Próximo paso

Abrir `PR-2-shared-agent-observability` con architect-driven CONTRACT.md + Step 0 grep gates + Cat 12 mirror detection.
