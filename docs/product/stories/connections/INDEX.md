# Stories — connections

> SSoT atómico. 1 story = 1 archivo YAML.

## Stories activas

| ID | Type | Status | Capability | Last audit |
|----|------|--------|------------|------------|
| connections-meta-oauth-flow | service-story | live | connections-meta-oauth | 2026-05-04 |
| connections-meta-page-account-pick | ui-story | live | connections-meta-oauth | 2026-05-04 |
| connections-manychat-webhook-receive | service-story | live | connections-manychat-integration | 2026-05-04 |
| connections-manychat-send-content-api | service-story | live | connections-manychat-integration | 2026-05-04 |
| connections-google-oauth-bundle | service-story | live | connections-google-services | 2026-05-04 |
| connections-ga4-property-picker | ui-story | in-progress | connections-google-services | 2026-05-04 |
| connections-status-list-ui | ui-story | live | connections-status-monitoring | 2026-05-04 |
| connections-reconnect-flow | ui-story | live | connections-status-monitoring | 2026-05-04 |

## Cómo agregar story nueva

1. `/po` skill toma user story
2. Crea `{story-id}.yaml` siguiendo template
3. Vincula a capability en `../capabilities/connections/{cap}.yaml`
4. /pm ratifica al merge → actualiza esta tabla
