# Stories — iam

> SSoT atómico. 1 story = 1 archivo YAML.
> Auto-populated by /po cuando crea/actualiza stories.
> Schema: ../../specs/templates/story-{ui,agentic,service}.yaml.

## Stories activas

| ID | Type | Status | Capability | Last audit |
|----|------|--------|------------|------------|
| iam-clerk-webhook-sync | service-story | live | auth-tenant-resolution | 2026-05-04 |
| iam-current-user-tenant-resolution | service-story | live | auth-tenant-resolution | 2026-05-04 |
| iam-plan-effective-resolution | service-story | live | admin-billing-config | 2026-05-04 |

## Cómo agregar story nueva

1. `/po` skill toma user story
2. Crea `{story-id}.yaml` siguiendo template
3. Vincula a capability en `../capabilities/iam/{cap}.yaml`
4. /pm ratifica al merge → actualiza esta tabla
