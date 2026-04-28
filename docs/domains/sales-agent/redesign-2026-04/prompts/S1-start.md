# Handoff prompt · S1 start

> **Refinado al cierre de S0 con contexto fresco.** Pega esto al iniciar conversación nueva.

---

```
Continuamos el redesign de sales_agent.

📋 Plan maestro: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S1 — Sales agent observability parity + PII sanitization
📂 Doc de la fase: docs/domains/sales-agent/redesign-2026-04/phases/S1-sales-agent-observability-parity.md
📝 Aprendizajes S0: docs/domains/sales-agent/redesign-2026-04/learnings/S0-shared-observability-extract.md

CONTEXTO post-S0 (cerrado 2026-04-28):
- src/shared/agent_observability/ creado con 6 sub-paquetes:
  * recording/ → sanitization.py + base_callback_handler.py (BaseAgentCallbackHandler ABC)
  * cost/ → calculator.py + fx_resolver.py
  * pricing/ → aliases.py (Kimi K2.6/K2.5) + resolver.py + litellm_sync.py
  * persistence/ → pricing_snapshot_repository.py + tenant_billing_config_repository.py + base_llm_call_repo.py (Protocol) + base_trace_event_repo.py (Protocol) + models/{pricing_snapshot_model, tenant_billing_config_model}
  * reporting/ → cycle_window.py + billing_cycle_service.py
  * workers/ → pricing_sync_task.py
- Quedan en copilot/observability/ (acoplados a tablas copilot_*, S1/S2 abstracta):
  * recording/{callback_handler, turn_envelope, domain_subscribers}
  * persistence/{llm_call_repository, trace_event_repository, models/llm_call_model}
  * reporting/cost_aggregator
  * application/cost_alert_service
  * workers/{retention_task, aggregate_refresh_task, cost_alert_task}
- Arch test ratchet activo: tests/architecture/test_shared_agent_observability_purity.py (KNOWN_VIOLATIONS vacío) — bloquea import de src.modules.* desde shared/agent_observability/.
- Tests verdes: 2522 (copilot/ + arch + admin + shared). Ruff 0 errors. Format check ok.
- Branch: development limpio. Último commit S0: {pendiente — generado por commit final}.
- Workers/settings.py registra sync_litellm_pricing desde shared/.
- Streamlit /costo-copilot lee de shared/agent_observability/reporting/.

DEUDA REMANENTE para S1:
- DEFERRED-S1: PII sanitization en sales_agent (HIGH) — base regex en shared/agent_observability/recording/sanitization.py incluye email, phones LATAM, API tokens. S1 extiende con DNI/CURP/CUIT/RFC/CVV/nro tarjeta agregando al tuple `_PHONE_RES`/nuevo `_PII_RES` sin tocar `redact_value` walker.
- DEFERRED-S1: retention 90d trace (HIGH) — copilot/observability/workers/retention_task.py SQL hardcoded copilot_*. S1 puede agregar entries a la SQL DELETE para sales_agent_*, o S2 abstraer cross-agent.
- DEFERRED-S1: sales_audit.py dual-read (HIGH) — plan completo en audit/admin-migration-plan.md §2. Window 4 semanas.
- DEFERRED-S1: schema admin sidebar "Ver Último Estado" — debe poblar desde sales_agent_trace_event con shape compat (`_legacy_compat_keys` projection es opción).
- DEFERRED-post-S6: chat.py 1082 LOC, closer_studio_service.py 623 LOC, semantic_router.py 328 LOC.
- DEFERRED-S0 → DEFERRED-post-S6: knowledge_builder.py 217 LOC con lazy imports brand+offer cross-module.

HOOKS LISTOS PARA S1:
- BaseAgentCallbackHandler abstract: src/shared/agent_observability/recording/base_callback_handler.py — métodos abstract `_persist_llm_call_row` + `_persist_trace_event_row` aceptan `**agent_specific` para lead_id/channel_type.
- BaseLLMCallRepoProtocol + BaseTraceEventRepoProtocol: src/shared/agent_observability/persistence/{base_llm_call_repo, base_trace_event_repo}.py — structural typing, sync/async session válidos.
- Copilot ObservabilityCallbackHandler NO hereda aún — S1 retrofitea ambos handlers en mismo sprint cuando hay 2 consumers.
- pricing/aliases.py PROVIDER_MODEL_ALIASES dict — sales_agent agrega entries sin tocar copilot.
- Audit map persistido: docs/domains/sales-agent/redesign-2026-04/audit/sales-agent-current-state.md (re-leer §2 cross-module imports + §10 §3 protected).
- Admin migration plan: docs/domains/sales-agent/redesign-2026-04/audit/admin-migration-plan.md.

PROTOCOLO:

1. Lee:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - 00-vision-and-objectives.md (§3)
   - 01-master-plan.md
   - 02-architecture-target.md (revisar §2 tablas DB)
   - 03-phase-protocol.md
   - 04-principles.md
   - 05-tech-debt-log.md (entradas DEFERRED-S1: PII sanitization + retention)
   - learnings/S0-*.md
   - phases/S1-sales-agent-observability-parity.md (entera)
   - .claude/rules/copilot-observability.md
   - .claude/rules/backend-migrations.md (idempotencia mandatoria)
   - .claude/rules/copilot-resilience.md (best-effort patterns)

2. Research mandate S1:
   - LATAM PII regex DNI/CURP/CUIT/RFC 2026
   - LangGraph callback handler StateGraph node-level
   - Dual-write observability migration patterns
   - Mercado Pago payment link PII sensitivity
   Tessl: tessl__langgraph, tessl__fastapi.
   Lectura: sales_agent infrastructure/monitoring/tracing.py + agent_state_checkpoint + chat.py + graph.py.

3. Documenta hallazgos research en phases/S1-*.md sección "Hallazgos research".

4. TaskCreate granular para los pasos de implementación.

5. TDD: tests RED primero. Foco crítico:
   - PII sanitization tests (regex LATAM completa) ANTES de cualquier write.
   - Best-effort handler test (excepción NO rompe turn).
   - Dual-write parity test.

6. Migración Alembic 3 tablas (sales_agent_llm_call, sales_agent_trace_event, sales_agent_routing_log) idempotente. Test en clone DB ANTES de prod.

7. Quality gates nativos:
   - ruff check + format --check
   - pytest tests/modules/sales_agent/ tests/shared/ tests/architecture/
   - alembic upgrade head en clone DB

8. Verificación funcional:
   - Smoke webhook real (Telegram dev) → turn ejecuta → rows en sales_agent_llm_call + sales_agent_trace_event.
   - PII redactada visible en payload JSONB.
   - §3 NO roto: closer studio + buffer + follow-up + frozen detection.

9. Tech debt log:
   - PII sanitization activación = mark FIXED entry [HIGH] del log.
   - Si encontras print(), datetime.utcnow() durante review → fix + log.
   - Bug ajeno: validá real → fix root cause SI cabe en scope.

10. Cierre:
    - learnings/S1-*.md (denso).
    - prompts/S2-start.md refinado con: ¿dual-write reconciliation worker on? ¿Streamlit /trazas extendido? ¿hooks listos para S2?

11. Commit: feat(sales-agent-redesign-s1): callback handler + dual-write + PII sanitization

PRINCIPIOS:
- TDD: PII tests SIEMPRE primero.
- Anti-parche: si callback handler captura algo que @trace_node no → investigar root cause antes de "ajustar".
- Best-effort: try/except + structlog.warning + db.rollback en TODOS los writes obs.
- Tenant isolation: every query filtra tenant_id.
- Stage por nombre en commits.

Empieza con paso 1.
```
