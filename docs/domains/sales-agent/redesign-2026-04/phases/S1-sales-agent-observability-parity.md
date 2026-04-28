# S1 · Sales agent observability parity + PII + tool_call_dedup

> **Actualizado 2026-04-28**: incluye explicit mirroring de `tool_call_dedup.py` (commit 3aab4002 copilot anti-loop). Reusa `pricing/aliases.py` (commit a3f65d04) cross-agent. Streamlit `sales_audit.py` migration plan via dual-read window.

## Objetivo

Sales_agent adopta `shared/agent_observability/` (S0) con `SalesAgentCallbackHandler`. Crea tablas event-sourced. **PII sanitization activa día 1** (bloqueante seguridad). Mirror del `tool_call_dedup.py` anti-loop. Dual-write con `@trace_node` por 4 semanas. Streamlit `sales_audit.py` adopta dual-read durante ventana.

## Dependencias

- S0 cerrado: `shared/agent_observability/` con `BaseAgentCallbackHandler` + repos abstract + `pricing/aliases.py` movido a shared.
- S00 cerrado: audit map existe, deprecated cleanup ejecutado.

## Criterios de éxito

1. Tablas creadas vía Alembic idempotente:
   - `sales_agent_llm_call` (mirror `copilot_llm_call` + `lead_id` UUID + `channel_type` text)
   - `sales_agent_trace_event` (mirror + `lead_id` + `channel_type`)
   - `sales_agent_routing_log` (mirror + `lead_id` + `stage` + `lead_score`)
2. `SalesAgentCallbackHandler` registrado en `LLMFactory.get_service(role).get_client(callbacks=[handler])`. Heredando `BaseAgentCallbackHandler` (S0). Reusa pricing resolver + aliases (Kimi K2.6/K2.5 ya correctos).
3. PII sanitization activa: emails / phones LATAM / tokens / **DNI/CURP/CUIT/RFC**.
4. `sales_agent/application/tools/tool_call_dedup.py` mirror de copilot (commit 3aab4002):
   - Per-turn tracker
   - Threshold 3 → anti-loop directive
   - Hard limit 5 → `ToolCallLoopError`
5. Dual-write 4 semanas: `@trace_node` y callback handler escriben en paralelo. Worker reconciliation diff <1%.
6. Domain event subscribers: `EVENT_TURN_STARTED`, `EVENT_TURN_ENDED`, `EVENT_LEAD_QUALIFIED`, `EVENT_OBJECTION_HANDLED`, `EVENT_TOOL_LOOP_DETECTED`.
7. Best-effort: callback handler exception NO rompe turn (test arquitectónico).
8. Trace queries funcionan en Streamlit `/trazas` (extender admin con filtro `agent_kind=sales_agent`).
9. **`sales_audit.py` dual-read**: durante ventana 4 semanas lee ambas tablas, muestra "leyendo desde sales_agent_trace_event (preferred) / agent_trace_model (legacy)". Post-cutover (S6) drop legacy reads.
10. Quality gates verdes (incluye admin smoke `tests/admin/test_admin_smoke.py`).
11. §3 sigue funcionando.

## Research mandate

### Queries WebSearch obligatorias

1. `LATAM PII regex DNI CURP CUIT RFC compliance 2026` — patterns vigentes.
2. `LangGraph callback handler StateGraph node-level vs LLM-level capture` — verificar si `astream_events` v2 captura tool calls dispatched fuera de LLM (sales tiene tools manualmente parsed por signal_accumulator).
3. `dual-write observability migration pattern legacy decorator cutover` — patrones cutover seguro.
4. `Streamlit dual-read pattern admin dashboard migration zero-downtime`.
5. `Mercado Pago payment link PII data sensitivity LATAM 2026` — qué tipo NO loguear.

### Tessl tiles

- `tessl__langgraph` — verificar si state graph + callback handler tienen race condition con `astream_events`.
- `tessl__fastapi` — DI del callback handler.

### Lectura obligatoria

- Aprendizajes S00 + S0 (`learnings/S00-*.md`, `learnings/S0-*.md`).
- `audit/sales-agent-current-state.md` — sección DB tables touched.
- `audit/admin-migration-plan.md` — sales_audit.py migration path.
- `backend/src/modules/sales_agent/infrastructure/monitoring/tracing.py` — `@trace_node` actual.
- `backend/src/modules/sales_agent/application/orchestrator/chat.py` — entrada de turn.
- `backend/src/modules/sales_agent/application/agents/sales/graph.py` — StateGraph subgraph.
- `backend/src/modules/sales_agent/application/agents/sales/nodes.py` — signal_accumulator + tool dispatch.
- `backend/src/modules/sales_agent/infrastructure/models/agent_trace_model.py`, `agent_log_model.py`.
- `backend/src/modules/copilot/application/orchestrator/tool_call_dedup.py` — mirror source (commit 3aab4002).
- `backend/src/modules/copilot/observability/recording/callback_handler.py` (post Phase 2 atomic switch — pattern reference).
- `backend/src/modules/copilot/observability/pricing/aliases.py` (post commit a3f65d04 — reuse).
- `backend/src/admin/modules/sales_audit.py` — current shape.
- `.claude/rules/copilot-observability.md` — reusar reglas.
- `.claude/rules/copilot-resilience.md` — best-effort patterns + tool_call_dedup pattern.
- `.claude/rules/backend-migrations.md` — idempotencia.
- `.claude/rules/admin-panel.md`.

### Hallazgos research

> COMPLETAR.

---

## Diseño

### Migración Alembic (idempotente)

```sql
CREATE TABLE IF NOT EXISTS sales_agent_llm_call (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    channel_type TEXT NOT NULL,
    turn_id UUID NOT NULL,
    span_id UUID NOT NULL,
    parent_span_id UUID,
    role TEXT NOT NULL,
    provider TEXT NOT NULL,                          -- e.g. 'kimi', 'deepseek', 'openai'
    model_requested TEXT NOT NULL,
    model_responded TEXT NOT NULL,                   -- e.g. 'kimi-k2.6', 'deepseek-reasoner'
    input_tokens INTEGER,
    output_tokens INTEGER,
    cached_read_tokens INTEGER,
    reasoning_tokens INTEGER,                        -- for reasoning models
    cost_usd NUMERIC(16,10),
    pricing_version_id UUID REFERENCES model_pricing_snapshot(id),
    duration_ms INTEGER,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    occurred_on DATE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')::DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_tenant_day ON sales_agent_llm_call(tenant_id, occurred_on);
CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_lead ON sales_agent_llm_call(tenant_id, lead_id);
CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_turn ON sales_agent_llm_call(turn_id);
```

(Equivalente para `sales_agent_trace_event`, `sales_agent_routing_log`.)

### `SalesAgentCallbackHandler`

```python
class SalesAgentCallbackHandler(BaseAgentCallbackHandler):
    """Reusa pricing/aliases.py shared (Kimi K2.6/K2.5 → LiteLLM)
    + cost calculator + FX resolver."""

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
                reasoning_tokens=call.reasoning_tokens,  # for DeepSeek-V4
            ))
        except Exception as exc:
            logger.warning("sales_agent_obs_write_failed", error=str(exc))
            await self._db_session.rollback()
```

### `tool_call_dedup.py` mirror

```python
# src/modules/sales_agent/application/tools/tool_call_dedup.py
# Mirror de copilot/application/orchestrator/tool_call_dedup.py (commit 3aab4002).

class ToolCallDedupTracker:
    """Per-turn. Detecta tool calls repetidos.
    Threshold=3 → anti-loop directive en next prompt.
    Hard limit=5 → raise ToolCallLoopError."""

    def __init__(self, threshold: int = 3, hard_limit: int = 5):
        self._counts: dict[tuple[str, str], int] = {}  # (tool_name, args_hash) → count
        self._threshold = threshold
        self._hard_limit = hard_limit

    def record(self, tool_name: str, args: dict) -> ToolCallStatus:
        key = (tool_name, _hash_args(args))
        self._counts[key] = self._counts.get(key, 0) + 1
        if self._counts[key] >= self._hard_limit:
            raise ToolCallLoopError(...)
        if self._counts[key] >= self._threshold:
            return ToolCallStatus.ANTI_LOOP_DIRECTIVE
        return ToolCallStatus.OK
```

Wire en `signal_accumulator` o `tool_executor` node.

### PII sanitization extensión LATAM

```python
_LATAM_NATIONAL_ID_PATTERNS = [
    re.compile(r"\b\d{7,8}\b(?=\s+(?:dni|documento))"),         # AR DNI
    re.compile(r"\b[A-Z]{4}\d{6}[A-Z]{6}\d{2}\b"),               # CURP MX (18)
    re.compile(r"\b\d{2}-\d{8}-\d{1}\b"),                        # CUIT/CUIL AR
    re.compile(r"\b[A-Z]{4}\d{6}[A-Z0-9]{3}\b"),                # RFC MX (13)
    re.compile(r"\b\d{8,11}\b(?=\s+(?:dni|cedula|cc|nit|ruc))"), # PE/CO/EC/UY
]
```

### Dual-write reconciliation worker

```python
# src/modules/sales_agent/observability/workers/dual_write_reconciliation_task.py
async def reconcile_dual_write(...):
    """Compara últimas N rows agent_log vs sales_agent_llm_call.
    Reporta diff > 1% como alert.
    Cron 1h. Disinstala post 4 semanas."""
```

### `sales_audit.py` dual-read

```python
# Durante ventana 4 semanas:
def render_sales_audit():
    legacy = query_agent_trace_model(tenant_id)
    new = query_sales_agent_trace_event(tenant_id)
    if new.count > 0 and legacy.count > 0:
        st.info("Dual-read window: leyendo trazas nuevas (preferido) + legacy")
        rows = merge_dedupe(new, legacy, key="turn_id")
    elif new.count > 0:
        rows = new
    else:
        rows = legacy
    render_rows(rows)
```

Post-S6 cutover: borrar query legacy.

### Domain events

```python
class LeadQualifiedEvent(DomainEvent): ...
class ObjectionHandledEvent(DomainEvent): ...
class StageTransitionedEvent(DomainEvent): ...
class ToolLoopDetectedEvent(DomainEvent): ...  # nuevo
```

---

## Plan TDD

### RED tests

1. `tests/modules/sales_agent/observability/test_callback_handler.py`:
   - Handler escribe row a `sales_agent_llm_call` con `lead_id` + `channel_type` + `reasoning_tokens`.
   - Excepción en repo NO rompe turn.
   - PII sanitizada en payload persistido.
   - Pricing resuelto via shared aliases (Kimi K2.6 → cost correcto, no 0).

2. `tests/modules/sales_agent/observability/test_pii_latam.py`:
   - DNI AR / CURP MX / CUIT AR / RFC MX redactados.
   - UUIDs y números de orden NO redactados.

3. `tests/modules/sales_agent/tools/test_tool_call_dedup.py`:
   - 3 mismas calls → `ANTI_LOOP_DIRECTIVE`.
   - 5 mismas calls → `ToolCallLoopError`.
   - Args distintos no cuentan como dedup.

4. `tests/modules/sales_agent/observability/test_dual_write_parity.py`:
   - Mock turn → ambas tablas pobladas consistentes.
   - Diff calculado por reconciliation worker = 0.

5. `tests/architecture/test_no_pii_in_writes.py`:
   - Todo write a `sales_agent_trace_event` o `sales_agent_llm_call` pasa por `sanitize_payload()`.

6. `tests/architecture/test_callback_handler_best_effort.py`:
   - `SalesAgentCallbackHandler._persist_*` envuelto en try/except + structlog.warning + db.rollback.

7. `tests/admin/test_sales_audit_dual_read.py`:
   - Page renderiza con solo legacy / solo new / ambos.
   - Dedupe por `turn_id` correcto.

---

## Implementación step-by-step

1. Migración Alembic 3 tablas + indexes idempotente. Test en clone DB.
2. Modelos SQLA registrados en `tests/conftest.py::db_engine`.
3. Repos concretos heredan `BaseLLMCallRepo` (S0).
4. `SalesAgentCallbackHandler` heredando `BaseAgentCallbackHandler`.
5. Extender PII patterns LATAM en `shared/.../sanitization.py`.
6. `tool_call_dedup.py` mirror — wire en signal_accumulator.
7. Wire callback handler en `LLMFactory` para sales role.
8. Domain events nuevos + subscribers.
9. Reconciliation worker dual-write (ARQ task hourly, opt-in env).
10. Streamlit admin `/trazas` extender con filtro `agent_kind=sales_agent`.
11. `sales_audit.py` adoptar dual-read pattern.
12. Smoke test live: turn real con webhook Telegram dev → verificar rows.
13. **Paso 11 code review final**: verificar `sales_audit.py` no roto, callers `@trace_node` siguen funcionando hasta cutover.

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Latencia adicional callback | Best-effort + measure <10ms p99. Si excede → cola async. |
| Diff dual-write >1% | Investigar antes cutover. NO drop `@trace_node` hasta verde 4 semanas. |
| PII regex false-positive | Test exhaustivo con UUID/decimales. Keyword guard. |
| Race condition `astream_events` | Verificar en research callback handler funciona en LangGraph 0.3+. |
| Migración rompe DB clone | Raw SQL `IF NOT EXISTS` + reference types existentes. Test en clone antes prod. |
| `tool_call_dedup` agresivo bloquea valid retries | Threshold 3 + hard 5. A/B test logs antes prod. |
| `sales_audit.py` dual-read query slow | Index correcto en ambas tablas. EXPLAIN ANALYZE. |

---

## Tech debt watchpoints

- `@trace_node` → eliminar completo cuando dual-write verde 4 semanas + cutover commit (S6).
- `AgentLogModel` legacy → drop en migración separada post-cutover.
- Si encontrás `print()` en sales_agent paths → fix (debe ser `structlog`).
- Si encontrás `datetime.utcnow()` → fix a `utc_now()`.
- `messages` JSONB en `agent_state_checkpoint` puede tener PII no sanitizada — flag para retention task de S2.
- Si `tool_call_dedup` reusa exacto código copilot → DRY: extraer a shared/agent_observability/tools/.

---

## Ajustes vs plan original

> **2026-04-28**: agregado mirror explícito de `tool_call_dedup.py` (omitido en plan original — emergió de revisión copilot). Agregado plan dual-read para `sales_audit.py`.
