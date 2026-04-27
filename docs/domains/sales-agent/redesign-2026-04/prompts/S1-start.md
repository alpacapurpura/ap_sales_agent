# Handoff prompt · S1 start

> **Refinado al cierre de S0 con contexto fresco.** Pega esto al iniciar conversación nueva.

---

```
Continuamos el redesign de sales_agent.

📋 Plan maestro: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S1 — Sales agent observability parity + PII sanitization
📂 Doc de la fase: docs/domains/sales-agent/redesign-2026-04/phases/S1-sales-agent-observability-parity.md
📝 Aprendizajes S0: docs/domains/sales-agent/redesign-2026-04/learnings/S0-shared-observability-extract.md

CONTEXTO:
- S0 cerrada: src/shared/agent_observability/ existe con sub-paquetes recording/, pricing/, cost/, persistence/, reporting/, workers/. BaseAgentCallbackHandler abstract. Copilot consume desde shared sin behavior change.
- Branch: development limpio.
- Último commit S0: {COMPLETAR AL CIERRE DE S0}
- Hooks listos para S1: {COMPLETAR AL CIERRE DE S0 — ej: BaseAgentCallbackHandler.{methods}, BaseLLMCallRepo, etc.}
- Tech debt en radar: {COMPLETAR}

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
