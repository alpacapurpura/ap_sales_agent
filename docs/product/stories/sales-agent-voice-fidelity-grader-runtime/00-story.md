---
story_id: sales-agent-voice-fidelity-grader-runtime
type: agentic-story
module: sales_agent
capability: sales-conversational-engine
links:
  story_yaml: "../../../../../../product/stories/sales-agent/voice-fidelity-grader-runtime.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — Voice Fidelity Grader Runtime

## Job-To-Be-Done

**Como** auditor del sales_agent (humano o CI)
**Quiero** un grader que evalúe si cada output del agente suena como la voz de la marca del tenant y devuelva un score 0-1
**Para** detectar regresiones de voz cuando un cambio de prompt, modelo o slot rompe la fidelidad sin que sea obvio en testing manual

## Por qué importa

La voz de marca per tenant es **la** propuesta de valor diferencial de Nicolify. "Tu agente suena como vos" es lo que justifica que un cliente pague por Nicolify y no use ChatGPT directo. Cuando un dev cambia un specialist prompt, sube de modelo (Kimi → Claude), o agrega un slot al prompt cache, puede degradar sutilmente la voz sin que ningún test funcional lo detecte. El cliente lo nota cuando lee output del bot y dice "esto no suena a mí".

Esta story implementa el **grader automatizado** que mide objetivamente "qué tan parecido suena a la voz tenant" usando un LLM-as-judge calibrado contra el `personality_profile.system_instruction` (SSoT voz definido en abril 2026, ver skill `sales-agent-expert`). Sin esto, el CI gate de Story 8 no tiene métrica para enforzar.

Es la story de **mayor riesgo del PI** — LLM-as-judge es no-determinístico, calibración requiere iteración manual con Chris. Por eso threshold se fija en 0.7 (no 1.0) y se documenta variance esperada.

## Outcome esperado

- Función `grade_voice_fidelity(output_text: str, tenant_voice_profile: PersonalityProfile) → VoiceFidelityScore` operativa
- `VoiceFidelityScore` retorna: `score: float (0-1)`, `confidence: float`, `breakdown: dict[str, float]` (ej. `{"vocabulary": 0.8, "tone": 0.6, "rhythm": 0.7}`), `reasoning: str` (judge explanation), `model_used: str`
- Judge implementation: prompt templated con `personality_profile.system_instruction` + rubric `docs/specs/rubrics/voice-fidelity.md` + output to grade
- Modelo del judge: Claude Sonnet por default (balanza calidad/costo) — configurable
- Calibración documentada en `tests/agentic_evals/sales_agent/calibration/voice_fidelity_calibration.md`:
  - 10 outputs etiquetados manualmente por Chris (5 alto fit, 5 bajo fit)
  - Grader corre sobre los 10 → variance vs labels Chris debe ser ≤0.15
  - Si variance >0.15 → iterar prompt judge hasta calibrar
  - Re-calibrar cada 50 goldens nuevos (regla operacional, no enforced en CI por ahora)
- Cache hits por `(output_hash, tenant_voice_profile_hash)` → no re-judgear outputs idénticos en cada CI run
- Tests:
  - Unit: grader devuelve score válido para input dummy
  - Integration: 10 outputs calibración → variance ≤0.15 vs Chris labels
  - Performance: latency p95 ≤ 3s per grade (Sonnet judge)

## Antecedentes / Contexto

- **Depende de:** Story 5 (goldens reales para evaluar) + Story 6 (personas para diversidad de outputs)
- **SSoT voz:** `personality_profile.system_instruction` per tenant — definido en migración brand-studio 2026-04. Cargar `sales-agent-expert` skill para entender Compiler v2 + 6 bloques + cache slots
- **Rubric:** `docs/specs/rubrics/voice-fidelity.md` (ya existe)
- **Decisión cardinal:** threshold 0.7 NO 1.0 (LLM judges son ruidosos a alta resolución)
- **Threshold env var:** `SALES_AGENT_VOICE_FIDELITY_THRESHOLD=0.7` (Decision 30, ya declarada — Story 8 la enforza en CI)
- **Skills:** `sales-agent-expert` (voz SSoT), `claude-api` (judge prompt + caching), `tessl__langgraph` (si grader hookea workflow), brand-expert (entender personality_profile structure)

## Out of scope (explícito)

- CI gate enforcement — es Story 8
- Per-tenant threshold tuning (scope global env var en este PI)
- Multi-judge ensembling (1 judge Sonnet es suficiente para Sprint 3)
- Auto-tuning del judge prompt vía optimization (manual iteración con Chris)
- Grader para otras métricas (no-hallucination, no-overpromise) — Story 9 los usa pero esta story es voice-fidelity only
- Backfill grader scores sobre conversaciones históricas de producción (scope: solo eval runtime)
- Grader que enseña al agente cómo mejorar (esta story sólo grades, no fine-tunes)

## Riesgos / Asunciones

- **Riesgo:** LLM-as-judge nondeterministic (mismo input puede dar score 0.65 una vez, 0.78 otra). **Mitigación:** Cache aggressive por output_hash + Stories de variance documentada (re-runs sobre cache reportan idéntico). Threshold 0.7 con buffer.
- **Riesgo:** Calibración con Chris consume tiempo si variance >0.15 inicial. **Mitigación:** Iteración prompt judge max 3 ciclos, si no converge escalar a re-evaluar enfoque.
- **Riesgo:** Costo judge alto (1 grade por output × N outputs por test × M tests = mucho Sonnet). **Mitigación:** Cache + Story 3 budget cap. Evaluar si Haiku sería suficiente para algunas dimensiones.
- **Asunción:** `personality_profile.system_instruction` está bien-formed para los 3 tenants elegidos en Story 5 (no edge cases con voice profile vacío o conflictivo). Validar al implementar.
- **Asunción:** Chris dispone de ~2 horas para etiquetar los 10 outputs de calibración. Sin esto, grader no puede ratificarse.

## Próximo paso

`→ /po lee este archivo + Stories 5+6 specs ratificados → produce 01-spec.md Gherkin (escenarios: happy grade output alta fidelidad, edge output ambiguo confidence baja, adversarial output que parece bien pero rompe voz, calibración variance documentada) + carga skills sales-agent-expert + brand-expert + claude-api`
