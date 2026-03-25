# Copilot v2 — Phase 3 Handoff: Lo que se hizo, lo que se descubrio, y como abordar Phase 4

**Fecha:** 2026-03-25
**Contexto:** Phase 3 (Rich Intelligence) completada. Este documento sirve como posta para el agente que planifique y ejecute Phase 4 (Observabilidad + Feedback Loop).

---

## 1. Lo que se implemento en Phase 3

### Sub-Phase 3.1: UI Generativa (Frontend + Backend Tools)

**4 componentes nuevos creados:**

| Componente | Tipo UIAction | Trigger | Archivo |
|---|---|---|---|
| `MetricSummaryCard` | `metric_summary` | `get_funnel_metrics()` tool | `messages/MetricSummaryCard.tsx` |
| `ComparisonTable` | `comparison` | LLM genera directamente | `messages/ComparisonTable.tsx` |
| `ProgressChecklist` | `checklist` | `get_module_completion_status()` tool | `messages/ProgressChecklist.tsx` |
| `MultiOptionSelector` | `multi_option` | LLM genera directamente | `messages/MultiOptionSelector.tsx` |

**Modificaciones realizadas:**
- `copilot-store.ts`: UIAction union extendida con 4 tipos + 6 campos opcionales (`metrics`, `columns`, `rows`, `recommended`, `items`, `options`)
- `AssistantMessage.tsx`: Ternario reemplazado por switch-case que despacha al componente correcto segun `action.type`
- `analytics_tools.py`: Ahora retorna `json.dumps({"text": ..., "ui_action": {"type": "metric_summary", "metrics": [...]}})` con 5 metricas
- `awareness.py`: Ahora retorna `json.dumps({"text": ..., "ui_action": {"type": "checklist", "items": [...]}})` con modulos + routes

### Sub-Phase 3.2: RAG Knowledge Base

**5 archivos backend nuevos:**
- `infrastructure/knowledge/vector_store.py` — `CopilotKnowledgeStore`: coleccion `copilot_knowledge` (separada de sales_agent), hybrid search dense+sparse+reranking
- `application/services/knowledge_ingestion.py` — `KnowledgeIngestionService`: chunking 800/200, auto-resumen de Brand+Offer+Connections
- `application/tools/knowledge_tools.py` — `search_knowledge_base(query, scope)` tool, disponible en TODAS las rutas
- `api/knowledge.py` — REST: `POST /ingest`, `GET /search`, `DELETE /{document_id}`
- `infrastructure/knowledge/__init__.py`

**Modificaciones realizadas:**
- `registry.py`: grupo `"knowledge"` agregado a `TOOL_GROUPS` y a TODAS las rutas en `ROUTE_TOOL_MAP`
- `main.py`: router registrado en `/api/v1/copilot/knowledge`
- `copilot_system.j2`: seccion "Herramientas de Conocimiento" con instrucciones de scope

### Sub-Phase 3.3: Conversation Memory

**Modificaciones en `chat.py`:**
- `_serialize_messages()`: convierte cadena completa (HumanMessage + AIMessage con tool_calls + ToolMessage) a dicts persistibles
- `_deserialize_messages()`: reconstruye mensajes LangChain, backward compatible con formato antiguo
- Acumulacion durante streaming: `on_chat_model_end` captura AIMessages, `on_tool_end` captura ToolMessages
- Fix: eliminado `tool_output.replace("'", '"')` — ahora usa `json.loads()` directo

### Sub-Phase 3.4: Streamlit Admin

- `admin/modules/knowledge.py`: 5 tabs (Dashboard, Explorar, Buscar, Ingestar, Eliminar)
- `admin/app.py`: nav entry "Knowledge Base" agregada

---

## 2. Hallazgos y descubrimientos durante la implementacion

### Issue 1: tool_call_id vacio en ToolMessage fallback (MEDIO)

**Ubicacion:** `chat.py` linea ~135

**Problema:** Cuando `on_tool_end` retorna un string en vez de ToolMessage, se crea:
```python
ToolMessage(content=tool_output, name=tool_name, tool_call_id="")
```

**Impacto:** El `tool_call_id=""` rompe la cadena de mensajes durante replay porque no matchea con el `id` del tool_call original en el AIMessage. En la practica actual funciona porque los mensajes se serializan correctamente para persistencia, pero si Phase 4 necesita replay exacto de conversaciones (por ejemplo, para debugging o retraining), esto sera un problema.

**Recomendacion para Phase 4:** Antes de empezar, agregar logica para extraer el `tool_call_id` del contexto del evento, o mantener un mapping `tool_name -> last_tool_call_id` durante el streaming loop. Alternativamente, si el graph executor ya genera ToolMessages correctamente (ver `graph.py` lineas 215-227), este fallback quizas nunca se ejecute en la practica — verificar con un test manual.

### Issue 2: Convencion de nombres field_id vs fieldId (BAJO)

**Ubicacion:** UIAction interface usa `field_id` (snake_case), componentes React usan `fieldId` (camelCase).

**Estado:** Funciona correctamente porque `AssistantMessage.tsx` hace el mapping explicito: `fieldId={action.field_id}`. No necesita fix, pero documentar la convencion para que Phase 4 no introduzca inconsistencias al agregar event tracking.

### Issue 3: `on_chat_model_end` con tool_calls — RIESGO VERIFICADO OK

El plan original flageaba como riesgo que `astream_events v2` podria no incluir `tool_calls` en `on_chat_model_end`. **Verificado:** funciona correctamente. El AIMessage completo (incluyendo tool_calls) esta disponible en `event["data"]["output"]`.

### Descubrimiento positivo: El flujo SSE ya emite ui_action para Phase 4

El loop de streaming en `chat.py` (lineas 139-143) ya detecta `ui_action` en tool outputs y los emite como SSE events. Esto significa que Phase 4 NO necesita modificar el streaming para que los nuevos componentes reciban sus datos — ya funciona. Lo que SI necesita es agregar `reportCopilotEvent()` calls en cada componente frontend para trackear interacciones.

### Descubrimiento: analytics_tools y awareness ya NO retornan strings simples

**Cuidado para Phase 4:** Ambos tools ahora retornan `json.dumps({"text": ..., "ui_action": ...})`. Si Phase 4 agrega logica que parsea tool outputs (por ejemplo, para logging de eventos), debe manejar este formato JSON con ui_action, no asumir texto plano.

---

## 3. Estado actual de todos los componentes que Phase 4 necesita instrumentar

Phase 4 debe agregar `reportCopilotEvent()` a estos componentes. Aqui esta el mapa exacto:

| Componente | Eventos a trackear | Event Handler existente | Archivo |
|---|---|---|---|
| `ProposalCard` | `proposal_accepted`, `proposal_rejected` | `handleApply()`, `handleReject()` | `messages/ProposalCard.tsx` |
| `NavigationCard` | `navigation_clicked` | `onClick={() => executeAction(action)}` | `messages/NavigationCard.tsx` |
| `NudgeBanner` | `nudge_clicked`, `nudge_dismissed` | `onClick`, dismiss handler | `components/NudgeBanner.tsx` |
| `MultiOptionSelector` | `option_selected` | `handleApply()` | `messages/MultiOptionSelector.tsx` |
| `MetricSummaryCard` | (solo render, no interactivo) | — | `messages/MetricSummaryCard.tsx` |
| `ComparisonTable` | (solo render, no interactivo) | — | `messages/ComparisonTable.tsx` |
| `ProgressChecklist` | `navigation_clicked` (via enqueue) | `onClick` en items con route | `messages/ProgressChecklist.tsx` |
| `ProcedureProgress` | `procedure_started`, `procedure_completed` | Ya trackeado via tool calls | `components/ProcedureProgress.tsx` |

**Nota:** MetricSummaryCard y ComparisonTable son read-only (no tienen interacciones del usuario). No necesitan event tracking a menos que se quiera trackear "impresiones" (el usuario vio esta card).

---

## 4. Cosas que el plan original de Phase 4 NO contempla pero deberia

### 4.1 Evento `knowledge_searched`
Phase 3 agrego `search_knowledge_base` tool. Phase 4 deberia trackear:
- `knowledge_searched`: query, scope, results_count — para medir si el RAG esta siendo util
- Esto se puede hacer server-side en `knowledge_tools.py` (mas facil) o como evento frontend

### 4.2 Evento `checklist_item_clicked`
El ProgressChecklist permite click en items no completados para navegar. Eso deberia generar un evento `checklist_item_clicked` con `{label, route}`.

### 4.3 Behavior summary deberia incluir RAG usage
El plan original de 4.3 inyecta behavior_summary en el system prompt. Deberia incluir:
- Cantidad de busquedas RAG del usuario
- Scope mas consultado (help vs business)
- Si el usuario tiene documentos ingestionados

### 4.4 Admin events dashboard
El plan no menciona un tab de eventos en el Streamlit admin, pero seria natural agregarlo junto al knowledge tab (ya existe la infraestructura).

### 4.5 `reportCopilotEvent` necesita conversation_id
El plan muestra `reportCopilotEvent(eventType, eventData, token, conversationId?)`. El `conversationId` esta disponible en el store (`useCopilotStore.conversationId`). La funcion deberia extraerlo automaticamente del store en vez de recibirlo como parametro.

---

## 5. Recomendaciones de ejecucion para Phase 4

### Orden optimo de sub-fases

```
4.1 Modelo de Eventos (backend)     ← Primero: crea tabla + modelo + repo
    |
    v
4.2a Events API (backend)           ← Segundo: endpoint POST /events
    |                                   + GET /events/summary (admin)
    v
4.2b reportCopilotEvent (frontend)  ← Tercero: funcion utilitaria
    |
    v
4.2c Instrumentar componentes       ← Cuarto: agregar calls a los 5+ componentes
    |
    v
4.3 Feedback-Informed Prompting     ← Quinto: inyectar behavior en system prompt
    |
    v
4.4 Admin Events Dashboard          ← Sexto (bonus): tab en Streamlit
```

### Paralelismo posible

- 4.1 + 4.2a son secuenciales (API depende del modelo)
- 4.2b + 4.2c pueden hacerse en paralelo con 4.3 si el contrato de la tabla ya existe
- 4.4 es independiente una vez que el repo existe

### Cuidados especificos

1. **Migracion idempotente:** Recordar usar raw SQL + `IF NOT EXISTS` (ver CLAUDE.md)
2. **Tenant isolation:** Todos los queries de eventos deben filtrar por `tenant_id`
3. **No bloquear el chat:** `reportCopilotEvent` debe ser fire-and-forget (no await en el path critico del chat)
4. **Backward compatibility en prompts:** Si no hay eventos, el system prompt no deberia incluir seccion vacia de behavior

---

## 6. Pre-fixes recomendados antes de empezar Phase 4

| Fix | Severidad | Archivo | Descripcion |
|-----|-----------|---------|-------------|
| tool_call_id vacio | Media | `chat.py:~135` | Agregar tracking de last tool_call_id o verificar si el fallback es dead code |
| Documentar field_id convention | Baja | `copilot-store.ts` (comentario) | Agregar comentario explicando snake_case en interface, camelCase en props |

Ninguno es bloqueante para Phase 4, pero el fix de tool_call_id mejoraria la calidad del replay de conversaciones, que es relevante si Phase 4 quiere usar el historial para analisis.

---

## 7. Archivos de referencia rapida para Phase 4

| Archivo | Relevancia |
|---------|-----------|
| `docs/plans/copilot-v2-phases-2-3-4.md` (lineas 583-735) | Plan original de Phase 4 |
| `backend/src/modules/copilot/application/orchestrator/graph.py` | Donde inyectar behavior_summary (4.3) |
| `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_system.j2` | Donde agregar bloque behavior (4.3) |
| `backend/src/main.py` (lineas 158-163) | Donde registrar events router |
| `frontend/src/features/copilot/api/copilot-api.ts` | Donde agregar reportCopilotEvent |
| `backend/src/admin/app.py` | Donde agregar events tab |
| `CLAUDE.md` (seccion Migrations) | Convenciones de migraciones idempotentes |
| `backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py` | Pattern para nuevo EventRepository |

---

## Resumen ejecutivo

Phase 3 esta **100% implementada y verificada** (ruff clean, tsc clean, tests de roundtrip OK). Agrego 10 archivos nuevos y modifico 10 existentes. Las 4 sub-fases (UI generativa, RAG, conversation memory, admin) estan operativas.

Phase 4 tiene un plan claro en el documento original, pero necesita 4 adiciones descubiertas durante Phase 3: tracking de `knowledge_searched`, `checklist_item_clicked`, RAG usage en behavior summary, y auto-extraction del conversationId. El fix de tool_call_id es recomendable pero no bloqueante.

El camino critico de Phase 4 es: **migracion → modelo → repo → API → frontend util → instrumentar componentes → feedback prompting**.
