---
story_id: sales-agent-eval-runner-foundation
type: service-story
module: sales_agent
capability: sales-conversational-engine
links:
  story_yaml: "../../../../../../product/stories/sales-agent/eval-runner-foundation.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — Eval Runner Foundation

## Job-To-Be-Done

**Como** dev/auditor que toca `modules/sales_agent/`
**Quiero** correr evaluaciones reproducibles del agente desde pytest contra goldens definidos
**Para** detectar regressions de comportamiento antes de mergear (no enterarme cuando un cliente se queja)

## Por qué importa

Hoy `backend/tests/agentic_evals/sales_agent/` **no existe**. Las 6 stories agentic declaradas en `product/stories/sales-agent/` (closer-conversation, follow-up-trigger, scheduler-tool-call, etc.) tienen `test_coverage.eval_suite_path: null`. Esto significa que cualquier cambio al agente — un nuevo prompt slot, un tweak al specialist router, un upgrade de modelo — se mergea **a ciegas**. La única señal real llega cuando un tenant reporta que el bot dejó de cerrar o cambió la voz.

Esta story es el primer ladrillo: el harness mínimo donde después se enchufa pass^k (Story 2), budget cap (Story 3), goldens reales (Story 5), personas (Story 6), grader (Story 7), CI gate (Story 8). Sin este harness, las otras 5 stories del PI no pueden empezar.

## Outcome esperado

- Existe `backend/tests/agentic_evals/sales_agent/` con estructura clara (`runner/`, `goldens/`, `conftest.py`, `__init__.py`)
- Existe un `conftest.py` con fixtures que: (a) instancian el agente con un tenant_id mock, (b) le pasan un input, (c) capturan output completo + traces (`copilot_trace_event`-equivalent del módulo) + cost (`copilot_llm_call`)
- Existe un primer test smoke `test_eval_runner_smoke.py` que carga 1 golden hardcoded simple (ej. "hola, ¿qué venden?"), corre el agente, valida que devuelve respuesta no-vacía y captura cost > 0
- Dev puede invocar manualmente: `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/ -v` y ver el smoke pasar
- README en `tests/agentic_evals/sales_agent/README.md` documenta: cómo agregar un golden, qué fixtures hay disponibles, cómo correr en local

## Antecedentes / Contexto

- **Origen:** `docs/process/gap-report-2026-05-04-group-c.md` — flag CRÍTICO sales_agent sin eval suite
- **Path confirmado:** `backend/tests/agentic_evals/sales_agent/` (Chris ratificó 2026-05-04)
- **Stack relacionado:** sales_agent post-redesign abril 2026 (carga `sales-agent-expert` skill al codear). Debe respetar:
  - PersonalityProfile.system_instruction como SSoT voz
  - Prompt cache slots (no romper cache hit rate)
  - Trial policy default trials=3 (Story 2 lo implementa, este harness debe permitirlo)
- **Stakeholder:** Chris (product owner) — necesita confianza para deployar cambios sales_agent
- **Skills que cargar al implementar:** `sales-agent-expert`, `tessl__pytest-api-testing`, `tessl__langgraph` (si runner espía state machine), `claude-api` (caching considerations)

## Out of scope (explícito)

- Pass^k tracking — es Story 2 (`sales-agent-eval-pass-k-tracking`)
- Budget cap por run — es Story 3 (`sales-agent-eval-cost-budget-cap`)
- Goldens reales de tenants — es Story 5 (`sales-agent-goldens-3-tenants-dataset`). Acá basta 1 golden hardcoded de smoke.
- Personas como simulators — es Story 6
- Voice fidelity grader — es Story 7
- CI gate — es Story 8
- Adversarial scenarios — es Story 9
- Cualquier cambio al `modules/sales_agent/` runtime real — esta story sólo agrega `tests/`

## Riesgos / Asunciones

- **Riesgo:** El runner consume budget tenant real al invocar el agente. **Mitigación:** Fixture mock budget guard (no consume budget table real). Documentar.
- **Riesgo:** Smoke test cuesta dinero cada corrida (1 LLM call con Claude/Kimi). **Mitigación:** Marker pytest `@pytest.mark.eval` que requiere flag `--run-evals` para ejecutar. CI no corre por defecto en cada push.
- **Asunción:** El agente sales_agent expone una entrypoint async invocable desde test sin levantar FastAPI completo. Validar al implementar — si no, agregar wrapper.
- **Asunción:** Existe forma de capturar `copilot_llm_call`-equivalent del módulo sales_agent para cost recording. Si la observabilidad sales_agent vive en otro repo/tabla → ajustar fixture.

## Próximo paso

`→ /po lee este archivo + carga skill sales-agent-expert + tessl__pytest-api-testing → produce 01-spec.md (Gherkin AI-resistant: happy + negative + edge + adversarial) + crea/actualiza product/stories/sales-agent/eval-runner-foundation.yaml`
