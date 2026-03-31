# 11 — Observability

## Vision General

El sistema de observabilidad captura **cada decision** del agente: que nodo se ejecuto, que estado recibio, que estado produjo, cuanto tardo, que prompt se envio al LLM, y que respondio. Todo esta linkeable por `trace_id`.

```
┌────────────────────────────────────────────────────┐
│                   agent_traces                      │
│                                                    │
│  trace_id: abc-123                                 │
│  node: "sales_supervisor"                          │
│  input:  { intent: "objection_money", ... }        │
│  output: { next_node: "closer" }                   │
│  time:   45ms                                      │
│                                                    │
│  ┌──────────────────────────────────┐              │
│  │          llm_logs                 │              │
│  │                                  │              │
│  │  trace_id: abc-123               │              │
│  │  model: "gpt-4o-mini"            │              │
│  │  prompt_template: "supervisor_*"  │              │
│  │  prompt_rendered: "You are..."    │              │
│  │  response: "closer"              │              │
│  │  tokens_in: 340                  │              │
│  │  tokens_out: 1                   │              │
│  └──────────────────────────────────┘              │
└────────────────────────────────────────────────────┘
```

---

## 1. trace_node Decorator

**Archivo:** `backend/src/modules/sales_agent/infrastructure/monitoring/tracing.py` (L16-149)

### Uso

```python
@trace_node("sales_supervisor")
def node_sales_supervisor(state: AgentState) -> Dict[str, Any]:
    ...
```

Cada nodo LangGraph esta decorado con `@trace_node("nombre")`. El decorator:
1. Crea un `AgentTrace` en la BD **antes** de ejecutar el nodo
2. Setea `current_trace_id` en contextvars
3. Ejecuta el nodo
4. Actualiza el trace con output y execution time
5. Resetea el contextvars

### Setup (_setup_trace, L25-70)

```python
def _setup_trace(state):
    start_time = time.time()
    db = SessionLocal()
    repo = AuditRepository(db)

    user_uuid = state.get("user_id")
    tenant_uuid = state.get("tenant_id")
    session_id = f"sess_{user_uuid}_{int(start_time/3600)}"

    # Input snapshot (selected fields, not full state)
    input_snapshot = {
        "current_state": state.get("current_state"),
        "detected_intent": state.get("detected_intent"),
        "lead_score": state.get("lead_score"),
        "next_node": state.get("next_node"),
        "last_message": messages[-1] if messages else None,
        "message_count": len(messages),
        "has_agent_identity": bool(state.get("agent_identity")),
        "lead_data": state.get("lead_data"),
        "user_profile": state.get("user_profile"),
        "session_active": state.get("session_active"),
        "launch_stage": state.get("launch_stage"),
    }

    trace = repo.create_trace(
        user_id=user_uuid, tenant_id=tenant_uuid,
        session_id=session_id, node_name=node_name,
        input_state=input_snapshot, output_state={"status": "running"},
        execution_time_ms=0
    )

    token = current_trace_id.set(str(trace.id))
    return start_time, db, repo, trace, token
```

**Decisiones de diseno:**
- **Input snapshot selectivo:** No guarda el `agent_identity` completo (es muy largo). Solo guarda `has_agent_identity: bool`.
- **`session_id` formula:** `"sess_{user_id}_{hour}"` — Agrupa traces de la misma hora. Util para analizar conversaciones completas.
- **`current_trace_id` contextvars:** Permite que `LLMFactory.generate_response()` attache el `trace_id` a los LLM logs sin pasarlo explicitamente.

### Finalize (_finalize_trace, L72-109)

```python
def _finalize_trace(start_time, repo, trace, token, result_state):
    execution_time = (time.time() - start_time) * 1000  # ms

    output_snapshot = {
        "next_node": result_state.get("next_node"),
        "current_state": result_state.get("current_state"),
        "detected_intent": result_state.get("detected_intent"),
        "lead_score": result_state.get("lead_score"),
        "new_message": result_messages[-1] if result_messages else None,
        "message_count": len(result_messages),
        "lead_data": result_state.get("lead_data"),
        "error": result_state.get("error"),
    }

    trace.output_state = output_snapshot
    trace.execution_time_ms = execution_time

    # RL / Data Flywheel Extraction
    if "action" in result_state:
        trace.action = result_state["action"]
    if "reward" in result_state:
        trace.reward = result_state["reward"]
    if "feedback" in result_state:
        trace.feedback = result_state["feedback"]

    repo.db.commit()
    current_trace_id.reset(token)
    repo.close()
```

**Data Flywheel fields:** `action`, `reward`, `feedback` estan preparados para un futuro sistema donde:
- **action:** Que accion tomo el nodo ("route_to_closer")
- **reward:** Score de calidad de la interaccion (post-hoc)
- **feedback:** Feedback humano del operador ("buena respuesta", "cambiar tono")

### Sync/Async Support (L122-147)

```python
if is_async:
    @functools.wraps(func)
    async def wrapper_async(state, *args, **kwargs):
        start_time, db, repo, trace, token = _setup_trace(state)
        try:
            result_state = await func(state, *args, **kwargs)
            _finalize_trace(...)
            return result_state
        except Exception as e:
            _handle_error(e, repo, trace, token)
            raise e
    return wrapper_async
else:
    @functools.wraps(func)
    def wrapper_sync(state, *args, **kwargs):
        ...
```
El decorator detecta automaticamente si la funcion es async o sync y usa el wrapper apropiado.

---

## 2. AuditRepository

**Archivo:** `backend/src/modules/sales_agent/infrastructure/memory/audit_repository.py` (L10-175)

### Metodos del Chat Flow

| Metodo | Usado En | Proposito |
|--------|----------|-----------|
| `get_chat_history(user_id, limit=10)` | `chat.py:368` | Ultimas N interacciones para contexto |
| `log_message(user_id, role, content, channel)` | `chat.py:330, 436` | Persistir mensajes user/assistant |
| `get_last_message(user_id)` | `chat.py:314` | Check session timeout + last intent |

### Metodos de Tracing

| Metodo | Usado En | Proposito |
|--------|----------|-----------|
| `create_trace(...)` | `tracing.py:55` | Crear registro de trace |
| `create_llm_log(...)` | `LLMFactory` | Registrar llamada LLM |

### Metodos del Admin Dashboard

| Metodo | Proposito |
|--------|-----------|
| `get_recent_users(tenant_id, limit=20)` | Lista de leads activos recientes |
| `get_full_timeline(lead_id, tenant_id)` | Timeline combinada (messages + traces + LLM logs) |
| `get_trace_details(trace_id)` | Detalle completo de un trace con sus LLM logs |
| `clear_user_history(lead_id)` | Borrar traces de un lead (admin action) |

### get_full_timeline (L100-142) — Ejemplo de Query Complejo

```python
def get_full_timeline(self, lead_id, tenant_id, limit=50):
    # Fetch Messages
    messages = self.db.query(Message).filter(Message.user_id == lead_id).order_by(Message.created_at.desc()).limit(limit).all()

    # Fetch Traces (eager load LLM logs to avoid N+1)
    traces = self.db.query(AgentTrace).options(joinedload(AgentTrace.llm_logs)).filter(AgentTrace.user_id == lead_id).order_by(AgentTrace.created_at.desc()).limit(limit).all()

    # Merge + Sort by created_at
    timeline = []
    for m in messages:
        timeline.append({"type": "message", "role": m.role, "content": m.content, ...})
    for t in traces:
        llm_summary = {"model": t.llm_logs[0].model, "total_tokens": sum(...)} if t.llm_logs else None
        timeline.append({"type": "trace", "node": t.node_name, "llm_summary": llm_summary, ...})

    timeline.sort(key=lambda x: x["created_at"], reverse=True)
    return timeline[:limit]
```

---

## 3. Context Variables para LLM Log Attachment

**Archivo:** `tracing.py` (L14)

```python
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)
```

**Flujo:**
```
trace_node("sales_supervisor")
  │
  ├─ _setup_trace(): current_trace_id.set("abc-123")
  │
  ├─ node_sales_supervisor():
  │     LLMFactory.generate_response(...)
  │       └─ trace_id = current_trace_id.get()  ← "abc-123"
  │       └─ audit_repo.create_llm_log(trace_id="abc-123", ...)
  │
  └─ _finalize_trace(): current_trace_id.reset(token)
```

Esto permite que los LLM logs se attachen automaticamente al trace correcto sin pasar `trace_id` por todo el call stack.

---

## 4. Ejemplo de Timeline Completa

```
[2026-03-16 10:00:01] MESSAGE (user): "Hola, quiero saber el precio"
[2026-03-16 10:00:02] TRACE main_supervisor (45ms)
                       input: { intent: "buying_signal", score: 0 }
                       output: { next_node: "sales_agent" }
[2026-03-16 10:00:02] TRACE sales_supervisor (120ms)
                       input: { intent: "buying_signal", stage: "rapport" }
                       output: { next_node: "closer" }
                       LLM: gpt-4o-mini, 340 tokens in, 1 out
[2026-03-16 10:00:04] TRACE closer (2100ms)
                       input: { next_node: "closer" }
                       output: { messages: [{ role: "assistant", content: "..." }] }
                       LLM: gpt-4o, 1200 tokens in, 280 out
[2026-03-16 10:00:04] MESSAGE (assistant): "¡Hola! Me encanta tu interés..."
```

---

## Casuisticas

### Que pasa si la BD esta lenta y el tracing retrasa el nodo?
El tracing crea el record en la BD (1 INSERT, ~5ms) antes de ejecutar el nodo. Es overhead minimo. El finalize es otro UPDATE + COMMIT (~5ms). Total overhead: ~10ms, negligible comparado con los 2-5s de LLM calls.

### Que pasa si el tracing falla?
`_handle_error` catchea la excepcion, intenta guardar el error en el trace, y resetea el contextvars. La excepcion original se re-lanza para que el nodo falle normalmente.

### Los LLM logs guardan el prompt completo?
Si. `prompt_rendered` contiene el prompt completo tal como se envio al LLM. Esto es critico para debugging pero ocupa espacio. Un TODO potencial es comprimir o truncar prompts largos.
