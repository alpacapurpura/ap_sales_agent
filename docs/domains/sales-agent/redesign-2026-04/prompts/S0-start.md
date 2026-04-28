# Handoff prompt · S0 start

> **Refinado al cierre de S00 (codebase audit + cleanup deprecated).**

---

```
Continuamos redesign sales_agent.

📋 Plan maestro: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S0 — Extract shared/agent_observability/ (foundation)
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S0-shared-observability-extract.md
📝 Aprendizajes: docs/domains/sales-agent/redesign-2026-04/learnings/S00-codebase-audit-and-cleanup.md
🗺️ Audit map: docs/domains/sales-agent/redesign-2026-04/audit/sales-agent-current-state.md

CONTEXTO post-S00 (cerrado 2026-04-28):
- Cleanup ejecutado: borrado route /sales/resumen + 6 componentes orphan (SalesDashboard, ConversionCommandCenter, SalesLane, AgendaLane, OpportunityLane, SalesInboxSheet). Sidebar consolidado a 3 entries (Studio/Contactos/Inscripciones). sales/page.tsx redirige a /sales/studio/inbox. types/sales-studio.ts reducido a PaymentGatewayConfig. registry-sales.ts purgado de 6 entries orphan.
- Audit map persistido: docs/domains/sales-agent/redesign-2026-04/audit/sales-agent-current-state.md (10 secciones: callers FE→BE, BE imports, DB tables, endpoints, admin reads, eventos, workers, cohesion/coupling heatmap, orphans, §3 protected verification).
- Admin migration plan listo: docs/domains/sales-agent/redesign-2026-04/audit/admin-migration-plan.md (sales_audit.py shape + dual-read S1 + nuevas pages S2/S4/S10 + _shared.py extensions).
- Spanish neutro voseo scan: 0 hits sales_agent + closer-studio (baseline limpia).
- Branch: development limpio. 3 commits ahead de origin/development (sync con main).
- Último commit S00: 066ea218 — chore(sales-agent-redesign-s00): cleanup deprecated /sales/resumen + audit map.
- Tests S00 activos: tests/architecture/test_no_resumen_deprecated_references.py (BE arch ratchet) + frontend/e2e/specs/smoke/sales-routes.smoke.spec.ts.

DEUDA DETECTADA POR S00 (revisar 05-tech-debt-log.md):
- DEFERRED-S0: 4 orphans pre-existentes en features/sales/components/dashboard/{ActivityFeedWidget,CalendarWidget}.tsx + overlay/{AppointmentSheet,AvailabilityModal}.tsx. NO consecuencia de S00 — no eliminados por scope strict. Si tocás archivos vecinos en S0, considerar borrarlos.
- DEFERRED-S0: knowledge_builder.py (217 LOC) lazy-imports brand+offer cross-module. Si formalizás ports, este archivo se simplifica.
- DEFERRED-S0: lazy imports brand+offer en style_anchor_retriever.py + business_repository.py — al borde de arch test. Evaluar si necesitan ports formales.
- DEFERRED-S1: sales_audit.py legacy reads (AgentTrace + LLMLogModel). Plan dual-read en audit/admin-migration-plan.md §2.
- DEFERRED-post-S6: chat.py (1082 LOC), closer_studio_service.py (623 LOC), semantic_router.py (328 LOC) — refactors cohesión candidate.

REALIDAD copilot (post commits abril 2026 — IMPORTANTE):
- copilot/observability/ ya tiene: ObservabilityCallbackHandler (Phase 2 atomic switch), copilot_llm_call, copilot_trace_event, model_pricing_snapshot, tenant_billing_config, mv_daily_llm_cost_per_tenant, pricing/aliases.py (Kimi K2.6/K2.5 → LiteLLM), retention worker, cost alert worker.
- ChatModelSpec native (commit c60197fa) en shared/infrastructure/llm/providers/_chat_model_resolver.py.
- Multi-provider per-role: AI_PROVIDER_{NANO,FAST,REASONING,AGENT,VISION,EMBEDDING} env vars.
- providers/_kwargs.py SSoT kwarg translation + reasoning-budget trap fix.
- Migration 073 agregó tenant.deepseek_api_key/kimi_api_key/dashscope_api_key.
- tool_call_dedup.py per-turn anti-loop (commit 3aab4002).
- F8 cache_boundary cerrado (slot order, ≥1024 prefix, NANO classifier).
- /copilot-routing admin muestra provider library provenance + runaway output alerts.

OBJETIVO S0: extraer observability de copilot a src/shared/agent_observability/ parametrizada por agent_kind. Zero behavior change copilot. Foundation para S1+.

PROTOCOLO obligatorio (10 pasos + Paso 11 code review final):

1. Lee, en orden:
   - README.md
   - 00-vision-and-objectives.md (§3)
   - 01-master-plan.md
   - 02-architecture-target.md (revisar §1, §2 con realidad post-abril 2026)
   - 03-phase-protocol.md (10 pasos + Paso 11 code review final)
   - 04-principles.md
   - 05-tech-debt-log.md
   - 06-glossary.md
   - learnings/S00-*.md
   - audit/sales-agent-current-state.md
   - audit/admin-migration-plan.md
   - phases/S0-shared-observability-extract.md
   - .claude/rules/copilot-observability.md
   - .claude/rules/copilot-resilience.md
   - .claude/rules/backend-ddd.md
   - .claude/rules/architectural-fitness.md

2. Research mandate S0:
   - WebSearch: LangChain BaseCallbackHandler best practices 2026, Python shared module DDD, LiteLLM JSON schema 2026.
   - Tessl: tessl__langgraph, tessl__fastapi.
   - Lectura crítica: copilot/observability/ entero (recording/, pricing/, cost/, persistence/, reporting/, workers/), pricing/aliases.py.

3. Confirmar/ajustar plan post-research. Si copilot/observability/ ya está más shared-ready de lo esperado → recortar S0 scope y documentar en "Ajustes vs plan original".

4. TaskCreate granular.

5. TDD:
   - RED tests: BaseAgentCallbackHandler invariants, sanitization invariants, pricing resolver, shared purity.
   - Regression copilot: tests existentes verdes sin tocar lógica.

6. Quality gates nativos (NUNCA docker exec):
   - cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   - cd backend && .venv/bin/ruff format --check src/ tests/
   - cd backend && .venv/bin/pytest tests/modules/copilot/ tests/architecture/ -x -q
   - cd backend && .venv/bin/pytest tests/shared/ -x -q (si tests creados)

7. Verificación funcional:
   - Smoke copilot: turn real → trazas siguen escribiendo a copilot_trace_event y copilot_llm_call.
   - §3 sigue funcionando — closer studio + buffer + webhooks no se tocan.
   - Streamlit /trazas + /copilot-routing + /costo-copilot renderean.

8. Tech debt log si detectaste durante extract.

9. Aprendizajes: learnings/S0-shared-observability-extract.md (denso, accionable).

10. Prompt siguiente: prompts/S1-start.md refinado con contexto fresco.

11. PASO 11 — Code review final (ver 03-phase-protocol.md §11):
    - Callers no rotos (grep + verificar).
    - Cohesión: cada subpaquete responsabilidad única.
    - Acoplamiento: shared no importa modules/.
    - Skill simplify sobre archivos modificados.
    - Cleanup oportunista (imports muertos, types).
    - Tests módulo afectado verdes.
    - Admin smoke (tests/admin/test_admin_smoke.py).

12. Commit conventional + push:
    - feat(sales-agent-redesign-s0): extract shared/agent_observability/
    - Cuerpo: menciona learning doc + handoff prompt.
    - Stage por nombre. NUNCA git add -A.

PRINCIPIOS NO NEGOCIABLES (04-principles.md):
- GoF + DRY + alta cohesión + bajo acoplamiento.
- Template Method en BaseAgentCallbackHandler. Strategy en PII regex pack. Repository abstract.
- Anti-parche: si copilot/observability/ ya está shared-ready → adoptar via re-export, no duplicar.
- TDD obligatorio.
- Best-effort observability (try/except + structlog warning + db.rollback).
- Native-first dev.
- response_model= en endpoints.
- Stage por nombre en commits.
- §3 NO se toca.

Empieza ahora con paso 1.
```
