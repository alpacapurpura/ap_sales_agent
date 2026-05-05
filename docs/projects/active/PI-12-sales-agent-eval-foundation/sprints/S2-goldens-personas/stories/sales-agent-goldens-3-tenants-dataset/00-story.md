---
story_id: sales-agent-goldens-3-tenants-dataset
type: service-story
module: sales_agent
capability: sales-conversational-engine
links:
  story_yaml: "../../../../../../product/stories/sales-agent/goldens-3-tenants-dataset.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — Goldens 3-Tenants Dataset

## Job-To-Be-Done

**Como** owner del producto + dev del eval suite
**Quiero** 12 conversaciones golden curadas (3 tenants × 4 escenarios) extraídas de producción y anonymizadas
**Para** que las evaluaciones midan el comportamiento real del agente, no escenarios sintéticos artificiales

## Por qué importa

Los goldens **son** el ground truth del eval suite. Sin ellos, todo lo construido en S1 (runner, pass^k, budget cap) y S3 (voice fidelity grader) son conchas vacías midiendo nada relevante. Goldens sintéticos escritos a mano por mí o un dev tienen sesgo (escribo lo que el agente sabe contestar, no lo que los leads reales preguntan). Goldens extraídos de producción tienen la varianza, el ruido y los edge cases reales.

Esta es la story más sensible del PI: define qué significa "el agente está bien". Por eso la curación es híbrida (agent extrae candidatos, Chris ratifica los 12 finales) — la tecnología hace el grunt work pero el juicio queda con el oracle de producto.

## Outcome esperado

- Estructura `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/` con 3 carpetas (1 por tenant representativo)
- 12 archivos YAML golden — 4 por tenant cubriendo: lead-frio (primer contacto), lead-tibio (mid-funnel), lead-caliente (cerca de cerrar), refutación de objeción
- Cada golden YAML incluye:
  - `id`, `tenant_slug`, `tenant_industry`, `scenario_type`
  - `input` (mensaje del lead)
  - `tenant_context` (snapshot voice profile + offer relevante + persona target)
  - `expected_behavior` (criterio observable: agendar/cobrar/derivar/refutar/escalar)
  - `expected_voice_attributes` (subset de personality_profile applicable a este turn)
  - `forbidden_outputs` (cosas que NO debe hacer: prometer X, mencionar Y, sonar Z)
- PII verificada anonymizada via `sanitize_payload`: cero emails reales, teléfonos, nombres propios, URLs internas
- README en `goldens/` documenta:
  - Criterios de selección (qué hace que un caso sea "golden material")
  - Cómo agregar un golden nuevo (template + checklist)
  - Política de actualización (cuándo refrescar dataset, quién aprueba)
- 3 tenants elegidos cubren verticales distintas (ej. coach, consultor, e-com) — Chris ratifica selección antes de extracción

## Antecedentes / Contexto

- **Origen:** sin goldens reales, voice fidelity grader (Story 7) y CI gate (Story 8) son humo
- **Decisión Chris 2026-05-04:** curación híbrida (b) — agent-helper extrae candidatos vía consulta a tablas `sales_agent_session` reales + `sanitize_payload`, Chris elige 12 finales
- **Stack:** datos vienen de tablas live de sales_agent (no producción crítica, sólo lectura). Output va a archivos YAML checked-in (no DB).
- **Stakeholder primario:** Chris (oracle de "qué responde bien el agente")
- **Skills que cargar:** `sales-agent-expert` (voice profile), `backend-expert` (query DB), `tessl__pytest-api-testing` (estructura YAML compatible con runner Story 1)

## Out of scope (explícito)

- Más de 12 goldens en este sprint (scope inicial 3 tenants × 4 escenarios — expand en PI futuro si grader saturate)
- Goldens adversariales (jailbreak/injection/overpromise) — son Story 9 en S4
- Personas como simulators dinámicos — es Story 6
- Versioning/diff tooling sobre goldens (basta git history en este PI)
- Goldens en idiomas distintos a español neutro (scope LatAm)
- Curation automática 100% (sin Chris en el loop) — riesgo de drift sin oracle

## Riesgos / Asunciones

- **Riesgo:** PII leak en commit (un email/teléfono no anonymizado se publica en repo). **Mitigación:** Pre-commit hook que escanea goldens/ buscando patterns PII (regex email/phone/dni). Bloquea commit si match. Test unitario sobre los 12 goldens.
- **Riesgo:** Goldens sesgados hacia happy path (agent extractor sólo captura conversaciones exitosas). **Mitigación:** Selección explícita 1 escenario "refutación objeción" por tenant — fuerza incluir casos donde el agente tuvo que trabajar.
- **Riesgo:** Tenants elegidos no representan diversidad real. **Mitigación:** Chris elige 3 con verticales/voces/lengua distintas explícitamente. Documentar selección.
- **Asunción:** Las tablas `sales_agent_session` (o equivalente) tienen >100 conversaciones por tenant para tener pool de candidatos. Si pool insuficiente, escalar a más tenants o usar mocks complementarios.
- **Asunción:** Chris dispone de ~2-3 horas concentradas para curar los 12 finales (resto del tiempo del story 5d es agent extraction + sanitization + format).

## Próximo paso

`→ /po lee este archivo + carga skill sales-agent-expert + backend-expert → produce 01-spec.md Gherkin (escenarios: happy 12 goldens válidos, edge tenant con pool insuficiente, adversarial PII slip detection, criterios curation Chris) + ratifica los 3 tenants antes de empezar extracción`
