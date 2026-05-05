---
story_id: sales-agent-eval-pass-k-tracking
type: service-story
module: sales_agent
capability: sales-conversational-engine
links:
  story_yaml: "../../../../../../product/stories/sales-agent/eval-pass-k-tracking.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — Eval Pass^k Tracking

## Job-To-Be-Done

**Como** dev que mira los resultados del eval suite
**Quiero** que cada golden corra N trials (default 3) y reporte la probabilidad de éxito en k intentos consecutivos
**Para** que un "verde" signifique "esto pasa de forma confiable", no "pasó esta vez de casualidad"

## Por qué importa

Los LLMs son no-determinísticos. Correr un golden 1 sola vez es ruido — un agente puede pasar 1 de 3 veces y darte la falsa sensación de que está bien. El estándar de la industria (Anthropic, OpenAI, Cohere) para evals con LLMs es **pass^k**: la probabilidad de que el modelo pase el golden en k corridas consecutivas independientes. Threshold típico: `pass^3 >= 0.5` (al menos 50% de los trios de 3 corridas pasan todos).

Sin esto, el eval suite que armamos en Story 1 te miente con verdes flaky. Después en Story 8 cuando el CI gate rechace un PR, el dev no va a saber si es regresión real o variance del modelo. Pass^k separa señal de ruido.

## Outcome esperado

- El runner ejecuta cada golden N veces (default 3, configurable via env `SALES_AGENT_EVAL_TRIALS`)
- Por cada golden reporta: `trials_total`, `trials_passed`, `pass_rate` (passed/total), `pass_k` (probabilidad de pasar k consecutivos)
- El reporte agregado por suite incluye: `pass_k_avg`, `pass_k_min`, goldens flaky (pass_rate entre 0.3-0.7)
- Threshold configurable per golden YAML: `min_pass_k: 0.5` (default), override per golden si justificado
- Output JSON estructurado en `/tmp/sales-agent-eval-report.json` para CI gate (Story 8) consumir
- Reporte humano-friendly por consola (color-coded verde/amarillo/rojo)

## Antecedentes / Contexto

- **Depende de:** Story 1 `sales-agent-eval-runner-foundation` (necesita el harness funcionando)
- **Decisión cardinal PI-12:** trial policy default trials=3, pass^3 >= 0.5, cost_cap_per_trial=$0.50
- **Stack:** integración con runner Story 1, uso de `pytest-asyncio` para ejecutar trials concurrentes (decidir en `01-spec.md` si paralelo o secuencial — paralelo más rápido pero satura rate limits)
- **Referencia matemática:** pass^k = (pass_rate)^k para trials independientes. Para k=3 y pass_rate=0.7 → pass^3 = 0.343 (no pasa threshold 0.5 → flaky)
- **Skills que cargar:** `sales-agent-expert`, `tessl__pytest-api-testing`, `claude-api` (rate limits considerations)

## Out of scope (explícito)

- Goldens reales — es Story 5
- Cost budget cap — es Story 3
- Voice fidelity grader (que también devuelve un score) — es Story 7. Pass^k mide **comportamiento esperado**, no fidelidad de voz.
- Statistical significance testing avanzado (chi-square, p-values) — pass_rate y pass_k son suficientes para Sprint 1
- Retry on transient errors (timeouts, 429s) — los trials cuentan tal cual; un timeout es un fail. Si problema operacional persiste, abrimos story aparte.

## Riesgos / Asunciones

- **Riesgo:** 12 goldens × 3 trials = 36 LLM calls/run = costo no trivial. **Mitigación:** Story 3 budget cap. Run nightly, no en cada commit.
- **Riesgo:** Trials paralelos saturan rate limits (especialmente Anthropic). **Mitigación:** Concurrencia configurable, default secuencial conservador.
- **Asunción:** Los trials son independientes (cache stateful entre trials no contamina). Validar al implementar — si cache hit en trial N+1 falsea el resultado, forzar `cache_control` reset entre trials.

## Próximo paso

`→ /po lee este archivo + Story 1 spec ya ratificado → produce 01-spec.md Gherkin (escenarios: happy 3/3 trials passed, edge 2/3 passed = pass_rate 0.67 + pass^3 0.30, flaky golden detection, configurable threshold override) + actualiza story YAML`
