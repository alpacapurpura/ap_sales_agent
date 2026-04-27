# Handoff prompt · S2 start

> **Refinado al cierre de S1.** Pega esto al iniciar conversación nueva.

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S2 — Cost guardrails + cycle 25-25 cross-agent
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S2-cost-guardrails.md
📝 Aprendizajes S1: docs/domains/sales-agent/redesign-2026-04/learnings/S1-sales-agent-observability-parity.md

CONTEXTO (refinar al cierre de S1):
- S1 cerrada: SalesAgentCallbackHandler activo, sales_agent_llm_call/trace_event/routing_log poblándose. PII sanitization day-1.
- Dual-write con @trace_node: {STATUS — activo / cutover ejecutado}
- Diff dual-write: {METRIC}
- Branch: development limpio.
- Último commit S1: {HASH}
- Hooks: BaseAgentCallbackHandler completo, model_pricing_snapshot poblado, sales_agent_llm_call.cost_usd populated.
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 (entradas DEFERRED-S2) + learnings/S1-* + phases/S2-*.
2. Research mandate: Postgres MV UNION ALL CONCURRENTLY 2026, cost alert UX SaaS multi-product, LiteLLM retention.
3. TaskCreate.
4. TDD: tests cross-agent aggregation, MV refresh test, breakdown alert test.
5. Migración: nueva MV con UNION ALL + unique index. Drop+create idempotente.
6. Quality gates nativos.
7. Verificación: Streamlit /costo-agentes renderiza tabs. Cost alert dispara con breakdown.
8. §3 sigue funcionando.
9. Tech debt log.
10. learnings/S2-* + prompts/S3-start.md refinado.

PRINCIPIOS: GoF, DRY, TDD, anti-parche, tenant isolation, native-first.

Empieza con paso 1.
```
