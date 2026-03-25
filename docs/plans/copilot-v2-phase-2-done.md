# Copilot v2: Phase 2 — Implementación Completada

> **Fecha:** 2026-03-25
> **Estado:** HECHO — CI verificado (ruff clean, tsc clean)
> **Dependencias:** Phase 1 (Schema-Driven Foundation) ✅

---

## Arquitectura Post-Phase 2

### Backend: `backend/src/modules/copilot/` (cambios Phase 2)

```
copilot/
├── domain/
│   ├── module_registry.py          # Sin cambios (7 módulos)
│   ├── schema_introspection.py     # Sin cambios
│   └── navigation_map.py           # Sin cambios
├── application/
│   ├── orchestrator/
│   │   ├── state.py                # ✅ +active_procedure: Optional[Dict[str, Any]]
│   │   ├── graph.py                # ✅ +active_procedure_ctx inyectado al system prompt
│   │   └── chat.py                 # Sin cambios (SSE ui_action emit ya funcionaba)
│   ├── procedures/                 # ✅ NUEVO directorio
│   │   ├── __init__.py
│   │   ├── base.py                 # ProcedureStep + Procedure dataclasses
│   │   ├── brand_setup.py          # 6 pasos (identity→communication_assets)
│   │   ├── offer_creation.py       # 1 paso (create_offer)
│   │   └── first_setup.py          # 4 pasos meta-procedimiento
│   └── tools/
│       ├── registry.py             # ✅ +"procedure" en TOOL_GROUPS y ALL routes
│       └── procedure_tools.py      # ✅ NUEVO: start/status/advance + PROCEDURE_REGISTRY
└── api/
    └── nudge.py                    # ✅ NUEVO: GET /nudge-context?route=
```

### Frontend: `frontend/src/features/copilot/` (cambios Phase 2)

```
copilot/
├── store/
│   └── copilot-store.ts            # ✅ +ActiveProcedure, +ProcedureStepStatus, UIAction extendido
├── hooks/
│   ├── useCopilotChat.ts           # ✅ +setActiveProcedure en onUIAction handler
│   └── useProactiveNudges.ts       # ✅ NUEVO: fetch nudges + dismiss via localStorage
└── components/
    ├── CopilotChat.tsx             # ✅ +ProcedureProgress mount + NudgeBanner cuando messages vacío
    ├── CopilotRail.tsx             # ✅ +amber pulse dot cuando hasNudges
    ├── ProcedureProgress.tsx        # ✅ NUEVO: dot stepper (green/purple-pulse/gray)
    └── NudgeBanner.tsx             # ✅ NUEVO: purple left-border + Lightbulb + CTA + dismiss
```

---

## Hallazgos y Decisiones Relevantes para Phases 3 y 4

### 1. No existe `src/core/redis.py`

**Problema:** El plan original para nudges proponía cache Redis con `from src.core.redis import get_redis`. No existe ese módulo.

**Decisión:** Se implementó cache in-memory con TTL de 5 minutos (`_nudge_cache: dict` en `nudge.py`).

**Impacto para Phase 4:**
- Si se quiere persistir eventos de nudge (`nudge_clicked`, `nudge_dismissed`) necesitan la tabla `copilot_events` — **no depende de Redis**.
- Si más adelante se necesita Redis compartido (ej. para invalidación cross-process), hay que crear `src/core/redis.py` con un helper que use `settings.REDIS_URL` (que sí existe, se usa en ARQ).

### 2. SSE `ui_action` emit ya funcionaba sin cambios

**Hallazgo:** El mecanismo en `chat.py` (líneas 130-143) ya parsea `tool_output` buscando `"ui_action"` key y emite el SSE event automáticamente. No fue necesario modificar `chat.py`.

**Impacto para Phase 3:**
- Los nuevos tipos de `ui_action` (`metric_summary`, `comparison`, `checklist`, `multi_option`) funcionarán sin tocar `chat.py` — solo necesitan que los tools retornen `json.dumps({"ui_action": {...}})` en su output.
- El parsing en `chat.py` usa `json.loads(tool_output.replace("'", '"'))` como fallback — esto es frágil. Si se quiere robustecer, migrar a un protocolo más formal (ej. separar texto de metadata con un delimitador).

### 3. `UIAction` type en store ya es extensible

**Estado actual del tipo:**
```typescript
type: "navigate" | "scroll_to_field" | "open_form" | "proposal" | "procedure_progress"
```

**Impacto para Phase 3:**
- Solo agregar los nuevos tipos: `"metric_summary" | "comparison" | "checklist" | "multi_option"`.
- Los campos opcionales de `UIAction` ya aceptan extensión — agregar `metrics?`, `columns?`, `rows?`, `items?`, `options?`.

### 4. Procedure tools retornan `json.dumps({"text": ..., "ui_action": ...})`

**Patrón establecido:** Los procedure tools retornan un JSON string con dos keys:
- `text`: markdown para el LLM
- `ui_action`: payload que chat.py emite como SSE event

**Impacto para Phase 3:**
- Seguir este patrón para `knowledge_tools.py` y cualquier tool que necesite emitir UI generativa.
- El LLM recibe el JSON raw como tool result — incluir siempre `text` legible para que el LLM pueda responder coherentemente.

### 5. `ProcedureProgress` step labels truncados a 30 chars

**Decisión:** En `_build_ui_action()` (`procedure_tools.py`), los labels se truncan desde la instruction: `step.instruction.split(":")[0].split("—")[0].strip()[:30]`.

**Impacto para Phase 3:**
- Si `ProgressChecklist` (Phase 3) reusa data similar, considerar un campo `label` explícito en `ProcedureStep` en lugar de derivarlo del instruction.
- Actualmente los labels son: "Completa la identidad básica d", "Cuenta la historia de tu marc", etc.

### 6. `useProactiveNudges` duplica lógica de headers de tenant

**Hallazgo:** La extracción de `X-Tenant-ID` desde la URL se repite en `copilot-api.ts` y `useProactiveNudges.ts`. Es la misma lógica de globals + localStorage fallback.

**Impacto para Phase 4:**
- Cuando se cree `reportCopilotEvent()` en `copilot-api.ts`, NO duplicar la lógica de headers — extraerla a un helper `getCopilotHeaders(token)` reutilizable.
- Esto afecta: `streamCopilotChat`, `useProactiveNudges.fetchNudges`, y el futuro `reportCopilotEvent`.

### 7. Nudge rules son declarativas pero no configurables

**Estado:** Las 4 reglas de nudge están hardcodeadas en `_generate_nudges()`:
1. `EmptyModuleNudge` — módulo de la ruta actual vacío
2. `CrossModuleGapNudge` — brand>30% pero offer=0%
3. `CrossModuleGapNudge` — brand+offer listos pero connections=0%
4. `IncompleteModuleNudge` — módulo <30% completado

**Impacto para Phase 4:**
- Los eventos `nudge_clicked` y `nudge_dismissed` ya tienen `nudge.id` como key (`empty_brand`, `cross_brand_offer`, etc.).
- Para feedback-informed prompting, se puede usar `event_data.nudge_id` para saber qué nudges son más efectivos.
- Futuro: mover las reglas a una estructura declarativa (lista de `NudgeRule` dataclasses) para hacerlas configurables por tenant.

### 8. `active_procedure` en state NO se persiste entre requests

**Hallazgo:** `CopilotState` es un `TypedDict` que se crea fresh cada request via `create_initial_copilot_state()`. El `active_procedure` inicia como `None` siempre.

**Cómo funciona actualmente:**
- El frontend mantiene `activeProcedure` en Zustand (persiste en la sesión del browser).
- Cada vez que el LLM llama `start_procedure` o `advance_procedure`, el tool emite `procedure_progress` UIAction → frontend actualiza el store.
- El system prompt recibe `active_procedure` solo si `state["active_procedure"]` fue seteado durante el request (vía tool execution).

**Impacto:**
- En la práctica, el procedure context en el system prompt solo aparece cuando el tool se ejecuta en el mismo request. Esto es aceptable porque el LLM decide cuándo llamar `advance_procedure`.
- Para Phase 4, si se quiere trackear `procedure_started`/`procedure_completed`/`procedure_abandoned`, el tracking debe ocurrir en el frontend (que tiene el estado persistente) o en los tools cuando se ejecutan.

### 9. NudgeBanner integrado solo cuando messages=0

**Decisión:** Los nudge banners se muestran solo en el estado vacío del chat (sin mensajes). Una vez el usuario envía un mensaje, desaparecen de la vista.

**Impacto para Phase 4:**
- Los eventos `nudge_clicked` pueden reportarse desde `NudgeBanner.onAction` (el handler ya tiene el `suggested_prompt`).
- Los eventos `nudge_dismissed` pueden reportarse desde `NudgeBanner.onDismiss` (el handler ya tiene el `nudge.id`).
- Para Phase 4, solo necesitan wrappear estos callbacks con `reportCopilotEvent()`.

### 10. `PROCEDURE_REGISTRY` es importable globalmente

**Patrón:** `PROCEDURE_REGISTRY` es un dict module-level en `procedure_tools.py`, importable desde cualquier parte.

**Impacto para Phase 4:**
- Se puede usar en `graph.py` para resolver procedure metadata (ya se hace con lazy import).
- Se puede usar en future admin endpoints para listar procedimientos disponibles.
- Para agregar nuevos procedimientos: crear archivo en `procedures/`, importar en `procedure_tools.py`, agregar al dict.

---

## Archivos Creados / Modificados (Resumen)

### Creados (10 archivos)

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `procedures/__init__.py` | Backend | Empty init |
| `procedures/base.py` | Backend | `ProcedureStep` + `Procedure` con validación schema-driven |
| `procedures/brand_setup.py` | Backend | 6 pasos: identity, story, positioning, narrative, visuals, communication_assets |
| `procedures/offer_creation.py` | Backend | 1 paso: create_offer (has_any_data) |
| `procedures/first_setup.py` | Backend | 4 pasos meta: identity → positioning → offer → connection |
| `tools/procedure_tools.py` | Backend | 3 tools + PROCEDURE_REGISTRY + _build_ui_action() |
| `api/nudge.py` | Backend | GET /nudge-context + 4 reglas declarativas + cache in-memory 5min |
| `components/ProcedureProgress.tsx` | Frontend | Horizontal dot stepper (green/purple-pulse/gray) |
| `components/NudgeBanner.tsx` | Frontend | Purple border + Lightbulb + CTA + dismiss |
| `hooks/useProactiveNudges.ts` | Frontend | Fetch on route change + localStorage dismiss filter |

### Modificados (8 archivos)

| Archivo | Cambio |
|---------|--------|
| `state.py` | `+active_procedure: Optional[Dict]` + init as `None` |
| `graph.py` | Build `active_procedure_ctx` from PROCEDURE_REGISTRY → pass to render() |
| `copilot_system.j2` | `{% if active_procedure %}` block con paso actual, instruction, tips |
| `registry.py` | `+"procedure"` en TOOL_GROUPS + ALL routes en ROUTE_TOOL_MAP |
| `main.py` | Import + register `copilot_nudge.router` under `/api/v1/copilot` |
| `copilot-store.ts` | `+ActiveProcedure`, `+ProcedureStepStatus` interfaces, UIAction extended, store actions |
| `useCopilotChat.ts` | `+setActiveProcedure` on `procedure_progress` UIAction |
| `CopilotChat.tsx` | `+ProcedureProgress` mount + `+NudgeBanner` in empty state |
| `CopilotRail.tsx` | `+amber pulse dot` when nudges pending |

---

## Contrato API (Establecido)

### Nudge Endpoint
```
GET /api/v1/copilot/nudge-context?route={current_route}
Headers: Authorization, X-Tenant-ID

Response 200:
{
  "nudges": [{
    "id": "empty_brand",
    "type": "empty_module" | "cross_module_gap" | "incomplete_module",
    "module_id": "brand",
    "title": "Tu Brand Studio está vacío",
    "message": "Configura tu identidad de marca...",
    "suggested_prompt": "Guíame para configurar mi marca",
    "priority": 1
  }]
}
```

### Procedure UIAction (via SSE `ui_action` event)
```json
{
  "type": "procedure_progress",
  "procedure_id": "brand_setup",
  "procedure_name": "Configuración de Marca",
  "steps": [
    {"id": "identity", "label": "Completa la identidad básica d", "status": "completed", "routeHint": "brand-settings"},
    {"id": "story", "label": "Cuenta la historia de tu marc", "status": "current", "routeHint": "brand-settings"},
    {"id": "positioning", "label": "Define el posicionamiento de", "status": "pending", "routeHint": "brand-settings"}
  ],
  "current_step_index": 1
}
```

### Frontend Types (establecidos)
```typescript
interface ProcedureStepStatus {
  id: string;
  label: string;
  status: "completed" | "current" | "pending";
  routeHint?: string;
}

interface ActiveProcedure {
  id: string;
  name: string;
  steps: ProcedureStepStatus[];
  currentStepIndex: number;
}

// UIAction.type ahora incluye: "procedure_progress"
// UIAction tiene campos opcionales: procedure_id, procedure_name, steps, current_step_index
```

---

## Dependencias para Phases 3 y 4

### Phase 3 puede proceder sin bloqueos
- `UIAction` type extensión → solo agregar nuevos types + campos opcionales al interface
- `chat.py` SSE emit → ya funciona para cualquier tool que retorne `{"ui_action": {...}}`
- `registry.py` pattern → solo agregar nuevo tool group + routes
- Qdrant reuse → `sales_agent/infrastructure/memory/vector_store.py` existe y es reutilizable

### Phase 4 depende de Phase 2 (completada) para:
- `nudge_clicked` / `nudge_dismissed` events → `NudgeBanner` ya tiene los handlers, solo wrappear con `reportCopilotEvent()`
- `procedure_started` / `procedure_completed` / `procedure_abandoned` events → tools ya emiten los estados, frontend ya los trackea en Zustand
- **Acción requerida:** Extraer helper `getCopilotHeaders(token)` antes de crear `reportCopilotEvent()` para evitar triplicar la lógica de `X-Tenant-ID` extraction

---

## Secuenciación Actualizada

```
Phase 1 ✅ Schema-Driven Foundation
Phase 2 ✅ Procedimientos Guiados + Inteligencia Proactiva (este documento)

Phase 3 → Rich Intelligence (INDEPENDIENTE de Phase 2)
  ├── 3.1 4 generative UI components + AssistantMessage switch + store types
  ├── 3.2 RAG: knowledge_tools + knowledge_ingestion + knowledge API
  └── 3.3 Conversation memory: tool_calls serialization in chat.py

Phase 4 → Learning (DEPENDE de Phase 2 ✅ y Phase 3)
  ├── 4.1 copilot_events migration + model + repository
  ├── 4.2 Events API + frontend reportCopilotEvent (extraer getCopilotHeaders helper primero)
  │   └── Integrar en: ProposalCard, NavigationCard, NudgeBanner, MultiOptionSelector
  └── 4.3 Feedback-informed prompting in graph.py + template
```

> **Phase 2 desbloqueó Phase 4.** Los componentes NudgeBanner y ProcedureProgress ya tienen handlers listos para event tracking.
