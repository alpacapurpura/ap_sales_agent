# Sales Agent — Codebase Audit Map (S00 Snapshot)

> **Generated 2026-04-28 in S00 (codebase audit + cleanup deprecated).**
>
> Source-of-truth para que S0..S10 no rompan callers. Re-leerlo en Paso 1 de cada fase. Si la realidad diverge → flag y actualizar acá.

---

## §1 · FE → BE endpoint callers

### `/api/v1/closer-studio/*` (router: `backend/src/modules/sales_agent/api/closer_studio.py`, 285 LOC)

Único feature FE consumer: `frontend/src/features/closer-studio/`.

| Endpoint | Method | FE caller (api/) | FE hook | Página |
|---|---|---|---|---|
| `/conversations` | GET | `fetchConversations()` | `use-conversations.ts` | `/sales/studio/inbox`, `/sales/studio/pipeline` |
| `/conversations/{lead_id}` | GET | `fetchConversationDetail()` | conversation panel | inbox detail |
| `/conversations/{lead_id}/stop` | POST | `stopAI()` | `use-conversation-actions.ts` | inbox |
| `/conversations/{lead_id}/resume` | POST | `resumeAI()` | `use-conversation-actions.ts` | inbox |
| `/conversations/{lead_id}/messages` | POST | `sendMessage()` | composer | inbox |
| `/conversations/{lead_id}/nudge` | POST | `nudge()` | inbox actions | inbox |
| `/conversations/{lead_id}/reactivate` | POST | `reactivate()` | frozen actions | `/sales/studio/frozen` |
| `/conversations/{lead_id}/diagnose` | POST | `diagnose()` | frozen actions | frozen |
| `/frozen` | GET | `fetchFrozen()` | `use-frozen.ts` | frozen |
| `/kpis` | GET | `fetchKPIs()` | `use-kpis.ts` | inbox header |

WS: `/ws/closer-studio?tenant_id=…` (`backend/.../api/ws.py`, 43 LOC) consumido por `use-closer-ws.ts`. Eventos: `new_message`, `handler_changed`, `conversation_updated` vía `ws_manager`.

### `/api/v1/sales-agent/enrollments/*` (router: `enrollments.py`, 221 LOC)

Consumer FE: `frontend/src/features/closer-studio/api/enrollments-api.ts`.

| Endpoint | Method | FE caller |
|---|---|---|
| `/enrollments` | POST | `enrollmentsApi.create()` |
| `/enrollments` | GET | `enrollmentsApi.list()` |
| `/enrollments/waitlist` | GET | `enrollmentsApi.listWaitlist()` |
| `/enrollments/by-conversation/{conversation_id}` | GET | `enrollmentsApi.getByConversation()` |
| `/enrollments/{id}` | GET | (consumido vía list/detail) |
| `/enrollments/{id}/status` | PATCH | (sin caller FE — sólo admin/scripts) |
| `/enrollments/{id}/mark-paid` | POST | `enrollmentsApi.markPaid()` |
| `/enrollments/promote-waitlist` | POST | `enrollmentsApi.promoteWaitlist()` |

Página: `/sales/enrollments`.

### `/api/v1/sales/leads/*` (router: `audit.py`, 229 LOC)

**Consumer único: Streamlit admin** (`backend/src/admin/modules/sales_audit.py`). NO FE consumer.

| Endpoint | Método | Uso admin |
|---|---|---|
| `/leads` | GET | dropdown leads recientes |
| `/leads/{lead_id}` | GET | header del audit page |
| `/leads/{lead_id}/timeline` | GET | timeline de trazas |
| `/leads/{lead_id}/llm-logs` | GET | LLM log summary |
| `/leads/{lead_id}/clear-history` | POST | "🗑️ Limpiar Conversación" |

> **Nota S1**: `audit.py` lee via `AuditRepository` que mezcla `MessageModel` + `AgentTrace` legacy + `LLMLogModel`. Migración paralela post-S1: replicar timeline desde `sales_agent_trace_event` + `sales_agent_llm_call` tipados.

### Rutas FE deprecated (a borrar en S00)

| Ruta | Componente | Acción |
|---|---|---|
| `/sales` (`app/.../sales/page.tsx`) | redirige a `/sales/resumen` | **fix redirect → `/sales/studio/inbox`** |
| `/sales/resumen` (`app/.../sales/resumen/page.tsx`) | `SalesDashboard` | **borrar carpeta** |

### Rutas FE activas (NO TOCAR)

- `/sales/studio/inbox`
- `/sales/studio/pipeline`
- `/sales/studio/frozen`
- `/sales/contactos`
- `/sales/enrollments`
- `/sales/mock` (live; consume `SalesMockView` de `features/sales/`)

---

## §2 · Backend cross-module imports

### Inbound (otros módulos importan sales_agent)

| Caller | Símbolo importado | Razón | Status |
|---|---|---|---|
| `backend/src/modules/connections/api/dependencies/__init__.py` | `ChatOrchestrator` (`sales_agent.application.orchestrator.chat`) | Webhook handlers Telegram/WhatsApp/IG inyectan orchestrator | ALLOWED (dependency injection wiring; not domain bleed) |
| `backend/src/main.py` | routers `audit`, `closer_studio`, `enrollments`, `ws` | mount FastAPI | ALLOWED |
| `backend/src/workers/settings.py` | `run_frozen_detection`, `run_follow_up_engine` | ARQ scheduler | ALLOWED |
| `backend/src/admin/modules/sales_audit.py` | `AuditRepository`, `AgentTrace` | admin UI | ALLOWED — pero acopla admin a tabla legacy (DEFERRED-S1) |

### Outbound (sales_agent lee otros módulos)

| Sales_agent file | Imports de | Vía | Status |
|---|---|---|---|
| `application/orchestrator/chat.py` | `iam.TenantModel`, `iam.api.dependencies.get_current_user/User` | direct | ALLOWED (tenant context + auth) |
| `application/orchestrator/chat.py` | `crm.LeadModel`, `IdentityService`, `LeadRepository` | port `shared/links/ports/crm_repos.py` | ALLOWED (port-based) |
| `application/services/style_anchor_retriever.py` | `brand.infrastructure.qdrant.StyleAnchorStore` | lazy import (TYPE_CHECKING + runtime) | ALLOWED (lazy) — DEFERRED-S0 si extract necesita port |
| `application/services/business_repository.py` | `offer.infrastructure.models.ProductModel` | lazy import | ALLOWED (lazy) — DEFERRED-S0 si extract necesita port |
| `application/services/knowledge_builder.py` | brand + offer dyn-loaded | lazy via factory | ALLOWED — alta coupling (ver §8) |

**Regla activa hoy:** `tests/architecture/test_no_new_cross_module_imports.py` con allowlist congelada. Cualquier import nuevo no allowlistado falla.

**Sin violaciones nuevas detectadas en S00.** Pero el `lazy import brand/offer` está al borde — S0 evaluará si necesita formalizar ports.

---

## §3 · DB tables touched by sales_agent

### Owned (sales_agent escribe)

| Modelo | File (`infrastructure/models/`) | Writer principal | Reader cross-module | LOC |
|---|---|---|---|---|
| `AgentStateCheckpoint` | `agent_state_checkpoint_model.py` | `ChatOrchestrator`, `frozen_detection`, `follow_up_engine` | admin (audit) | 85 |
| `MessageModel` | `message_model.py` | `ChatOrchestrator`, channel resolvers | admin (audit) | 50 |
| `EnrollmentModel` | `enrollment_model.py` | `EnrollmentService` | — | 68 |
| `AgentTrace` (legacy) | `agent_trace_model.py` | `@trace_node` decorator | admin `sales_audit.py` | 30 |
| `LLMLogModel` (legacy) | `llm_log_model.py` | `LLMFactory.generate_response` | admin (audit timeline) | 25 |
| `SensitiveDataModel` | `sensitive_data_model.py` | sanitization pipeline | — | 20 |
| `PromptVersion` | `prompt_version_model.py` | tenant prompt overrides | knowledge builder | 15 |

### Read-only (sales_agent lee, no escribe)

- `iam.TenantModel` — tenant resolve
- `crm.LeadModel`, `crm.CustomerProfileModel` — identidad lead (vía port)
- `offer.ProductModel` — catálogo oferta (lazy)
- `brand.qdrant` colección — style anchors (lazy)

### Tablas globales reference data (cross-agent)

- `model_pricing_snapshot` — vía S0 shared (post-S0); hoy copilot-only.
- `tenant_billing_config` — idem.
- `mv_daily_llm_cost_per_tenant` — idem.

### Tablas a crear (S1)

- `sales_agent_llm_call`
- `sales_agent_trace_event`
- `sales_agent_routing_log`

### Tablas a dropear (S6, post cutover dual-write)

- `agent_trace_model` (`AgentTrace`)
- `agent_log_model` (`LLMLogModel`)

---

## §4 · Endpoints `/api/v1/sales*` con response_model audit

| Router | LOC | Response models tipados | Status |
|---|---|---|---|
| `closer_studio.py` | 285 | sí (todos los endpoints declaran) | OK |
| `enrollments.py` | 221 | sí | OK |
| `audit.py` | 229 | sí | OK |
| `ws.py` | 43 | N/A (WebSocket) | OK |

`tests/architecture/test_api_contracts.py` enforza `response_model=` en todos. Sin violaciones detectadas.

---

## §5 · Streamlit admin — sales tables reads

Único page: `backend/src/admin/modules/sales_audit.py` (slug `/sales-audit`).

Operaciones:

1. `repo.get_recent_users(tenant_id, limit=200)` — últimos leads.
   - Lee: `LeadModel` (CRM) join `MessageModel` + fallback `AgentTrace` para `last_activity`.
2. `_format_lead_option(lead_tuple)` — render dropdown.
   - Lee: `lead.profile_data`, `lead.key_objections_history` (CRM).
3. Timeline render — `AuditRepository.get_*_for_lead()`.
   - Lee: `MessageModel`, `AgentTrace`, `LLMLogModel`.
4. "Ver Último Estado" sidebar — query directo:
   ```python
   from src.modules.sales_agent.infrastructure.models.agent_trace_model import AgentTrace
   repo.db.query(AgentTrace).filter(AgentTrace.user_id == lead_id)...
   ```
   **Acopla admin a tabla legacy** — bloqueante de S1 cutover sin dual-read.
5. `repo.clear_user_history(lead_id, tenant_id)` — destructivo: borra mensajes + trazas + LLM logs + checkpoints.

**Migración path** ver `audit/admin-migration-plan.md`.

---

## §6 · Domain events

`application/event_bus.py` — in-memory single-process bus.

Producers detectados:

| Evento | Publisher | Trigger | Subscribers |
|---|---|---|---|
| `LeadCapturedEvent` (`shared/domain/events`) | `ChatOrchestrator.process_message` | primera interacción | (no encontrado en sales_agent — posible CRM consumer) |

**Riesgo:** event bus no persistente, sin async subscribers wiring claro. Eventos perdidos en restart. **DEFERRED-S1** ampliar inventario cuando observability event-sourced entre.

S1 agregará subscribers tipados:
- `EVENT_TURN_STARTED`
- `EVENT_TURN_ENDED`
- `EVENT_LEAD_QUALIFIED`
- `EVENT_OBJECTION_HANDLED`
- `EVENT_TOOL_LOOP_DETECTED`

---

## §7 · Workers ARQ

| Worker | File | Schedule | Reads | Writes | LOC | §3 protected? |
|---|---|---|---|---|---|---|
| `frozen_detection` | `workers/frozen_detection.py` | cada 4h | `AgentStateCheckpoint` + `MessageModel.last_activity` | `cp.frozen_at`, `cp.frozen_reason`, `cp.frozen_diagnosis` | 83 | sí (no tocar cadence) |
| `follow_up_engine` | `workers/follow_up_engine.py` | cada 1h | `AgentStateCheckpoint` activos | mensaje vía `channel_resolver`; `cp.follow_up_cadence` | 230 | sí (no tocar cadence math) |

Registrados en `backend/src/workers/settings.py`. Threshold frozen = 72h inactividad.

---

## §8 · Cohesion / coupling heatmap

> Ranking inicial — DEFERRED-S6 ratchet bumps allowlist + flagear refactors candidatos para fase posterior.

### Top 5 archivos con cohesión baja / coupling alto

1. **`application/orchestrator/chat.py` — 1082 LOC** ⚠⚠⚠
   - Mezcla: parsing entrada + state machine + event publish + identity resolve + buffer + output format + audit log.
   - 15+ deps cross-module (lazy o vía ports), pero el archivo es claro candidato Stranger Fig hacia: `ConversationPipeline`, `IdentityResolver`, `AuditEmitter`.
   - **Bloqueado por §3**: `BufferService.smart_debounce` y `OutputManager.process_response` no se tocan. Pero refactor del orchestrator sí es viable post-S6 sin tocarlas.

2. **`application/services/closer_studio_service.py` — 623 LOC** ⚠⚠
   - 8+ acciones (list/detail/stop/resume/send/nudge/reactivate/diagnose/kpis) en una clase.
   - Query SQL inline mezclada con lógica de dominio.
   - Refactor candidato post-S6: split por aggregate (`ConversationQueryService`, `ConversationCommandService`, `KpiService`).

3. **`infrastructure/external/output_manager.py` — 166 LOC** ⚠
   - Typing simulation + chunking + delay injection en una clase.
   - **§3 protegido** — no tocar process_response. S5 sí tocará el registry de canales adyacente sin invadir.

4. **`application/services/semantic_router.py` — 328 LOC** ⚠
   - Routes hardcoded + embeddings + tenant overrides en un archivo.
   - Refactor candidato — DEFERRED post-S6 (no bloqueante de redesign).

5. **`application/services/knowledge_builder.py` — 217 LOC** ⚠
   - Tenant context + offer + brand + style anchors (factory amplio).
   - Lazy imports cross-module concentrados acá. Si S0 formaliza ports brand/offer, este archivo se simplifica.

### Cohesión saludable (no requiere atención)

- `domain/` modelos pequeños y puros.
- `infrastructure/repositories/` repos por agregado (CRUD).
- `api/closer_studio.py` thin (endpoints delegando al service).
- Workers son monolíticos por diseño (cron handler patrón aceptado).

---

## §9 · Orphan code candidates (post-S00 cleanup)

Tras borrar `app/.../sales/resumen/page.tsx`:

| File | Status post-cleanup | Acción S00 |
|---|---|---|
| `frontend/src/features/sales/components/SalesDashboard.tsx` | **ORPHAN** (sólo lo importaba `resumen/page.tsx`) | Borrar (limpio) |
| `frontend/src/features/sales/components/dashboard/ConversionCommandCenter.tsx` | **ORPHAN** (sólo SalesDashboard lo usa) | Borrar |
| `frontend/src/features/sales/components/overlay/SalesInboxSheet.tsx` | **ORPHAN** (sólo SalesDashboard) | Borrar |
| `frontend/src/features/sales/components/dashboard/ActivityFeedWidget.tsx` | revisar consumers | dejar si vive en otro consumer |
| `frontend/src/features/sales/components/dashboard/CalendarWidget.tsx` | revisar consumers | dejar si vive en otro consumer |
| `frontend/src/features/sales/types/sales-studio.ts` | flagear `SalesDashboardState` interface | dejar archivo si otros tipos viven; remover tipo orphan |
| `frontend/src/features/sales/index.ts` | re-exporta SalesDashboard | actualizar barrel |
| `frontend/src/lib/design-system/registry-sales.ts` | catálogo registry, menciona los 3 componentes | actualizar registry |

### Live (no tocar)

- `features/sales/components/views/SalesMockView.tsx` (consumido por `/sales/mock`).
- `features/sales/components/EventTypeForm.tsx`, `AvailabilityView.tsx`, `EventTypeView.tsx`, `GenerateLinkModal.tsx` (scheduling settings).
- `features/sales/components/molecules/LeadCard.tsx`, `IdentityHeader.tsx`.
- `features/sales/components/atoms/*` (incluyendo `ScoreRing` consumido por closer-studio).
- `features/sales/types/lead.ts`, `mocks/leads.ts`.
- `features/sales/api/lead-service.ts`, `dashboard-service.ts`.

> **Decisión S00**: borrar los 3 orphans (SalesDashboard, ConversionCommandCenter, SalesInboxSheet) + actualizar barrel + registry. Tocar archivos a-borrar = scope estricto. ActivityFeedWidget/CalendarWidget se evalúan caso a caso vs consumers.

---

## §10 · §3 protected surface — verificación

Files mencionados en `00-vision-and-objectives.md §3` confirmados existentes:

| Path | Tipo | LOC |
|---|---|---|
| `backend/src/modules/sales_agent/api/closer_studio.py` | Router | 285 |
| `backend/src/modules/sales_agent/api/ws.py` | WS Router | 43 |
| `backend/src/modules/sales_agent/application/services/closer_studio_service.py` | Service | 623 |
| `backend/src/modules/sales_agent/infrastructure/external/buffer_service.py` (`smart_debounce` method) | Service | ~101 |
| `backend/src/modules/sales_agent/infrastructure/external/output_manager.py` (`process_response`) | Manager | 166 |
| `backend/src/modules/sales_agent/infrastructure/models/enrollment_model.py` + `domain/enrollment.py` + `application/services/enrollment_service.py` | Modelo + dominio + service | ~481 total |
| `backend/src/modules/sales_agent/infrastructure/models/agent_state_checkpoint_model.py` | SQLA Model | 85 |
| Webhook adapters | `connections/*` (módulo separado) | — |
| `backend/src/modules/sales_agent/workers/follow_up_engine.py` | Worker | 230 |

Todo presente. **S00 no toca ninguno.**

---

## Resumen ejecutivo

- **24 endpoints** sales activos (closer_studio + enrollments + audit + ws).
- **2 workers** ARQ (follow_up_engine, frozen_detection) con cadence frozen by §3.
- **7 modelos SQLA** owned (5 activos + 2 legacy a dropear).
- **0 violaciones cross-module** detectadas hoy (allowlist arch test).
- **3 archivos orphan FE** post-cleanup (SalesDashboard + 2 deps).
- **5 candidatos refactor** cohesión/coupling alto — todos DEFERRED post-S6.
- **§3 protected** verificada existente, sin tocar.

S0..S10 deben re-leer este doc en Paso 1 y actualizar §1-9 si la realidad diverge.
