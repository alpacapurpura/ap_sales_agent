# Stories — copilot

> SSoT atómico. 1 story = 1 archivo YAML.

## Stories activas

| ID | Type | Status | Capability | Last audit |
|----|------|--------|------------|------------|
| copilot-chat-conversation-web | agentic-story | live | copilot-conversational-orchestrator | 2026-05-04 |
| copilot-tier-routing-classifier | service-story | live | copilot-conversational-orchestrator | 2026-05-04 |
| copilot-subagent-stream-isolation | service-story | live | copilot-conversational-orchestrator | 2026-05-04 |
| copilot-doc-extract-to-brand-fields | agentic-story | live | copilot-document-extraction | 2026-05-04 |
| copilot-url-extract-to-offer-fields | agentic-story | live | copilot-document-extraction | 2026-05-04 |
| copilot-telegram-magic-link | service-story | live | copilot-telegram-channel | 2026-05-04 |
| copilot-telegram-orchestrator-respond | agentic-story | live | copilot-telegram-channel | 2026-05-04 |
| copilot-suggestions-show-route-aware | service-story | live | copilot-suggestions-engine | 2026-05-04 |
| copilot-suggestions-accept-emit-event | service-story | live | copilot-suggestions-engine | 2026-05-04 |

## Cómo agregar story nueva

1. `/po` skill toma user story
2. Crea `{story-id}.yaml` siguiendo template
3. Vincula a capability en `../capabilities/copilot/{cap}.yaml`
4. /pm ratifica al merge → actualiza esta tabla
