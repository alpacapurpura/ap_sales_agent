---
story_id: sales-agent-eval-cost-budget-cap
type: service-story
module: sales_agent
capability: sales-conversational-engine
links:
  story_yaml: "../../../../../../product/stories/sales-agent/eval-cost-budget-cap.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — Eval Cost Budget Cap

## Job-To-Be-Done

**Como** owner del producto / dev que corre evals
**Quiero** que el suite aborte automáticamente si el costo acumulado de un run supera $5 USD
**Para** no recibir bills sorpresa cuando S2 (12 goldens) o S4 (adversarial) escalen el número de LLM calls

## Por qué importa

Cuando el suite crezca a `12 goldens × 3 trials × 5 personas = 180 LLM calls`, un runaway (loop infinito en el agente, retry budget mal configurado, modelo más caro de lo esperado) puede sumar fácil $20-50 USD en una sola corrida. Si nadie está mirando, eso pasa silencioso hasta el cierre de mes.

Esta story es **defensa preventiva barata** (1d de trabajo) que evita un pain potencial mucho mayor. Es complementaria al cost recorder (Story 4) — Story 4 te dice "cuánto gastaste", esta story te dice "no gastes más de X".

## Outcome esperado

- Env var `SALES_AGENT_EVAL_BUDGET_CAP_USD=5.0` (default 5.0, override per-CI o local)
- Antes de cada LLM call, el runner consulta el cost acumulado del run actual
- Si próxima call estimada (input_tokens × price + output_estimate × price) supera el cap restante → **abortar con error claro**: `BudgetCapExceededError: run cost would exceed cap (current=$4.20, estimated_next=$1.10, cap=$5.00). Aborted at golden N, trial M, persona P.`
- Reporte parcial: el suite escribe `/tmp/sales-agent-eval-report-partial.json` con resultados hasta el momento del abort + razón
- Modo override: env var `SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=1` para correr sin cap (debug local)
- Logging visible (no silencioso): cuando 80% del cap consumido, warning estructurado en consola
- Test unitario que simula run que supera cap → assert raises + reporte parcial generado

## Antecedentes / Contexto

- **Depende de:** Story 1 (runner) + Story 4 (deepseek pricing fix — sin cost real, esta story no puede hookear nada confiable)
- **Decisión Chris 2026-05-04:** $5 USD/run cap razonable para Sprint 1-3. Re-evaluar en cierre PI-12 si Sprint 4 adversarial necesita más.
- **Stack:** consume `cost_usd` reportado por wrapper LLM del módulo (mismo path que `copilot_llm_call` recorder)
- **Skills:** `sales-agent-expert`, `tessl__pytest-api-testing`

## Out of scope (explícito)

- Per-tenant budget cap (esto es per-eval-run, no per-tenant runtime)
- Budget cap per trial individual (`cost_cap_per_trial=$0.50` ya existe a nivel trial policy — esta story es per-run aggregated)
- Notificaciones externas (Slack, email) cuando cap se aproxima — solo console log
- Auto-scaling del cap si modelos cambian de precio — manual via env var
- Cost cap para runs de producción del agente (este es solo eval)

## Riesgos / Asunciones

- **Riesgo:** Estimación pre-call (`estimated_next`) imprecisa porque output_tokens son desconocidos. **Mitigación:** Usar input_tokens reales + asumir output max permitido por config (over-estimate, mejor sobreestimar que pasarse del cap).
- **Riesgo:** Cap hit en medio de un trial deja golden con resultado parcial confuso. **Mitigación:** Reporte parcial documenta claramente "ABORTED" para esos goldens, no se cuentan en pass^k.
- **Asunción:** El cost wrapper del módulo sales_agent (mismo path o equivalente a `copilot_llm_call`) reporta `cost_usd` confiable post-Story 4. Si Story 4 no se completa antes, esta story queda blocked.

## Próximo paso

`→ /po lee este archivo + ratificar Story 1 + Story 4 specs → produce 01-spec.md Gherkin (escenarios: happy run dentro cap, edge cap hit a mitad de golden, adversarial cap=0 abort inmediato, override disable funcional, warning 80% threshold)`
