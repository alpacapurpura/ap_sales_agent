---
story_id: sales-agent-personas-instrumented-runtime
type: agentic-story
module: sales_agent
capability: sales-conversational-engine
links:
  story_yaml: "../../../../../../product/stories/sales-agent/personas-instrumented-runtime.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — Personas Instrumented Runtime

## Job-To-Be-Done

**Como** dev del eval suite
**Quiero** que las 5 personas declaradas en `docs/specs/personas/*.yaml` (lead-frio, lead-tibio, lead-caliente, tenant-novato, tenant-experto) sean simuladores activos que el runner puede invocar
**Para** ampliar la cobertura del eval suite sin escribir 60+ inputs estáticos a mano (5 personas × 12 goldens = 60 escenarios)

## Por qué importa

Hoy las 5 personas son **sólo documentación YAML** sin vida en runtime. El eval suite, sin instrumentarlas, sólo testea conversaciones estáticas — un input fijo, una respuesta evaluada. Pero un sales_agent enfrenta personas reales con tono, urgencia, escepticismo, ignorancia técnica distintos. Lead-frio tira frases cortas y desconfiadas; lead-caliente pregunta cosas concretas y específicas; tenant-novato no sabe usar la plataforma.

Convertir las personas en **simuladores activos** (un LLM que asume la persona y responde como ella al output del agente) multiplica la cobertura del suite por ~5 sin proporcionalmente multiplicar el costo de mantenimiento de goldens. También expone bugs que goldens estáticos esconden (ej. el agente cierra bien con leads explícitos pero falla con leads pasivos).

## Outcome esperado

- Loader `personas/loader.py` (o equivalente en eval runner) lee `docs/specs/personas/*.yaml` y construye prompts de simulación per persona
- Cada persona expone un método `simulate_response(agent_output, conversation_state) → str` que devuelve el siguiente turn user-side simulado
- Tests parametrizados por persona en pytest: `@pytest.mark.parametrize("persona", load_personas())` corre los 12 goldens en cada persona
- Métricas separadas por persona en el reporte JSON: `pass_k_by_persona["lead-frio"]`, `pass_k_by_persona["lead-caliente"]`, etc — NO agregadas (lead-frio passing 0.4 + lead-caliente passing 0.9 promediados ocultan que el agente falla con leads fríos)
- Persona simulator usa modelo barato (Kimi/Haiku) para no inflar costo del eval — calidad de simulación > determinismo
- Cache simulator outputs por (persona_id, agent_output_hash) — re-runs idempotentes mientras goldens no cambien
- Test que verifica las 5 personas se cargan, instancian y producen respuestas no-vacías

## Antecedentes / Contexto

- **Depende de:** Story 1 (runner harness), Story 5 (goldens reales para tener inputs sobre los que personas reaccionan)
- **Personas declaradas:** ver `docs/specs/personas/*.yaml` (5 archivos: lead-frio, lead-tibio, lead-caliente, tenant-novato, tenant-experto)
- **Decisión PI-12:** NO crear personas nuevas en este story sin justificar (las 5 son consideradas exhaustivas para Sprint 2)
- **Skill stack:** `sales-agent-expert` (entender voz tenant impacta cómo persona reacciona), `tessl__langgraph` (si simulator hookea state machine), `claude-api` (caching del simulator)
- **Trial policy:** persona simulator NO cuenta en el cost budget cap (Story 3) del eval — usa pool separado para no descontar del cap del agente. Documentar.

## Out of scope (explícito)

- Crear personas nuevas (esto se hace en `docs/specs/personas/` por /pm o /po, NO en runtime)
- Personas adversariales (jailbreak personas) — son Story 9
- Persona simulator usando el mismo modelo que el agente (siempre Kimi/Haiku para personas)
- Multi-turn conversations >5 turns (scope inicial: persona reacciona 1-2 turns al output del agente, no full conversation simulation)
- Persona memory cross-test (cada test arranca persona en estado virgen)
- Persona switching mid-conversation (cada test = 1 persona fija)

## Riesgos / Asunciones

- **Riesgo:** Persona simulator devuelve outputs irrealistas (un LLM "actuando" lead-frio puede sonar caricaturesco). **Mitigación:** Calibrar prompts de simulator contra ejemplos reales de cada persona del dataset goldens (Story 5). Iterar simulator prompts hasta outputs >70% indistinguibles de leads reales (Chris evalúa muestra).
- **Riesgo:** Costo del eval explota con 5x personas. **Mitigación:** Story 3 budget cap absorbs. Persona simulator usa modelo barato. Cache outputs.
- **Asunción:** Las 5 personas declaradas cubren bien el espacio (no falta una persona crítica). Si surge gap durante calibración, escalar a /pm para agregar persona en `docs/specs/personas/`.
- **Asunción:** Persona simulator cache key `(persona_id, agent_output_hash)` es válido — el mismo output del agente en mismo persona produce misma reacción. Si la persona necesita estado conversacional para reaccionar coherentemente, cache key debe incluir state hash.

## Próximo paso

`→ /po lee este archivo + Stories 1+5 specs ratificados → produce 01-spec.md Gherkin (escenarios: happy 5 personas cargan, edge persona YAML mal-formado, adversarial persona simulator caricaturesco detected via calibración Chris) + actualiza story YAML`
