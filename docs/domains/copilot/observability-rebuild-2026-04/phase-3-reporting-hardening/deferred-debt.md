# Phase 3 — Deferred Debt

> Items descubiertos que NO entraron al alcance de Fase 3. Como esta es la
> última fase del rebuild, los items relevantes están movidos a
> `docs/mejoras-proceso/to-do.md` (regla 12 de CLAUDE.md), no a una "Fase 4".

---

## Items de Fase 3 NO completados

(Todos los tasks T3.1–T3.14 cerrados. Completion checklist verificada en T3.14.)

---

## Items movidos a `docs/mejoras-proceso/to-do.md`

Listados en `docs/mejoras-proceso/to-do.md` con prefijo `[copilot-obs]`:

- **PII redaction async con Presidio + spaCy `es_core_news_md`.** Cubre 100% del PII de texto libre (nombres, direcciones LATAM) que el regex no toca. No se incluyó porque instalar Presidio agrega ~600MB y la latencia `es_core_news_md` no está medida en 2026 — el callback handler corre en el hot path SSE y necesita <10ms. Implementar como worker ARQ post-write que lee `copilot_trace_event` rows con texto libre, aplica Presidio, y reescribe `data` JSONB. Defer hasta que haya un caso real reportado de PII no redactado.
- **Email / Slack delivery para cost alerts.** Hoy `cost_alert_threshold_exceeded` es solo structlog warning. Para llegar a humanos hace falta infra de email transaccional o webhook Slack que el repo aún no tiene. Implementar cuando llegue el primer ticket de "no me enteré que un tenant superó su quota".
- **Bootstrap automático de `tenant_billing_config` para tenants nuevos.** Hoy son 11 tenants × 0 rows; cuando se crea uno nuevo, queda sin config y cae a defaults. Considerar agregar un trigger DDL o un hook al onboarding que inserte la row default 25 / USD / frankfurter.
- **Test arch: meta-guard "every `*_*_task.py` has matching test_*.py"** para asegurar que cualquier worker nuevo del observability módulo tiene cobertura. Diferido — patrón emergente, agregar cuando el 2do worker olvide el test.
- **`/trazas`: borrar `_legacy_compat_keys` del JSONB de `turn_end` cuando los consumers internos terminen de migrar.** Phase 2 dejó las keys (`model`, `prompt_tokens`, `completion_tokens`, …) por compat. Phase 3 ya migró `/trazas` (lee de `copilot_llm_call` por span_id) y `/copilot-routing` (lee `copilot_llm_call` directo). Si nadie más los lee, borrarlas en una limpieza posterior.

---

## Mejoras post-rebuild sugeridas (opcionales, no urgentes)

- **Currency conversion para PEN/COP.** Frankfurter no las cubre; hoy tenants en esos países caen al passthrough USD (`fx_rate_source='passthrough'`). Si llega un cliente PE/CO real, integrar `exchangerate.host` o similar como fallback de Frankfurter.
- **Per-tenant cycle anchor override.** Hoy todos los tenants caen a anchor 25; el dashboard ya respeta cualquier override que el admin escriba directo en SQL. Falta UI para que el operador edite `tenant_billing_config.billing_cycle_anchor_day` desde Streamlit. Diferido hasta que haya un caso real (cliente nicho con ciclo distinto al 25-25 estándar Nicolify).
- **Sampling para `copilot_trace_event` en producción de alto volumen.** Si el volumen explota >10M rows/mes, considerar guardar solo 1 de cada N rows para event types ruidosos (`node_enter`/`node_exit`) — los `llm_call` y `tool_call` son el corazón del debug y conviene mantenerlos al 100%.
- **`copilot_llm_call.parent_span_id` poblado de verdad.** Hoy queda NULL; Phase 1 dejó la columna pero nunca el callback handler la rellena. Útil para reconstruir el árbol completo en `/trazas` cuando un turn invoca subagentes vía `task` tool. Phase 2 deferred-debt ya lo tenía listado.
- **Costo dashboard: filtro por modelo.** Comando Central agrupa por tenant; agregar tab "Por modelo cross-tenant" daría visibilidad de qué modelo es el dominante en gasto del producto. Trivial — `agg.tenants_summary` ya tiene los datos, solo falta otro group-by.

---

## Notas para futuras evoluciones

- **¿Cuándo migrar a TimescaleDB?** Trigger: cuando volumen `copilot_llm_call` supere ~5M rows/mes y el `REFRESH MATERIALIZED VIEW CONCURRENTLY` empiece a tardar >30s.
- **¿Cuándo adoptar Langfuse/LangSmith hosted?** Trigger: cuando el equipo crezca y necesite UI compartida de eval/comparación de prompts. Hoy el dashboard Streamlit + `/trazas` cubren al operador único.
- **¿Cuándo exportar a OTel collector?** Trigger: cuando otro módulo del repo adopte OTel y haya valor en consolidar. El schema actual ya es OTel-shape compatible (`provider`, `model_requested`, `input_tokens`, etc.); el rename a `gen_ai.*` es trivial cuando la spec OTel GenAI promueva a Stable.
- **¿Cuándo borrar el `_legacy_compat_keys`?** Después de pasar prod por al menos 30 días sin que un solo consumer FE custom los lea — verificar via `git grep` antes de borrar.
