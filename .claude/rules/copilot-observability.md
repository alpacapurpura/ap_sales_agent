# Copilot Observability

Módulo cohesivo: `backend/src/modules/copilot/observability/`. Subscribe vía LangChain callbacks + domain event bus. **Copilot no la invoca**; observability se conecta sola.

> Diseño completo: `docs/domains/copilot/observability-rebuild-2026-04/`. Antes de modificar, leer `ARCHITECTURE.md` + `PRINCIPLES.md`.

## Estructura del módulo

| Subpaquete | Responsabilidad |
|---|---|
| `recording/` | Callback handler LangChain + domain subscribers + sanitization (PII redaction) + turn envelope. |
| `pricing/` | Resolver point-in-time (provider, model, ts) → unit cost + sync diario LiteLLM. |
| `cost/` | Calculator (tokens × unit cost) + FX resolver (Frankfurter passthrough). |
| `persistence/` | Repos para `copilot_llm_call`, `model_pricing_snapshot`, `tenant_billing_config`, `copilot_trace_event`. |
| `reporting/` | `BillingCycleService` + `CostAggregator` + `cycle_window` (math 25-25). |
| `workers/` | ARQ tasks: pricing sync diario, MV refresh hourly, retention diario, cost alert diario. |
| `application/` | Servicios cross-corte (cost_alert_service). |

## Tablas

| Tabla | Quién escribe | Schema doc |
|---|---|---|
| `copilot_llm_call` | `recording/callback_handler.py::on_llm_end` | ARCHITECTURE.md §4.2 |
| `copilot_trace_event` | `recording/callback_handler.py` + `domain_subscribers.py` + `turn_envelope.py` | Migration 059 |
| `model_pricing_snapshot` | `workers/pricing_sync_task.py` | ARCHITECTURE.md §4.2 |
| `tenant_billing_config` | manual (admin SQL hoy) | ARCHITECTURE.md §4.2 |
| `mv_daily_llm_cost_per_tenant` | `workers/aggregate_refresh_task.py` (MV) | Migration 077 |

## Cómo agregar un domain event

1. Definir subclase de `DomainEvent` en `src/modules/copilot/domain/events.py` con classmethod `create(...)`.
2. Agregar literal `EVENT_*` arriba del archivo.
3. Publicar desde el productor via `event_bus.publish(MyEvent.create(...), session=None)` (dispatch inmediato — copilot no tiene transaction "principal" durante stream).
4. Si querés persistirlo a `copilot_trace_event`, agregar handler en `observability/recording/domain_subscribers.py::register_subscribers`. Si NO (ej: telemetría futura), dejá sin subscriber — los eventos son opt-in para consumers.
5. Test: `tests/modules/copilot/domain/test_events.py` cubre la classmethod, `tests/modules/copilot/observability/test_domain_subscribers.py` cubre el handler.

**Prohibido:** pasar `session=db` al `event_bus.publish` desde el orchestrator. Defiere dispatch a `after_commit` de una transacción ambigua.

## Cómo agregar un provider LLM nuevo

**Auto-cubierto.** El callback handler captura `serialized` + `usage_metadata` de cualquier `BaseChatModel` o `BaseLLM` que LangChain invoque vía `RunnableConfig(callbacks=[handler])`. No hay registro manual.

Pricing: el provider tiene que aparecer en el JSON de LiteLLM (`https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json`). El sync diario (`pricing_sync_task.py`) lo trae automático. Si no aparece, el resolver cae a costo 0 — el llm_call row se persiste igual con `cost_usd=0` y `pricing_version_id` apuntando al snapshot vigente.

Si el provider tiene cache pricing especial (ej: prompt cache), agregar las keys `cache_read_input_token_cost` / `cache_creation_input_token_cost` al filter del parser en `pricing/litellm_sync.py` (ya cubre las usuales).

## Cómo modificar pricing manual

Insertar row directo con `source='manual'`:

```sql
-- Cerrar la activa (si existe).
UPDATE model_pricing_snapshot
SET valid_to = NOW()
WHERE provider = 'kimi' AND model = 'kimi-k2.6' AND valid_to IS NULL;

-- Abrir la nueva.
INSERT INTO model_pricing_snapshot (
    provider, model, input_cost_per_token, output_cost_per_token,
    source, valid_from, raw_payload
) VALUES (
    'kimi', 'kimi-k2.6',
    0.00000040, 0.00000200,
    'manual', NOW(), '{"reason": "...", "operator": "..."}'::jsonb
);
```

El sync diario respeta rows `source='manual'` (no las sobreescribe).

## Retention

Default 90 días para `copilot_trace_event` (rows `status='error'` se preservan), 365 días para `copilot_llm_call` (auditoría billing). Configurable:

```bash
# .env
COPILOT_TRACE_RETENTION_DAYS=180        # default 90
COPILOT_LLM_CALL_RETENTION_DAYS=730     # default 365
```

Worker `purge_expired_trace_rows` corre diario a las 04:00 UTC. Best-effort, structlog warning si falla.

## PII redaction

Sincrónico, regex-only en `recording/sanitization.py`. Se aplica automático cada vez que se llama `sanitize_payload(...)` (callback handler, turn envelope, domain subscribers). Cubre:

- Email (`juan@x.com` → `j***@x.com`)
- Phones LATAM con `+country` o separadores (`+51 999 888 777` → `+51 [REDACTED_PHONE]`)
- Phones bare 8-12 dígitos solo cuando está precedido por keyword (numero/cel/tel/whatsapp/llámame/contacto). Sin keyword no se enmascara para evitar false-positives en UUIDs/decimals.
- API tokens: `sk-...`, `sk-ant-api...`, `xai-...`, `gsk_...` → `[REDACTED_TOKEN]`.

**No hay Presidio sincrónico** — overhead de spaCy NER es demasiado para el hot path. Worker async post-write con Presidio es deferred-debt.

## Best-effort writes (no negociable)

Toda escritura de observability va envuelta en try/except + structlog warning. Una excepción NO debe romper un turn del copilot. Pattern:

```python
try:
    repo.add(...)
except Exception as exc:
    logger.warning("obs_write_failed", error=str(exc))
    db.rollback()
```

Validado por `test_atomic_switch.py::test_observability_failure_does_not_break_turn`.

## Tenant isolation

Todas las queries en `persistence/` y `reporting/` filtran `tenant_id`. Las del workers son cross-tenant pero NO leakean data row-level (operan a nivel agregado o por tenant_id en loop).

Los índices están armados para que ningún tenant scan full table:

- `ix_llm_call_tenant_day` (tenant_id, occurred_on)
- `ix_llm_call_turn` (turn_id) — global, pero `turn_id` ya implica tenant
- `ix_pricing_active` (provider, model) WHERE valid_to IS NULL — global por diseño (reference data)

## Costo del callback handler

<10ms p99 medido contra `tests/modules/copilot/observability/test_e2e_isolated.py`. Si una sub-routine empieza a tardar más:

1. Verificar PII regex (usa `re.compile` cacheado al import).
2. Verificar pricing resolver — usa cache in-memory keyed por `(provider, model)`.
3. Verificar FX resolver — Frankfurter API call NO debería ocurrir en el hot path; el resolver cachea por TTL.

## Workers ARQ

| Task | Schedule | Función | Best-effort |
|---|---|---|---|
| `sync_litellm_pricing` | daily 03:00 UTC | Sync LiteLLM JSON → `model_pricing_snapshot` | Sí |
| `refresh_daily_cost_mv` | hourly :05 | `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_llm_cost_per_tenant` | Sí |
| `purge_expired_trace_rows` | daily 04:00 UTC | DELETE rows pasada retención | Sí |
| `run_cost_alerts` | daily 12:00 UTC | Walk `tenant_billing_config` con threshold > 0; structlog warning si cycle cost lo excede | Sí |

Registradas en `backend/src/workers/settings.py` (en `WorkerSettings.functions`, `SchedulerSettings.functions` y `SchedulerSettings.cron_jobs`).

## Prohibido

- ❌ Llamar `recorder.record(...)` directo desde `chat.py` o tools. Usar `event_bus.publish(...)` para domain events; el callback handler captura LLM/tool/chain calls sin acoplar.
- ❌ Hardcodear precios en código (`_PRICING = {...}`). Pricing vive en `model_pricing_snapshot`. Sync diario actualiza.
- ❌ Bypass del callback handler para "ahorrar latencia". Best-effort y rapidez son compatibles (<10ms p99).
- ❌ Persistir PII sin pasar por `sanitize_payload(...)`. Aún si pensás que el campo "no puede tener PII", llamálo igual.
- ❌ Borrar rows de `copilot_llm_call` salvo via worker `retention_task`. Las queries billing dependen de la inmutabilidad event-sourced.
- ❌ Cambiar el shape del `_legacy_compat_keys` en `turn_envelope._write_turn_end` sin migrar antes los consumers que aún leen el JSONB (`/copilot-routing` ya migró; `/trazas` ya migró; cualquier consumer FE custom debe migrar antes).
- ❌ Modificar el callback handler para acoplarlo al stream de LangGraph (`astream_events`). El callback handler es **separado** del stream de eventos del orchestrator — sobrevive a cambios en `astream_events` versioning.

## Anchor

- Cualquier query de costo / billing / cycle → `copilot_llm_call` o `mv_daily_llm_cost_per_tenant`.
- Cualquier query de timeline / trace → `copilot_trace_event`.
- Cualquier query de routing → `copilot_routing_log`.
- Cualquier query de pricing histórico → `model_pricing_snapshot`.
- Cualquier query de billing config → `tenant_billing_config`.
- Dashboard live: `/costo-copilot` (Streamlit admin).

Future Claude: si el módulo necesita una capacidad nueva (ej: forecast de costo, anomaly detection), agregá sub-paquete bajo `observability/`. **Nunca** colocar lógica en `application/orchestrator/` o `tools/`.
