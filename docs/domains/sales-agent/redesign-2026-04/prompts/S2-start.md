# Handoff prompt · S2 start

> **Refinado al cierre de S1 (2026-04-28).** Pega esto al iniciar conversación nueva.

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S2 — Cost guardrails + cycle 25-25 cross-agent
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S2-cost-guardrails.md
📝 Aprendizajes S1: docs/domains/sales-agent/redesign-2026-04/learnings/S1-sales-agent-observability-parity.md

CONTEXTO post-S1 (cerrado 2026-04-28):
- S1 cerrada: tablas sales_agent_llm_call/_trace_event/_routing_log creadas (migration 078 idempotente).
- SalesAgentCallbackHandler activo en orchestrator/chat.py:868 con `config={"callbacks":[handler]}` al ainvoke.
- Subgraph forwarding: orchestrator/graph.py::sales_agent_node(state, config) → sales_app.invoke(state, config=config).
- PII LATAM activa día 1: DNI/CURP/CUIT/RFC/CC/RUC/CPF/CVV/tarjeta con keyword guards en shared/agent_observability/recording/sanitization.py.
- Mirror tool_call_dedup en sales_agent/application/orchestrator/tool_call_dedup.py + wired en node_tool_executor; env vars `SALES_AGENT_TOOL_CALL_DEDUP_THRESHOLD/HARD_LIMIT`.
- 4 domain events (LeadQualified/ObjectionHandled/StageTransitioned/ToolLoopDetected) con subscribers persistiendo a sales_agent_trace_event con event_type='domain_event'.
- Reconciliation worker `run_sales_agent_dual_write_reconcile` registrado en WorkerSettings.functions + SchedulerSettings.cron_jobs (minute=25). Off por env-flag `SALES_AGENT_DUAL_WRITE_RECONCILE=1`.
- Dual-write con @trace_node: ACTIVO. 4-week observation window arrancando 2026-04-28. Cutover criterion: diff <1% per-tenant.
- sales_audit.py dual-read: timeline merge + sidebar prefer event-sourced + clear_user_history extends sales_agent_* tables.
- Branch: development limpio. Último commit S1: {HASH — pin al cerrar}.

HOOKS LISTOS PARA S2:
- model_pricing_snapshot + tenant_billing_config son cross-agent (post-S0). NO duplicar.
- BillingCycleService en shared/agent_observability/reporting/billing_cycle_service.py — ya cross-agent capable, S2 lo invoca con tabla parametrizada.
- cost_aggregator + cost_alert_service en copilot/observability/ siguen copilot-only (SQL hardcoded). S2 abstrae.
- 4 architectural fitness tests S1 vivos (test_sales_agent_observability_invariants.py + master_data USD allowlist con sales handler). S2 agrega mv_daily_v2 invariants si aplican.
- Reconciliation worker es vital — NO desactivar antes de cutover S6.

DEUDA REMANENTE para S2:
- DEFERRED-S2: cost_aggregator/retention_task/aggregate_refresh_task SQL hardcoded `copilot_*`. S2 los abstrae con tabla parametrizada o crea worker cross-agent.
- DEFERRED-S2: `mv_daily_llm_cost_per_tenant_v2` UNION ALL cross-agent con discriminator `agent_kind`. Migration idempotente.
- DEFERRED-S2: `costo-agentes` Streamlit page — mirror de costo-copilot. PageSpec + thin wrapper + module render. Lee MV cross-agent. Implementar `_shared.render_agent_kind_selector()` + `_shared.query_cross_agent_costs()` per admin-migration-plan.md §4.
- DEFERRED-S2: cost alert breakdown per agent_kind. Default threshold per-tenant ya en tenant_billing_config.cost_alert_threshold_usd (cross-agent).
- DEFERRED-S2: subscribers crean SessionLocal() per-event — si latency emerge, threadlocal o context-bound session.
- DEFERRED-post-S6: SalesAgentCallbackHandler 6-callbacks duplica copilot ~250 LOC. Lift al BaseAgentCallbackHandler base cuando copilot retrofitee. Pattern: on_* callbacks abstract base + _persist_*_row overrides per-agent.
- DEFERRED-post-S6: drop @trace_node + current_trace_id ContextVar + agent_traces/llm_logs tablas (depende de cutover dual-write verde).
- DEFERRED-S6: docs (tech-debt-log + admin-migration-plan) mencionan `agent_log_model.py` que no existe — la tabla legacy real es `llm_logs` con clase `LLMLog` en `llm_log_model.py`. Corregir nombres durante cleanup S6.

PROTOCOLO:

1. Lee:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - 00-vision-and-objectives.md (§3 lo que NO se toca)
   - 01-master-plan.md
   - 02-architecture-target.md (§2 tablas DB + §3.x contratos)
   - 03-phase-protocol.md (10 + Paso 11 code review)
   - 04-principles.md
   - 05-tech-debt-log.md (entradas DEFERRED-S2)
   - learnings/S0-*.md + learnings/S1-*.md
   - phases/S2-cost-guardrails.md
   - audit/sales-agent-current-state.md
   - audit/admin-migration-plan.md (§3 costo-agentes + §4 _shared extensions)
   - .claude/rules/copilot-observability.md (best-effort patterns + workers section)
   - .claude/rules/admin-panel.md (smoke tests)
   - .claude/rules/backend-migrations.md (idempotencia)

2. Research mandate S2:
   - Postgres MATERIALIZED VIEW UNION ALL + REFRESH CONCURRENTLY 2026 (require unique index for concurrent)
   - Cost alert UX SaaS multi-product (breakdown vs total threshold)
   - LiteLLM retention + tier pricing >200k tokens (S2 deferred-debt si aparece)
   - PII redaction async post-write workers (Presidio + spaCy NER) — Phase 3 deferred-debt mention en research

3. Documenta hallazgos research en phases/S2-*.md sección "Hallazgos research".

4. TaskCreate granular para los pasos de implementación.

5. TDD: tests RED primero. Foco crítico:
   - mv_daily_v2 UNION ALL test (insert into both tables → MV refresh → query returns both agent_kinds).
   - cost_aggregator cross-agent parametrize test (factory por agent_kind).
   - cost_alert breakdown test (alert dispara cuando suma cross-agent excede threshold).

6. Migración Alembic 079 (mv_daily_v2 + cost_alert_threshold backfill si aplica) idempotente. Test en clone DB.

7. Quality gates nativos:
   - ruff check + format --check
   - pytest tests/modules/sales_agent/ tests/modules/copilot/observability/ tests/shared/agent_observability/ tests/architecture/ tests/admin/
   - alembic upgrade head en clone DB

8. Verificación funcional:
   - Streamlit `/costo-agentes` renderiza tabs por agent_kind con cost USD + tenant currency.
   - Cost alert structlog warning dispara con breakdown copilot vs sales_agent.
   - Reconciliation worker S1 sigue running OK (no regresión).
   - §3 NO roto: closer studio + buffer + follow-up + frozen detection.

9. Tech debt log: si encontrás print() / datetime.utcnow() durante S2 audit → fix + log.

10. Cierre:
    - learnings/S2-*.md (denso, accionable).
    - prompts/S3-start.md refinado con: ¿costo-agentes en producción? ¿cross-agent MV refresh hourly OK? ¿reconciliation diff <1%?
    - Mark FIXED entradas DEFERRED-S2 que se hayan resuelto.

11. Commit: `feat(sales-agent-redesign-s2): cost guardrails cross-agent + costo-agentes admin`

PRINCIPIOS:
- TDD: tests primero.
- Anti-parche: cost_aggregator hoy es copilot-only por SQL hardcoded — S2 abstrae cleanly, no patches if-else por agent_kind.
- Best-effort: workers y MV refresh wrapped try/except + structlog.warning.
- Tenant isolation: every query filter tenant_id.
- Stage por nombre en commits.
- Spanish neutro LATAM en banners y user-facing strings (sin voseo).

Empieza con paso 1.
```
