---
story_id: sales-agent-cost-tracking-deepseek-fix
type: service-story
module: sales_agent                              # surface principal; toca también shared/agent_observability/cost/
capability: sales-conversational-engine           # cost observability transversal — capability principal afectada
links:
  story_yaml: "../../../../../../product/stories/sales-agent/cost-tracking-deepseek-fix.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — Cost Tracking DeepSeek Fix

## Job-To-Be-Done

**Como** owner del producto / dev que mira los reportes de costo del agente
**Quiero** que `cost_usd` nunca sea $0 falso cuando el provider real fue DeepSeek
**Para** confiar en las decisiones de routing entre modelos (cuándo usar Kimi vs Claude vs DeepSeek) y para que el billing tenant esté correcto

## Por qué importa

Hoy las llamadas a DeepSeek se taggean incorrectamente como provider="openai" en `model_pricing_snapshot` (porque DeepSeek usa OpenAI-compatible SDK y el wrapper hereda el alias mal). Cuando el pricing resolver busca el row para calcular cost, no encuentra match exacto → devuelve `cost_usd=0`. Resultado: los reportes de costo del sales_agent muestran **muchas trials con costo cero**, lo que rompe:

- Decisiones de routing (Kimi vs DeepSeek vs Claude) — sin costo real, no podés optimizar
- Story 3 (budget cap) — no puede capear nada si la métrica miente
- Billing si en algún momento cobramos por cost+margin

Es un bug acotado pero crítico para el resto del PI. Por eso lo movimos a S1 (era S4 originalmente) — quick win de 2d que desbloquea reporting confiable durante todo el PI-12.

## Outcome esperado

- `pricing_resolver.py` (o equivalente en `shared/agent_observability/cost/`) mapea correctamente `provider=deepseek` → row correcto en `model_pricing_snapshot`
- Migración idempotente (Alembic, `IF EXISTS`) que repara snapshots históricos donde `provider="openai"` pero `model` empieza con `deepseek-` → re-tag como `provider="deepseek"`
- Test unitario verifica los 5 providers (`openai`, `deepseek`, `kimi`, `qwen`, `gemini`) tienen pricing resolution correcta
- Métrica post-deploy verificable: `SELECT COUNT(*) FROM copilot_llm_call WHERE provider='deepseek' AND cost_usd=0 AND created_at > NOW() - INTERVAL '1 day'` → debe ser 0
- Documentado en commit body (cumple `anti-default-flip-audit.md` pattern aunque NO sea un flag flip — es un fix de pricing, pero el rigor de tests audited aplica)

## Antecedentes / Contexto

- **Origen:** `docs/process/gap-report-2026-05-04-group-c.md` — bug detectado durante migración SDD
- **Stack afectado:** `backend/src/shared/agent_observability/cost/pricing_resolver.py` + `backend/src/shared/agent_observability/persistence/pricing_snapshot_repository.py` (paths exactos a confirmar al implementar — leer skill `sales-agent-expert` para SSoT cost stack)
- **Decisión Chris 2026-05-04:** Movido de S4 a S1 — quick win + reporting confiable día 1
- **Owner pool:** `qwen-opencode` (BE non-agentic patch, NO toca prompts ni voice — apto para qwen sin necesidad Opus)
- **Skills:** `backend-expert`, `tessl__pytest-api-testing`. NO carga `sales-agent-expert` agentic surfaces (no toca prompts).

## Out of scope (explícito)

- Refactor del pricing stack completo (esta story es **fix** acotado, no rediseño)
- Agregar nuevos providers (kimi/qwen/gemini ya tienen mapping — sólo verificar que sigue verde post-fix)
- Cambiar precios actuales en `model_pricing_snapshot` — sólo arreglar el mapeo, no actualizar tarifas
- Migración de cost histórico para tenants en facturación (si afecta billing pasado, escalar Chris antes de aplicar — la migración acá repara snapshot mapping, NO recalcula bills)
- Cualquier cambio al runtime del agente (latency, routing, prompts)

## Riesgos / Asunciones

- **Riesgo:** El fix toca código `shared/agent_observability/` que es consumido también por `copilot/`. **Mitigación:** Tests cross-module (verificar copilot cost tracking sigue verde post-fix). Cargar skill `copilot-expert` para entender impacto.
- **Riesgo:** Migración de repair sobre `model_pricing_snapshot` puede ser destructiva si misclasifica algún row legítimo openai. **Mitigación:** WHERE clause estricto: `provider='openai' AND model LIKE 'deepseek-%'`. Backup table snapshot antes de UPDATE. Rollback plan documentado.
- **Asunción:** Los 5 providers actuales son exhaustivos. Si hay un sexto provider en uso (ej. Anthropic direct API en un wrapper olvidado) que también está mal-tagged, surge en testing. Documentar y abrir story separada.

## Próximo paso

`→ /po lee este archivo + carga skill backend-expert + investiga path exacto pricing_resolver → produce 01-spec.md Gherkin (escenarios: happy fix verifies 5 providers, edge migración rollback, adversarial duplicate snapshot rows post-repair) + crea/actualiza story YAML`
