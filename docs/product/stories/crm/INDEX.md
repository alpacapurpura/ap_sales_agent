# Stories — crm

> SSoT atómico. 1 story = 1 archivo YAML.
> Auto-populated by /po cuando crea/actualiza stories.
> Schema: ../../specs/templates/story-{ui,agentic,service}.yaml.

## Stories activas

| ID | Type | Status | Capability | Last audit |
|----|------|--------|------------|------------|
| crm-list-contacts | service-story | live | contacts-cdp | 2026-05-04 |
| crm-contacts-page | ui-story | live | contacts-cdp | 2026-05-04 |
| crm-create-static-segment | ui-story | live | contacts-cdp | 2026-05-04 |
| crm-pipeline-stage-override | service-story | live | pipeline-lifecycle | 2026-05-04 |

## Cómo agregar story nueva

1. `/po` skill toma user story
2. Crea `{story-id}.yaml` siguiendo template
3. Vincula a capability en `../capabilities/crm/{cap}.yaml`
4. /pm ratifica al merge → actualiza esta tabla
