# PR-1-pi1-bugs-hotfix

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-pi1-bugs-hotfix |
| Sprint padre | S1-stabilization |
| PI padre | PI-1.1-pi1-post-mortem |
| Estado | ready |
| Tipo | bug |
| Esfuerzo | M |
| Owner PM | /pm |
| Claimed by session | 2026-04-30 |

## Origen

Manual gate Chris staging PI-1 ejecutado 2026-04-30 vía chrome-devtools MCP. Encontró 4 bugs que debieron bloquear cierre PI-1. Retro PI-1 mark "DONE" prematuro — manual gate era el verdadero ship verdict.

## Bugs detectados

### Bug #1 — `/sales/contactos` muestra empty + toast error

**Síntoma:** UI tabla vacía + toast "No pudimos cargar contactos. Reintenta." + console error 404.

**Root cause:**
- FE `frontend/src/features/crm-hub/api/use-contacts-query.ts:26` pide `${API_URL}/api/v1/contacts?${search.toString()}` (sin trailing slash)
- BE `backend/src/modules/crm/api/contacts.py:212` registra `@router.get("/")` (con slash) montado en `/api/v1` → effective path `/api/v1/contacts/`
- BE config `redirect_slashes=False` (rule obligatoria, evita 307 POST que rompe Next.js) → no redirect → 404

**Datos OK:** 15 leads existen para tenant visionarias `6347e21e-8112-4aa1-80d3-6adaa73bf6f9`. 4 con messages Telegram reales (Christian Revilla, Brenda Pastor, Camila Clausen, Bernardo Pereyra).

**Fix:** FE `use-contacts-query.ts:26` cambiar `/api/v1/contacts?` → `/api/v1/contacts/?`. Auditar consistencia con detail (`/api/v1/contacts/${contactId}`) y filter-schema (`/api/v1/contacts/_filter-schema`) — esos OK porque path segment después del slash.

**Verdict no parche:** Este es la convención BE en 10+ módulos (`@router.get("/")`). FE estaba inconsistente. NO es band-aid.

### Bug #2 — Sales agent observability totalmente muerta

**Síntoma:** 68 mensajes Telegram reales en `messages` table (4 leads, abr 2026), pero `sales_agent_trace_event` = **0 filas globalmente** (todos tenants), `sales_agent_llm_call` = 0, `sales_agent_routing_log` = 0.

**Root cause investigation needed:**
- Recording infra existe: `observability/recording/factory.py::build_sales_agent_callback_handler`, `observability/recording/callback_handler.py::_persist_trace_event_row`
- Wired en `application/orchestrator/chat.py:327` (turn entry path) + `application/orchestrator/outbound_orchestrator.py:226` (campaigns outbound)
- Mensajes existen en `messages` (writer separado vía `message_repository.py`) pero traces no
- Hipótesis (deep investigation owner = `nicolify-agentic`):
  1. Handler best-effort silently swallowed (try/except + log warning, no DB flush)
  2. Recording uses dual-write window y legacy path no escribe (sólo S1+ path lo hace, pero S1 path no se ejecuta)
  3. AsyncSession scope incorrecto (handler graba a session que nunca commitea)
  4. Conditional skip cuando `tenant_id` o `lead_id` es None (silently bypass)
  5. Old conversations pre-instrumentation (descartado: latest message 2026-04-27 post-PI-2 close)

**Impacto:** Voice fidelity grader ciego. Costos sales_agent no rastreados. Tool exec traces no auditables. Routing decisions perdidas. PI-3 sales-agent-improvement está construyendo sobre observability que no existe.

**Fix esperado:**
1. RCA con trace logging temporal en `_persist_trace_event_row` para identificar gap exacto
2. Fix root cause (no try/except swallow)
3. Smoke test que dispara real turn → asserts INSERT en `sales_agent_trace_event` (no mock)
4. Backfill consideration: si hay messages reales sin trace, ¿generamos retro-traces? (DEFERIDO — discusión Chris)

### Bug #3 — Streamlit admin user_id confusion (NO ES BUG)

**Síntoma reportado:** Chris vio `e06bb384-9242-4db4-8419-b73005981fc9` en Streamlit panel asumiendo es lead Telegram chalreme. Real lead chalreme = `cb711aea-e0a5-42c0-b276-7a63570207bd` (Christian Revilla).

**Análisis:** Streamlit `backend/src/admin/modules/trazas.py:95` query `copilot_trace_event` (NO sales_agent). Field `user_id` en context copilot = Clerk user_id (admin humano usando copilot), no lead. UX engaña al lector.

**Verdict:** No bug. Defer mejora UX a PI-3 sales-agent-improvement (cuando construyamos sales agent traces panel — Bug #2 prerequisito).

### Bug #4 — Next.js 16 no compila rutas con `ñ` + sidebar orfana

**Síntoma:** `/sales/campañas` y `/sales/campañas/nuevo` retornan Next.js 404 pese a que `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/{nuevo,[id]}/page.tsx` existen en filesystem y container.

**Root cause:**
1. Next.js 16 dev compile **NO emite chunks** para folder name con char no-ASCII (`ñ`). Compilado `.next/dev/server/app/(main)/[tenantId]/(dashboard)/sales/` solo tiene `contactos/`, falta `campañas/`. Bug Next.js documented o limitación dev mode.
2. Sidebar `frontend/src/components/shared/layout/AppSidebar.tsx:118` linkea `/contactos` pero **NO** linkea `/campañas`. Ruta orfana incluso si compilara.

**Fix esperado:**
1. Rename folder `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/` → `campanas/` (sin ñ). Coincide con convención `growth-studio/campanas` que ya existe.
2. UI label sigue siendo "Campañas" (rule spanish-text — strings UI con ñ; URL slug es ASCII por compat técnica).
3. Add sidebar link en `AppSidebar.tsx`: title "Campañas" con icon Megaphone (o similar) → href `/${tenantId}/sales/campanas/nuevo` (entry point wizard) o `/sales/campanas` (lista — verificar si existe `page.tsx` raíz; sino, decisión defer).
4. Update referencias en `features/campaigns-lite/` y wizard internal links.

**Verdict no parche:** Convention alignment (otros routes ASCII). NO band-aid.

### Bug #5 — `Maximum update depth exceeded` (a investigar post-fix)

**Síntoma:** Browser console aislado log capturado en `docker logs visionarias_client_dev` durante navegación inicial. Componente no identificado.

**Fix:** Re-test post-PR-1 fixes con chrome-devtools, capture exact stack. Si persiste → spawn debug session con frontend-expert.

## Outcome esperado

| Bug | Verificación post-fix |
|---|---|
| #1 | `/sales/contactos` muestra 15 leads paginados, 0 console errors, X-Tenant-ID inyectado |
| #2 | Disparar 1 mensaje real Telegram a chalreme → `sales_agent_trace_event` recibe ≥3 rows (turn_start + tool_call + turn_end) en <5s |
| #4 | `/sales/campanas/nuevo` carga wizard (no 404), sidebar muestra link "Campañas" navegable |
| #5 | 0 ocurrencias de "Maximum update depth" en consola durante 15min de navegación |

## Walking skeleton

Mínimo entrega:
1. FE `use-contacts-query.ts:26` add `/`
2. FE rename `campañas/` → `campanas/` + sidebar entry add
3. BE sales_agent observability fix (handler persists rows real)
4. Smoke test sales_agent observability (asserts INSERT)
5. Re-test full TC1-TC12 chrome-devtools

NO bundling de features nuevos. Solo bug fixes.

## Soluciones consideradas

### Bug #1 — slash convention

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A) FE add `/` antes de `?` | Match BE convention 10+ módulos. 1 char. Cero risk regression | — | **ELEGIDA** |
| B) BE cambiar `@router.get("/")` → `""` | Match minoría 4 módulos. Cambia OpenAPI path | Inconsistencia mayor con resto | descartada |
| C) Habilitar `redirect_slashes=True` | Fix global redirect | Rompe POST Next.js (regla CLAUDE.md prohíbe — origen 5 deploys fallidos 2026-04-27) | descartada — viola rule |

### Bug #2 — observability fix approach

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A) Deep RCA con `nicolify-agentic` skill `sales-agent-expert` | Fix root cause real, sin parche. Smoke test asserting INSERT | Tiempo investigación 30-60min | **ELEGIDA** |
| B) Quick try/except fix | Rápido | No address root cause. Chris explícito "no parches" | descartada |

### Bug #4 — folder rename vs Next.js workaround

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A) Rename `campañas`→`campanas` | Aligns con `growth-studio/campanas` existente. Webpack-safe. Cero next.config change | — | **ELEGIDA** |
| B) Custom Next.js loader/encoder | Generalizable | Over-engineering. Riesgo regresión otros routes | descartada |
| C) Forzar compile via dynamic route export | Hack | No fix Webpack underlying | descartada |

## Validación técnica preliminar

- Modules afectados: `frontend/src/features/crm-hub/`, `frontend/src/features/campaigns-lite/`, `frontend/src/app/(main)/.../sales/campañas/`, `frontend/src/components/shared/layout/AppSidebar.tsx`, `backend/src/modules/sales_agent/observability/recording/`, `backend/src/modules/sales_agent/application/orchestrator/`
- Blockers conocidos: ninguno
- Tiempo estimado: 1-2h dos builders en paralelo
- Alternativas técnicas: ver Soluciones consideradas

## Existing systems audit

- **#1**: convention `@router.get("/")` ya 10+ módulos. EXTEND alineando FE. NO new layer.
- **#2**: recording infra ya existe completa. EXTEND fix logic gap. NO new layer.
- **#4**: folder convention `campanas` ASCII ya en `growth-studio/`. EXTEND alignment. NO new convention.

## Decisiones diferidas

- Backfill traces sales_agent para conversaciones pre-fix (descartar VS retro-generar) — discusión Chris post-PR-1 ship.
- UX mejora Streamlit admin (Bug #3) — defer PI-3 sales-agent-improvement.
- Audit otros FE files trailing slash inconsistency (analytics? assets? brand?) — defer si grep no devuelve más violaciones reales (verificación incluida en este PR).

## Out of scope

- Nuevas features. Solo bug fixes.
- Reabrir PI-1 a active state (queda archivado, este PR vive en PI-1.1-post-mortem dedicado).
- Cambiar `redirect_slashes` global (sigue `False`, rule inviolable).

## Copilot-first checklist

- [x] Operable copilot? **NO** — esto es hotfix técnico, no feature user-facing operable. Chris ejecuta manualmente test post-fix.
- [x] Tools nuevos: ninguno.
- [x] Cards/UI nueva: ninguna (sidebar entry es navigation, no card).
- [x] Razón NO copilot: hotfix invisible al user. Capabilities ya existían (PI-1), solo se desbloquen al user.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Pre-design | (skip) — no nueva contract | — | — |
| UX | (skip) — no nueva UI | — | — |
| Implementation FE | `nicolify-frontend` (Sonnet) + `frontend-expert` skill | `prompts/02-builder-frontend.md` | code + tests + `IMPL-LOG-fe.md` |
| Implementation Agentic | `nicolify-agentic` (Opus) + `sales-agent-expert` skill | `prompts/02-builder-agentic.md` | code + tests + `IMPL-LOG-agentic.md` |
| Audit FE | `nicolify-frontend-auditor` (Opus, auto-spawn) | (builder dispara) | `REVIEW-frontend.md` |
| Audit Agentic | `nicolify-agentic-auditor` (Opus, auto-spawn) | (builder dispara) | `REVIEW-agentic.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + retro PI-1 update |

**Paralelismo:** FE y Agentic surfaces no se tocan (regla M1). Spawn ambos en paralelo. Tests/Docker secuencial (M3) — cada builder corre sus gates en momentos distintos.

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| FE archivo | `frontend/src/features/crm-hub/api/use-contacts-query.ts` | edit línea 26 (add `/`) |
| FE folder | `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/` | rename a `campanas/` |
| FE archivo | `frontend/src/components/shared/layout/AppSidebar.tsx` | add sidebar entry "Campañas" |
| FE refs | `frontend/src/features/campaigns-lite/**` | grep + replace `campañas` → `campanas` en hrefs/imports si aplica |
| BE archivos | `backend/src/modules/sales_agent/observability/recording/{factory,callback_handler}.py` | fix root cause (TBD — investigation) |
| BE archivos | `backend/src/modules/sales_agent/application/orchestrator/{chat,outbound_orchestrator}.py` | possible scope fix |
| Tests BE | `backend/tests/modules/sales_agent/observability/test_real_trace_persistence.py` | nuevo smoke con real DB INSERT assertion |
| current-state | `docs/pm-nico/current-state/sales_agent.md` | append nota observability fixed |
| current-state | `docs/pm-nico/current-state/campaigns.md` | append nota CRM contacts route fixed |

## Tests requeridos (TDD)

### FE
- Re-run `frontend/src/features/crm-hub/__tests__/` — ya hay tests, deben seguir verdes
- Add unit test: `use-contacts-query.test.ts` — assert URL incluye `/api/v1/contacts/?` (con slash)
- Add E2E smoke: `e2e/specs/smoke/sales-campaigns-route.spec.ts` — asserts `/sales/campanas/nuevo` carga sin 404

### BE
- New: `backend/tests/modules/sales_agent/observability/test_real_trace_persistence.py`
  - Setup: real AsyncSession + real lead + real tenant
  - Act: simulate turn execution con `build_sales_agent_callback_handler`
  - Assert: `sales_agent_trace_event` rows ≥1 con `event_type='turn_start'`
  - NO mocks de DB session. Real persistence test.

## Aceptación

- [ ] FE tests verdes (vitest + playwright smoke)
- [ ] BE tests verdes (pytest)
- [ ] Lint/type check verdes (FE: tsc + eslint, BE: ruff + mypy)
- [ ] `IMPL-LOG-fe.md` + `IMPL-LOG-agentic.md` completos
- [ ] `REVIEW-frontend.md` + `REVIEW-agentic.md` verdict PASS
- [ ] Re-test chrome-devtools TC1-TC12 verdict PASS
- [ ] Real Telegram message a chalreme → trace rows en DB
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/sales_agent.md` + `current-state/campaigns.md` updated
- [ ] Retro PI-1 append section "Post-mortem 2026-04-30 + bugs encontrados + fixes"

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Bug #2 RCA toma >2h sin solución clara | Builder agentic escalate PM tras 1h con findings parciales; PM decide A) defer fix B) backfill skip C) workaround temporal con flag |
| Folder rename rompe imports inesperados | grep recursivo `campañas` antes commit. Test FE compila + tsc passes |
| Real Telegram test envía mensaje no deseado a chalreme | Chris autorizó. Mensaje es template `welcome` — único y descartable |
| Otros FE files con misma slash inconsistency aparecen post-fix | Grep included en builder prompt. Fix all-at-once |
