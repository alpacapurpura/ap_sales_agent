# Phase 2 — Research Checklist

**Objetivo:** verificar que las decisiones del switch atómico son robustas. Foco en LangGraph callback wiring + event bus patterns.

**Tiempo estimado:** 30-45 min.

---

## 1. LangGraph `RunnableConfig` con callbacks — pattern vigente 2026

**Por qué importa:** la línea más crítica del switch es `graph.astream_events(state, version="v2", config={"callbacks": [handler]})`. Si LangGraph cambió la forma de inyectar callbacks (ej. removed astream_events o renombrado), el switch falla.

**Verificar:**
- WebFetch → https://langchain-ai.github.io/langgraph/concepts/streaming/
- WebFetch → https://langchain-ai.github.io/langgraph/how-tos/stream-values/
- WebSearch → "langgraph astream_events callbacks RunnableConfig 2026"
- Confirmar:
  - `astream_events(state, version="v2", config=...)` sigue siendo API soportada.
  - `config` acepta `{"callbacks": [BaseCallbackHandler]}` (o si cambió a `RunnableConfig` typed dict).
  - Callbacks se propagan a sub-runnables (tools, sub-graphs).

**Si cambió a v3 o equivalente:** ajustar invocación. Anotar en `learnings.md`.

---

## 2. LangChain callback propagation a sub-tools

**Por qué importa:** en deep_agent harness, los tools corren via Runnable interface. Si un tool no propaga callbacks, sus `on_tool_start`/`on_tool_end` no se reciben.

**Verificar:**
- WebSearch → "langchain Tool callback propagation 2026"
- WebFetch → https://python.langchain.com/docs/how_to/tools_runtime_values/
- Confirmar pattern para asegurar que todos los tools del copilot reciben los callbacks del config raíz.

**Si requiere ajuste:** documentar y ajustar el wrapping de tools en deep_agent (sin romper).

---

## 3. Event bus pattern en proyectos LangGraph

**Por qué importa:** decidir si usar event bus interno simple (in-process dict) o algo más robusto.

**Verificar:**
- Leer `backend/src/shared/` completo — buscar event bus existente. Si ya hay → usar.
- WebSearch → "langgraph custom events emit_custom 2026"
- LangGraph tiene `astream_events` con custom events vía `dispatch_custom_event` — investigar si conviene usar eso en vez de event bus separado.

**Decisión:** elegir entre:
- (a) Event bus in-process simple (subscribers sincrónicos, fail-safe).
- (b) `dispatch_custom_event` de LangGraph (eventos viajan junto al stream — más cohesivo).

Anotar elección + razón en `learnings.md`.

---

## 4. SQLAlchemy session lifecycle en callbacks async

**Por qué importa:** callbacks pueden disparar desde threads o coroutines distintas. SQLAlchemy session no es thread-safe.

**Verificar:**
- Leer comportamiento actual de `trace_recorder.py:139-173` — usa `SessionLocal()` (sync) en cada call, no async session. Esto **funciona** porque corre en thread separado.
- Confirmar pattern: cada `on_chat_model_end` → nueva session sync, commit, close. NO compartir session entre callbacks.
- WebSearch → "sqlalchemy 2.0 sessionlocal in callback handler langchain"

**Criterio:** mantener pattern actual (session per write). No cambiar a async session compartida.

---

## 5. ARQ event bus integration

**Por qué importa:** si el event bus es async/queue-based, podría ser ARQ. Pero `register_subscribers` debe ser sincrónico al boot.

**Verificar:**
- Leer `backend/src/workers/settings.py` — ver pattern actual de registración.
- Decidir: subscribers ejecutan sincrónicos en el mismo proceso del FastAPI worker (más simple) o pushean a queue ARQ (más resiliente, más latencia).

**Recomendación tentativa:** sincrónicos in-process (best-effort, like trace_recorder hoy). Confirmar en research.

---

## 6. Tests con `FakeListChatModel` o `FakeChatModel`

**Por qué importa:** test de atomic switch corre el graph completo. Mockear LLM evita costos reales en CI.

**Verificar:**
- WebSearch → "langchain FakeChatModel FakeListChatModel test 2026"
- WebFetch → https://api.python.langchain.com/en/latest/community/chat_models/langchain_community.chat_models.fake.FakeListChatModel.html (o equivalente actual)
- Confirmar pattern con `FakeListChatModel(responses=[...], usage_metadata=[...])` para tests.

**Si la API cambió:** anotar y ajustar tests.

---

## 7. Verificar archivos del repo a tocar

Lectura obligatoria antes de Fase 2:

- `backend/src/modules/copilot/application/orchestrator/chat.py` (full read — entender hot path actual).
- `backend/src/modules/copilot/application/orchestrator/deep_agent.py` (entender wiring de tools/graph).
- `backend/src/modules/copilot/application/orchestrator/graph.py`.
- `backend/src/modules/copilot/application/extraction_card_flow.py` (lugar de `recorder.record(card_emitted)`).
- `backend/src/main.py` (lifespan de FastAPI — donde registrar subscribers).
- `backend/src/shared/` recursive `find . -name "event*"` — buscar event bus existente.
- `backend/tests/modules/copilot/test_trace_recorder.py` y `tests/modules/copilot/test_deep_agent_*` para entender patterns de tests existentes.

---

## 8. Verificar fecha actual + sesiones paralelas

```bash
date
git log --oneline -10
git status --short
```

Si `git status` muestra archivos en `chat.py` o `extraction_card_flow.py` modificados por otra sesión → **postergar fase**, coordinar con el usuario.

---

## Output del research

Bloque al inicio de `learnings.md`:

```markdown
## Research findings (executed YYYY-MM-DD)

### LangGraph astream_events + callbacks
- Status: [vigente / cambió]
- Pattern confirmado: ...

### Callback propagation a tools
- Pattern: ...

### Event bus decision
- Elegido: [in-process / dispatch_custom_event]
- Razón: ...

### SQLAlchemy session lifecycle
- Pattern: [session per write — confirmed]

### ARQ event bus
- [in-process / queue-based]
- Razón: ...

### Test mocking
- Pattern: FakeListChatModel con usage_metadata: confirmed / ajustado

### Sesiones paralelas
- chat.py / extraction_card_flow.py: [libre / con WIP]

### Cambios al diseño respecto a ARCHITECTURE.md
- (vacío si nada)
```

Si "Cambios al diseño" tiene items o sesiones paralelas tienen WIP → **pausá**.
