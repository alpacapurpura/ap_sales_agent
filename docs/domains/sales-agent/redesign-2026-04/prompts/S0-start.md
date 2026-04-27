# Handoff prompt · S0 start

> **Pega esto al iniciar conversación nueva para arrancar S0.**

---

```
Iniciamos el redesign arquitectónico de sales_agent → madurez copilot + capacidades nuevas.

📋 Plan maestro: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S0 — Extract shared/agent_observability/ (foundation)
📂 Doc de la fase: docs/domains/sales-agent/redesign-2026-04/phases/S0-shared-observability-extract.md

CONTEXTO:
- Es la primera fase del plan de 11 fases.
- Objetivo: extraer la capa de observabilidad de copilot/observability/ a src/shared/agent_observability/ parametrizada por agent_kind.
- Zero behavior change en copilot (todos los tests existentes deben pasar sin tocar lógica).
- Foundation para que sales_agent (S1+) consuma el mismo substrate.
- Branch: development limpio.

PROTOCOLO obligatorio:

1. Lee, en este orden:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - docs/domains/sales-agent/redesign-2026-04/00-vision-and-objectives.md (presta atención a §3 lo que NO se toca)
   - docs/domains/sales-agent/redesign-2026-04/01-master-plan.md (DAG de fases)
   - docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md
   - docs/domains/sales-agent/redesign-2026-04/03-phase-protocol.md (los 9 pasos)
   - docs/domains/sales-agent/redesign-2026-04/04-principles.md (GoF, DRY, anti-parche, TDD, etc.)
   - docs/domains/sales-agent/redesign-2026-04/05-tech-debt-log.md (deuda detectada relevante)
   - docs/domains/sales-agent/redesign-2026-04/06-glossary.md
   - docs/domains/sales-agent/redesign-2026-04/phases/S0-shared-observability-extract.md (la fase actual completa)
   - .claude/rules/copilot-observability.md
   - .claude/rules/copilot-resilience.md
   - .claude/rules/backend-ddd.md
   - .claude/rules/architectural-fitness.md

2. Ejecuta el Research mandate de S0 (sección "Research mandate" del doc de fase):
   - WebSearch: 3 queries mínimas sobre LangChain BaseCallbackHandler 2026, shared module DDD pattern, LiteLLM JSON schema vigente.
   - Tessl tiles: tessl__langgraph, tessl__fastapi.
   - Lectura del code de copilot/observability/ (paths listados en S0 doc).
   Pobla "Hallazgos research" en el doc de la fase.

3. Si research sugiere cambio del enfoque inicial → documenta en sección "Ajustes vs plan original" del doc de la fase ANTES de codear, y pregunta al usuario si confirma.

4. Crea TaskCreate granular (≤4h por task) para los pasos de implementación.

5. TDD obligatorio:
   - Test que reproduce el comportamiento target → RED
   - Implementación mínima → GREEN
   - Refactor con tests verdes
   - Para arch invariants nuevos: fitness test en tests/architecture/

6. Quality gates nativos (NUNCA docker exec):
   - cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   - cd backend && .venv/bin/ruff format --check src/ tests/
   - cd backend && .venv/bin/pytest tests/modules/copilot/ tests/architecture/ -x -q
   - cd backend && .venv/bin/pytest tests/shared/ -x -q (si se crearon tests shared)

7. Verificación funcional:
   - Smoke copilot: turn real con tenant test → trazas siguen escribiendo a copilot_trace_event y copilot_llm_call.
   - §3 sigue funcionando: closer studio + buffer + webhooks (sales_agent NO se toca todavía).

8. Tech debt log:
   - Si detectas bug ajeno en copilot/observability/ durante extract → validá real → mide impacto → fix root cause SI cabe en scope, DEFERRED si no.
   - Loggear entrada en docs/domains/sales-agent/redesign-2026-04/05-tech-debt-log.md.
   - NO patches.

9. Cierra la fase:
   - learnings/S0-shared-observability-extract.md (denso, accionable, sin filler — usa learnings/_template.md como base).
   - prompts/S1-start.md (refina con contexto fresco — incluye hash de último commit, hooks listos, tech debt en radar).

10. Commit conventional + push:
    - Stage por nombre (NUNCA git add -A).
    - feat(sales-agent-redesign-s0): extract shared/agent_observability/
    - Mensaje del commit menciona learning doc + handoff prompt.

PRINCIPIOS NO NEGOCIABLES (04-principles.md):
- GoF + DRY + alta cohesión + bajo acoplamiento.
- Template Method en BaseAgentCallbackHandler. Strategy en PII regex. Repository abstract.
- Anti-parche: bug ajeno → validá → fix root cause SI cabe en scope, DEFERRED si no.
- TDD obligatorio.
- Best-effort observability (try/except + structlog warning + db.rollback).
- Spanish neutro LATAM en user-facing.
- Native-first dev (NUNCA docker exec lint/tests/type-check).
- response_model= en endpoints.
- Stage por nombre en commits.

Empieza ahora con paso 1.
```
