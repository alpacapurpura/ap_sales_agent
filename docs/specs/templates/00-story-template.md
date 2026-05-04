# 00-story.md — Template (PM)

> Owner: `/pm`. Lo que sabe el PM del story ANTES de invocar /po.
> NO es spec ejecutable (eso es 01-spec.md). Aquí va el QUÉ y el PORQUÉ.

---
story_id: STORY_ID_KEBAB
type: ui-story                                    # ui-story | agentic-story | service-story
module: MODULE_NAME
capability: CAPABILITY_ID
links:
  story_yaml: "../../../../../product/stories/{module}/{story-id}.yaml"
  capability_yaml: "../../../../../product/capabilities/{module}/{capability}.yaml"
  module_doc: "../../../../../product/modules/{module}.md"
  opportunity: "../../../../../product/opportunities/{slug}.md"   # si origina de discovery
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

## Job-To-Be-Done

**Como** [rol/persona]
**Quiero** [acción concreta]
**Para** [resultado de negocio medible]

## Por qué importa

[1-2 párrafos: contexto de mercado, dolor user, costo de no hacerlo, impacto esperado.]

## Outcome esperado

- [Outcome user-observable 1]
- [Outcome product-observable 2]
- [Métrica que debería mover, target y baseline si existe]

## Antecedentes / Contexto

- [Story relacionada o capability previa]
- [Decisión cardinal del PI]
- [Restricción técnica conocida]
- [Stakeholder que pidió esto]

## Out of scope (explícito)

- [Lo que NO entra en este story]
- [Funcionalidad que parece relacionada pero va en otro story]

## Riesgos / Asunciones

- **Riesgo:** [riesgo 1] — **Mitigación:** [...]
- **Asunción:** [asunción 1 que validamos al implementar]

## Próximo paso

`→ /po lee este archivo + carga skill correspondiente (brand-expert, copilot-expert, etc) → produce 01-spec.md + actualiza/crea product/stories/{module}/{story-id}.yaml`
