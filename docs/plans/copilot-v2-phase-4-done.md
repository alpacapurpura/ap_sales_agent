# Copilot v2 — Phase 4 Done: Observabilidad + Feedback Loop

**Completado:** 2026-03-25
**Verificacion:** ruff clean, tsc clean, 309 tests PASS, migration applied, import smoke OK
**Dependencias:** Phase 1 (Schema-Driven Foundation), Phase 2 (Procedures + Nudges), Phase 3 (Rich Intelligence) — todas completadas

---

## Resumen Ejecutivo

Phase 4 cierra el ciclo del Copilot v2: todo lo que el usuario hace dentro del copilot ahora se registra, se analiza y se usa para personalizar la experiencia. El sistema ahora puede:

1. **Registrar** 12 tipos de eventos (9 frontend, 1 backend, 2 hibridos)
2. **Analizar** patrones de uso por usuario y por tenant (friction map, engagement, procedure rates)
3. **Personalizar** las respuestas del LLM usando el historial de comportamiento del usuario
4. **Visualizar** insights accionables en un dashboard admin con 5 tabs
5. **Limpiar** datos antiguos automaticamente via ARQ cron job (soft delete >90 dias)

---

## Arquitectura Post-Phase 4

### Archivos Nuevos (6)

| Archivo | Sub-fase | Proposito |
|---------|----------|-----------|
| `backend/alembic/versions/c3d4e5f6a7b8_create_copilot_events.py` | 4.1 | Migracion idempotente: tabla + 3 partial indexes |
| `backend/src/modules/copilot/infrastructure/models/event_model.py` | 4.1 | SQLAlchemy model con soft delete (`deleted_at`) |
| `backend/src/modules/copilot/infrastructure/repositories/event_repository.py` | 4.1 | 9 metodos: record, summaries, friction, engagement, procedures, soft_delete |
| `backend/src/modules/copilot/api/events.py` | 4.2a | REST: POST /record (201), GET /summary, GET /insights |
| `backend/src/admin/modules/events.py` | 4.4 | Streamlit 5-tab dashboard de eventos |
| `backend/src/modules/copilot/application/services/event_cleanup.py` | 4.5 | ARQ task: soft-delete eventos >90 dias |

### Archivos Modificados (18)

| Archivo | Sub-fase | Cambio |
|---------|----------|--------|
| `backend/.../orchestrator/chat.py` | 4.0 | Fix: `tool_call_id=""` → tracked via `last_tool_call_ids` map |
| `backend/src/shared/infrastructure/model_registry.py` | 4.1 | +CopilotEventModel import |
| `backend/src/main.py` | 4.2a | +events router `/api/v1/copilot/events` |
| `backend/src/core/context.py` | 4.2d | +`_user_id_ctx` ContextVar + get/set |
| `backend/.../api/chat.py` | 4.2d | +`set_user_id(current_user.id)` |
| `backend/.../tools/knowledge_tools.py` | 4.2d | +`_track_knowledge_search()` server-side (best-effort) |
| `backend/.../orchestrator/graph.py` | 4.3 | +`_get_behavior_summary()` → Spanish markdown, inyectado al prompt |
| `backend/.../prompts/templates/copilot_system.j2` | 4.3 | +`{% if behavior_summary %}` block con instrucciones de personalizacion |
| `backend/src/admin/app.py` | 4.4 | +nav entry "Copilot Events" + routing |
| `backend/src/modules/analytics/workers/settings.py` | 4.5 | +cleanup_old_events en functions + cron 3:30am UTC |
| `frontend/.../api/copilot-api.ts` | 4.2b | +`getCopilotHeaders()`, +`reportCopilotEvent()`, refactor headers |
| `frontend/.../hooks/useProactiveNudges.ts` | 4.2b | Refactored → usa `getCopilotHeaders()` (elimina 3ra duplicacion) |
| `frontend/.../messages/ProposalCard.tsx` | 4.2c | +proposal_accepted, +proposal_rejected |
| `frontend/.../messages/NavigationCard.tsx` | 4.2c | +navigation_clicked |
| `frontend/.../components/NudgeBanner.tsx` | 4.2c | +nudge_clicked, +nudge_dismissed |
| `frontend/.../messages/MultiOptionSelector.tsx` | 4.2c | +option_selected |
| `frontend/.../messages/ProgressChecklist.tsx` | 4.2c | +checklist_item_clicked |
| `frontend/.../components/CopilotRail.tsx` | 4.2c | +copilot_opened |
| `frontend/.../hooks/useCopilotChat.ts` | 4.2c | +message_sent |
| `frontend/.../components/SuggestedActions.tsx` | 4.2c | +suggested_action_clicked |
| `frontend/.../components/CopilotChat.tsx` | 4.2c | +procedure_abandoned (useEffect on panel close) |

---

## Catalogo de Eventos (12)

| # | Evento | Fuente | Trigger | event_data |
|---|--------|--------|---------|------------|
| 1 | `proposal_accepted` | Frontend | ProposalCard "Aplicar" | `{field_count, field_ids}` |
| 2 | `proposal_rejected` | Frontend | ProposalCard "Rechazar" | `{field_count, field_ids}` |
| 3 | `nudge_clicked` | Frontend | NudgeBanner action | `{nudge_id, nudge_type, nudge_title}` |
| 4 | `nudge_dismissed` | Frontend | NudgeBanner dismiss | `{nudge_id, nudge_type}` |
| 5 | `option_selected` | Frontend | MultiOptionSelector "Aplicar" | `{field_id, selected_option_id, selected_title}` |
| 6 | `navigation_clicked` | Frontend | NavigationCard click | `{route, page_label, section_id}` |
| 7 | `checklist_item_clicked` | Frontend | ProgressChecklist navigate | `{label, route}` |
| 8 | `knowledge_searched` | Backend | knowledge_tools.py (server-side) | `{query, scope, results_count}` |
| 9 | `copilot_opened` | Frontend | CopilotRail click | `{}` (route auto-extracted) |
| 10 | `message_sent` | Frontend | useCopilotChat.sendMessage | `{message_length, has_selected_fields, is_first_message}` |
| 11 | `procedure_abandoned` | Frontend | Panel close con procedimiento activo incompleto | `{procedure_id, procedure_name, abandoned_at_step, total_steps}` |
| 12 | `suggested_action_clicked` | Frontend | SuggestedActions chip click | `{action_label}` |

---

## Contratos API

### Events Endpoints

```
POST /api/v1/copilot/events/record
  Body: { event_type: str, event_data: dict, conversation_id?: str, route?: str }
  Response: 201 { recorded: true }

GET /api/v1/copilot/events/summary?days=30
  Response: { events: {type: count}, period_days: int, tenant_id: str }

GET /api/v1/copilot/events/insights?days=30
  Response: {
    friction_map: {route: count},
    engagement: {messages_per_user_avg, active_users, total_messages, suggested_vs_typed},
    procedure_rates: {proc_id: {name, started, completed, abandoned, avg_abandoned_step}},
    period_days: int,
    tenant_id: str
  }
```

### DB Schema

```sql
copilot_events (
  id UUID PK DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  conversation_id UUID,
  event_type VARCHAR(50) NOT NULL,
  event_data JSONB DEFAULT '{}',
  route VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
)

-- Partial indexes (exclude soft-deleted)
idx_copilot_events_tenant_created (tenant_id, created_at DESC)
idx_copilot_events_tenant_type (tenant_id, event_type)
idx_copilot_events_tenant_user_created (tenant_id, user_id, created_at DESC)
```

---

## Feedback Loop: Como funciona

1. **Usuario interactua** → evento se registra via `reportCopilotEvent()` (fire-and-forget) o server-side (knowledge_searched)
2. **Siguiente mensaje** → `graph.py:_get_behavior_summary()` consulta eventos de los ultimos 30 dias
3. **System prompt enriquecido** → `copilot_system.j2` incluye bloque "Historial de Interaccion del Usuario" con metricas en espanol
4. **LLM personaliza** → si acepta muchas propuestas → mas proactivo; si rechaza → pregunta antes; si usa navegacion → ofrece links directos
5. **Admin revisa** → dashboard Streamlit con friction map, procedure rates, engagement KPIs

### Ejemplo de behavior_summary inyectado

```
## Historial de Interaccion del Usuario
- Propuestas: acepta 80% (12 aceptadas, 3 rechazadas)
- Nudges: 8 aceptados, 2 descartados
- Navegaciones realizadas: 18
- Mensajes enviados: 47 (usuario muy activo)
- Aperturas del copilot: 23
- Busquedas en knowledge base: 7 (scope preferido: business)
- Procedimiento 'Offer Creation': abandonado 2/3 veces en paso ~3
```

---

## Hallazgos durante la implementacion

### 1. Header duplication eliminada (3 lugares → 1)

`getCopilotHeaders(token)` ahora es la unica fuente de verdad para construir headers con tenant ID. Antes estaba duplicado en:
- `streamCopilotChat()` (copilot-api.ts)
- `useProactiveNudges()` (useProactiveNudges.ts)
- (Ahora tambien usado por) `reportCopilotEvent()`

### 2. procedure_abandoned requirio useEffect con ref

No se puede usar hooks dentro de Zustand store. La deteccion de abandono se implemento como `useEffect` en `CopilotChat.tsx` que observa la transicion `isOpen: true→false` via `prevOpenRef`. Esto es limpio y no agrega complejidad al store.

### 3. knowledge_searched es server-side (no frontend)

La busqueda de knowledge base ocurre dentro de un tool call del LLM. No hay trigger directo del frontend para este evento. Se implemento server-side en `knowledge_tools.py` usando `get_user_id()` del ContextVar (que se setea en `chat.py` endpoint). Best-effort con try/except.

### 4. user_id ContextVar era necesario

El ContextVar de `user_id` no existia antes de Phase 4. Se agrego a `context.py` siguiendo el patron exacto de `tenant_id`. Es necesario para que los tools de backend puedan registrar eventos sin recibir `user_id` como parametro.

---

## Recapitulacion: Las 4 Fases del Copilot v2

| Fase | Nombre | Que agrego |
|------|--------|-----------|
| **Phase 1** | Schema-Driven Foundation | MODULE_REGISTRY, schema introspection, 13 tools con seleccion por ruta, system prompt dinamico, conversation persistence |
| **Phase 2** | Procedures + Nudges | Guided procedures (brand_setup, offer_creation, first_setup), proactive nudges por ruta, ProcedureProgress stepper |
| **Phase 3** | Rich Intelligence | UI generativa (4 componentes), RAG knowledge base (Qdrant), conversation memory (tool_calls roundtrip), admin knowledge dashboard |
| **Phase 4** | Observabilidad + Feedback Loop | 12 eventos, behavioral analytics, feedback-informed prompting, admin events dashboard, event retention cron |

### Capacidades acumuladas del Copilot v2

El copilot ahora es un sistema **completo** con:

- **Descubrimiento dinamico** de modulos, campos y secciones (sin hardcodear)
- **Seleccion inteligente de tools** basada en la ruta del usuario
- **Mutaciones** propuestas antes de ejecutarse (proposal → accept/reject)
- **Procedimientos guiados** paso a paso con stepper visual
- **Nudges proactivos** que sugieren acciones contextuales
- **UI generativa** (metricas, tablas comparativas, checklists, selectores)
- **Knowledge base RAG** con documentos del negocio y de la plataforma
- **Memoria de conversacion** con replay completo de tool calls
- **Tracking de comportamiento** con 12 tipos de eventos
- **Personalizacion** del LLM basada en patrones de uso del usuario
- **Dashboard admin** para encontrar mejoras accionables (friction points, procedure abandonment)
- **Retention automatica** de datos (soft delete >90 dias)

---

## Recomendaciones para Copilot v3 (Segunda Etapa)

Considerando que las 4 fases estan completas y el copilot tiene una base solida, estas son las areas de mayor impacto para una segunda etapa:

### 1. Satisfaction Signal: Thumbs Up/Down en Mensajes (ALTO IMPACTO)

**Problema:** Los 12 eventos actuales miden interaccion, pero no satisfaccion. No sabemos si las respuestas del copilot son utiles.

**Propuesta:**
- Agregar iconos thumbs-up/down debajo de cada `AssistantMessage`
- Eventos: `response_rated` con `{rating: "positive"|"negative", message_id, had_tool_calls}`
- Almacenar en `copilot_events` + agregar al behavior_summary
- Admin: tasa de satisfaccion por tipo de consulta, por ruta, por tool usado
- **Esto es lo mas valioso que falta** — sin feedback explicito del usuario, solo tenemos proxy signals

### 2. Session Analytics: Duración y Profundidad (ALTO IMPACTO)

**Problema:** Sabemos cuantos mensajes envia un usuario, pero no cuanto tiempo interactua ni que tan profundas son las sesiones.

**Propuesta:**
- Evento `copilot_closed` con `{session_duration_ms, messages_count, tools_triggered}`
- Calcular tiempo entre `copilot_opened` y `copilot_closed` (o panel close)
- Admin: duracion promedio de sesion, correlacion con satisfaccion
- Dato clave: sesiones cortas con rechazo = copilot no entendio; sesiones largas con aceptacion = copilot es util

### 3. A/B Testing de System Prompts (ALTO IMPACTO)

**Problema:** El system prompt se itero manualmente. No hay forma de medir si un cambio mejora o empeora la experiencia.

**Propuesta:**
- Aprovechar que `PromptLoader` ya soporta DB + versiones
- Asignar variantes de prompt por tenant o por porcentaje de usuarios
- Correlacionar variante con satisfaction rate y proposal acceptance rate
- Esto convierte al copilot en un sistema auto-optimizable

### 4. Proactive Insights: El Copilot que te busca (MEDIO IMPACTO)

**Problema:** El copilot es reactivo — espera a que el usuario lo abra. Los nudges son semi-proactivos (aparecen cuando abres el panel).

**Propuesta:**
- Push notifications dentro de la app (no solo nudge banners)
- "Tu agente de ventas ha cerrado 3 ventas hoy — quieres ver el resumen?"
- "Tu Brand Studio lleva 7 dias sin cambios y tiene 40% incompleto"
- Trigger: cron job que evalua condiciones + notificacion via WebSocket o badge

### 5. Multi-Turn Tool Chains (MEDIO IMPACTO)

**Problema:** El copilot hace un tool call a la vez. Para tareas complejas, el usuario tiene que guiarlo paso a paso.

**Propuesta:**
- Permitir que el LLM planifique multiples tool calls secuenciales ("primero leo brand, luego offer, luego propongo cambios")
- Requiere agregar un nodo `planner` al grafo LangGraph antes del `agent`
- Tracking: `plan_executed` con `{steps_count, tools_used, success}`

### 6. Export de Datos y Reportes (MEDIO IMPACTO)

**Problema:** El admin dashboard es util para exploracion pero no para reportes periodicos.

**Propuesta:**
- Endpoint `GET /api/v1/copilot/events/export?format=csv&days=30`
- Reporte semanal automatico por email: "Tu copilot esta semana: X mensajes, Y propuestas aceptadas, Z puntos de friccion"
- Integrable con el modulo de analytics existente

### 7. Conversation Summarization (BAJO IMPACTO AHORA, ALTO A ESCALA)

**Problema:** El campo `summary` en `copilot_conversations` esta siempre NULL. No se usa.

**Propuesta:**
- Al cerrar una conversacion (o despues de N mensajes), generar un summary con LLM
- Usar summaries para: busqueda de conversaciones pasadas, contexto cross-session, reporte admin
- Ya existe la columna — solo falta el trigger

### 8. Impression Tracking para UI Generativa (BAJO IMPACTO)

**Problema:** Sabemos cuando el usuario interactua con MetricSummaryCard o ComparisonTable, pero no cuando los *ve*. Si el LLM genera una tabla comparativa y el usuario la ignora, no lo detectamos.

**Propuesta:**
- `IntersectionObserver` en componentes de UI generativa
- Eventos: `metric_card_viewed`, `comparison_table_viewed`
- Ayuda a medir: "el LLM genera mucha UI que nadie mira?"

### 9. Error Tracking Granular (BAJO IMPACTO)

**Problema:** Si un tool call falla, el error queda en el log del servidor pero no en el sistema de eventos.

**Propuesta:**
- Evento `tool_error` con `{tool_name, error_message, input_args}`
- Admin: tab "Errores" con frecuencia por tool, para detectar tools rotos
- Ya existe logging en `graph.py:tool_executor_node` — solo falta persistir

### 10. Integracion con Sales Agent Telemetria (BAJO IMPACTO, ALTA SINERGIA)

**Problema:** El copilot y el sales_agent tienen sus propios sistemas de tracking desconectados.

**Propuesta:**
- Tabla unificada de eventos o al menos una vista SQL que cruce `copilot_events` con `agent_traces`
- Dashboard que muestre: "usuario configuro X en copilot → sales_agent uso X en conversacion → lead convirtio"
- Esto prueba el ROI del copilot: configuracion → impacto en ventas

---

## Priorizacion Recomendada para v3

| Prioridad | Item | Esfuerzo | Razon |
|-----------|------|----------|-------|
| P0 | Thumbs up/down (satisfaction signal) | 1 dia | Sin esto, las metricas actuales son proxy signals. Feedback explicito > todo lo demas |
| P0 | Session analytics | 0.5 dias | Dato basico que falta para entender engagement real |
| P1 | A/B testing de prompts | 2-3 dias | Convierte al copilot en auto-optimizable. Infraestructura de PromptLoader ya existe |
| P1 | Proactive insights (push) | 2 dias | Diferenciador: copilot que te busca, no al reves |
| P2 | Multi-turn tool chains | 3 dias | Mejora percepcion de inteligencia, pero requiere cambios al grafo |
| P2 | Export/reportes | 1 dia | Quick win para clientes enterprise |
| P3 | Conversation summarization | 1 dia | Valor futuro cuando haya muchas conversaciones |
| P3 | Impression tracking | 0.5 dias | Nice-to-have, no critico |
| P3 | Error tracking granular | 0.5 dias | Nice-to-have, complementa observabilidad |
| P3 | Integracion Sales Agent | 3 dias | Alto valor estrategico pero depende de madurez del sales_agent |

---

## Verificacion Funcional Checklist

| # | Verificacion | Estado |
|---|-------------|--------|
| 1 | `POST /api/v1/copilot/events/record` → 201 | Implementado |
| 2 | `GET /api/v1/copilot/events/summary` → aggregation correcta | Implementado |
| 3 | `GET /api/v1/copilot/events/insights` → friction + engagement + procedures | Implementado |
| 4 | Abrir copilot → `copilot_opened` en DB | Instrumentado |
| 5 | Enviar mensaje → `message_sent` en DB | Instrumentado |
| 6 | Click suggested action → `suggested_action_clicked` | Instrumentado |
| 7 | ProposalCard apply/reject → `proposal_accepted`/`rejected` | Instrumentado |
| 8 | NudgeBanner click/dismiss → `nudge_clicked`/`dismissed` | Instrumentado |
| 9 | NavigationCard click → `navigation_clicked` | Instrumentado |
| 10 | ProgressChecklist navigate → `checklist_item_clicked` | Instrumentado |
| 11 | MultiOptionSelector apply → `option_selected` | Instrumentado |
| 12 | Cerrar copilot mid-procedure → `procedure_abandoned` | Instrumentado |
| 13 | Knowledge search via chat → `knowledge_searched` (server-side) | Instrumentado |
| 14 | 5+ eventos + nuevo mensaje → system prompt incluye "Historial de Interaccion" | Implementado |
| 15 | 0 eventos → system prompt NO incluye bloque de behavior | Implementado |
| 16 | Streamlit admin → Events tab con 5 sub-tabs | Implementado |
| 17 | ARQ cron → cleanup_old_events a las 3:30am UTC diario | Configurado |
| 18 | Migration idempotente con partial indexes | Verificado |
| 19 | ruff clean | PASS |
| 20 | tsc clean | PASS |
| 21 | pytest 309 PASS | PASS |
