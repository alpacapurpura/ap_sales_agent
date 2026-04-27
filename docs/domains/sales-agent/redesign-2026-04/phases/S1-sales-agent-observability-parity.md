# S1 · Sales agent observability parity + PII

## Objetivo

Sales_agent adopta `shared/agent_observability/` (S0) con `SalesAgentCallbackHandler`. Crea tablas event-sourced. **PII sanitization activa día 1** (bloqueante de seguridad). Dual-write con `@trace_node` por 4 semanas para validar paridad antes de cutover.

## Dependencias

- S0 cerrado: `shared/agent_observability/` con `BaseAgentCallbackHandler` + repos abstract.

## Criterios de éxito

1. Tablas creadas vía Alembic idempotente:
   - `sales_agent_llm_call` (mirror `copilot_llm_call` + `lead_id` UUID + `channel_type` text)
   - `sales_agent_trace_event` (mirror + `lead_id` + `channel_type`)
   - `sales_agent_routing_log` (mirror + `lead_id` + `stage` + `lead_score`)
2. `SalesAgentCallbackHandler` registrado en `LLMFactory.get_service(role).get_client(callbacks=[handler])`.
3. PII sanitization activa: emails / phones LATAM / tokens / **DNI/CURP/CUIT/RFC** redactados.
4. Dual-write: `@trace_node` y callback handler escriben en paralelo. Worker reconciliation diff <1%.
5. Domain event bus suscriptores: `EVENT_TURN_STARTED`, `EVENT_TURN_ENDED`, `EVENT_LEAD_QUALIFIED`, `EVENT_OBJECTION_HANDLED`.
6. Best-effort: callback handler exception NO rompe turn (test arquitectónico).
7. Trace queries funcionan en Streamlit `/trazas` (extender admin para sales_agent).
8. Quality gates verdes.
9. §3 sigue funcionando (closer studio, buffer, webhooks, follow-up, frozen).

## Research mandate

### Queries WebSearch obligatorias

1. `LATAM PII regex DNI CURP CUIT RFC compliance 2026` — patterns vigentes.
2. `LangGraph callback handler StateGraph node-level vs LLM-level capture` — verificar si `astream_events` v2 captura tool calls que pasan por nodes (sales tiene tools dispatched fuera de LLM).
3. `dual-write observability migration pattern legacy decorator` — patrones de cutover seguro.
4. `Mercado Pago payment link PII data sensitivity LATAM` — qué tipo de datos NO logear.

### Tessl tiles

- `tessl__langgraph` — verificar si state graph + callback handler tienen race condition con `astream_events`.
- `tessl__fastapi` — DI del callback handler en endpoints sales (`webhook` + `closer-studio`).

### Lectura obligatoria

- Aprendizajes de S0: `learnings/S0-*.md`.
- `backend/src/modules/sales_agent/infrastructure/monitoring/tracing.py` — `@trace_node` actual.
- `backend/src/modules/sales_agent/application/orchestrator/chat.py` — entrada de turn.
- `backend/src/modules/sales_agent/application/agents/sales/graph.py` — StateGraph subgraph.
- `backend/src/modules/sales_agent/infrastructure/models/agent_trace_model.py`, `agent_log_model.py`, `agent_state_checkpoint_model.py`.
- `.claude/rules/copilot-observability.md` — reusar reglas.
- `.claude/rules/backend-migrations.md` — idempotencia.

### Hallazgos research

> COMPLETAR DURANTE FASE.

---

## Diseño

### Migración Alembic (idempotente)

```python
# Raw SQL CREATE TABLE IF NOT EXISTS — referenciar enum types existentes
op.execute("""
CREATE TABLE IF NOT EXISTS sales_agent_llm_call (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    channel_type TEXT NOT NULL,
    turn_id UUID NOT NULL,
    span_id UUID NOT NULL,
    parent_span_id UUID,
    role TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_requested TEXT NOT NULL,
    model_responded TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cached_read_tokens INTEGER,
    cost_usd NUMERIC(16,10),
    pricing_version_id UUID REFERENCES model_pricing_snapshot(id),
    duration_ms INTEGER,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    occurred_on DATE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')::DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""")
op.execute("CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_tenant_day ON sales_agent_llm_call(tenant_id, occurred_on);")
op.execute("CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_lead ON sales_agent_llm_call(tenant_id, lead_id);")
op.execute("CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_turn ON sales_agent_llm_call(turn_id);")
```

(Equivalente para `sales_agent_trace_event`, `sales_agent_routing_log`.)

### `SalesAgentCallbackHandler`

```python
# src/modules/sales_agent/observability/callback_handler.py
class SalesAgentCallbackHandler(BaseAgentCallbackHandler):
    def __init__(self, db_session, tenant_id, lead_id, channel_type, ...):
        super().__init__(...)
        self._lead_id = lead_id
        self._channel_type = channel_type

    async def _persist_llm_call(self, call: LLMCallEvent) -> None:
        try:
            await self._llm_call_repo.add(SalesAgentLlmCall(
                ...,
                lead_id=self._lead_id,
                channel_type=self._channel_type,
            ))
        except Exception as exc:
            logger.warning("sales_agent_obs_write_failed", error=str(exc))
            await self._db_session.rollback()
```

### PII sanitization extensión

Agregar patterns LATAM al `sanitization.py` shared:

```python
# DNI Argentina: 7-8 dígitos
_LATAM_NATIONAL_ID_PATTERNS = [
    re.compile(r"\b\d{7,8}\b(?:\s+(?:dni|documento))"),  # AR
    re.compile(r"\b[A-Z]{4}\d{6}[A-Z]{6}\d{2}\b"),       # CURP MX (18 chars)
    re.compile(r"\b\d{2}-\d{8}-\d{1}\b"),                 # CUIT/CUIL AR
    re.compile(r"\b[A-Z]{4}\d{6}[A-Z0-9]{3}\b"),         # RFC MX (13)
    re.compile(r"\b\d{8,11}\b(?:\s+(?:dni|cedula|cc|nit))"),  # PE/CO
]
```

NOTA: regex agnostic-of-language; NO false-positive en UUIDs (ya cubierto por keyword guard).

### Dual-write reconciliation worker

```python
# src/modules/sales_agent/observability/workers/dual_write_reconciliation_task.py
async def reconcile_dual_write(...):
    """Compara últimas N rows de agent_log vs sales_agent_llm_call.
    Reporta diff > 1% como alert.
    Corre cada 1h durante 4 semanas. Después se desinstala."""
```

### Domain events nuevos

```python
# src/modules/sales_agent/domain/events.py
class LeadQualifiedEvent(DomainEvent):
    @classmethod
    def create(cls, tenant_id, lead_id, score, signals, ...): ...

class ObjectionHandledEvent(DomainEvent): ...

class StageTransitionedEvent(DomainEvent): ...
```

Suscriptores en `observability/domain_subscribers.py` persisten a `sales_agent_trace_event`.

---

## Plan TDD

### RED tests primero

1. `tests/modules/sales_agent/observability/test_callback_handler.py`:
   - Handler escribe row a `sales_agent_llm_call` con `lead_id` + `channel_type`.
   - Excepción en repo NO rompe turn (best-effort).
   - PII sanitizada en payload persistido.

2. `tests/modules/sales_agent/observability/test_pii_latam.py`:
   - DNI AR / CURP MX / CUIT AR / RFC MX redactados.
   - UUIDs y números de orden NO redactados (false-positive guard).

3. `tests/modules/sales_agent/observability/test_dual_write_parity.py`:
   - Mock turn → ambas tablas pobladas con datos consistentes.
   - Diff calculado por reconciliation worker = 0.

4. `tests/architecture/test_no_pii_in_writes.py`:
   - Todo write a `sales_agent_trace_event` o `sales_agent_llm_call` debe pasar por `sanitize_payload()`.
   - AST scan: si encuentra `repo.add(...)` con argumento sin pasar por sanitizer → fail.

5. `tests/architecture/test_callback_handler_best_effort.py`:
   - `SalesAgentCallbackHandler._persist_*` envuelto en try/except + structlog.warning + db.rollback.

---

## Implementación step-by-step

1. Migración Alembic 3 tablas + indexes idempotente. Test en clone DB.
2. Modelos SQLA (`sales_agent_llm_call_model.py`, etc.) registrados en `tests/conftest.py::db_engine`.
3. Repos concretos heredan `BaseLLMCallRepo` (S0).
4. `SalesAgentCallbackHandler` heredando `BaseAgentCallbackHandler`.
5. Extender PII patterns LATAM en `shared/.../sanitization.py`. Tests primero.
6. Wire del handler en `LLMFactory` para sales role: `factory.get_service(ModelRole.FAST, callbacks=[sales_handler])`.
7. Domain events nuevos + subscribers.
8. Reconciliation worker dual-write (ARQ task hourly, opt-in via env).
9. Streamlit admin `/trazas` extender con filtro `agent_kind=sales_agent`.
10. Smoke test live: turn real con webhook Telegram dev → verificar rows.

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Latencia adicional del callback | Best-effort + measure <10ms p99. Si excede → cola async + drainer. |
| Diff dual-write >1% | Investigar antes de cutover. NO drop `@trace_node` hasta verde 4 semanas. |
| PII regex false-positive | Test exhaustivo con UUID, números de orden, decimales. Keyword guard estricto. |
| Race condition en `astream_events` | Verificar en research que callback handler funciona correcto en LangGraph 0.3+. |
| Migración rompe DB clone (FK enum) | Raw SQL `IF NOT EXISTS` + reference types existentes. Test en clone antes prod. |

---

## Tech debt watchpoints

- `@trace_node` → eliminar completo cuando dual-write verde 4 semanas + cutover commit. Loggear plan para S2.
- `AgentLogModel` legacy → drop en migración separada post-cutover.
- Si encontrás `print()` en sales_agent paths → fix (debe ser `structlog`). Loggear.
- Si encontrás `datetime.utcnow()` → fix a `utc_now()`. Loggear.
- `messages` JSONB en `agent_state_checkpoint` puede tener PII no sanitizada — flag para retention task de S2.

---

## Ajustes vs plan original

> COMPLETAR si research/implementación reveló desviación.
