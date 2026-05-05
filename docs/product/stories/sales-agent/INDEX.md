# Stories — sales-agent

> SSoT atómico. 1 story = 1 archivo YAML.
> Auto-populated by /po cuando crea/actualiza stories.
> Schema: ../../specs/templates/story-{ui,agentic,service}.yaml.

## Stories activas

| ID | Type | Status | Capability | Last audit |
|----|------|--------|------------|------------|
| sales-inbound-conversation-qualify | agentic-story | live | sales-conversational-engine | 2026-05-04 |
| sales-inbound-conversation-close | agentic-story | live | sales-conversational-engine | 2026-05-04 |
| sales-brand-voice-fidelity | agentic-story | live | sales-conversational-engine | 2026-05-04 |
| sales-tool-send-payment-link | agentic-story | live | sales-tools-scheduling-payment | 2026-05-04 |
| sales-tool-schedule-meeting | agentic-story | live | sales-tools-scheduling-payment | 2026-05-04 |
| sales-outbound-campaign-launch | agentic-story | live | sales-outbound-orchestrator | 2026-05-04 |
| sales-trace-persist-turn | service-story | live | sales-observability-cost-tracking | 2026-05-04 |
| sales-cost-tracking-cycle-billing | service-story | live | sales-observability-cost-tracking | 2026-05-04 |
| sales-agent-litellm-canonicalization | service-story | planned | sales-observability-cost-tracking | 2026-05-04 |
| sales-followup-cadence | service-story | live | sales-follow-up-workers | 2026-05-04 |
| sales-payment-reminder-pending | service-story | live | sales-follow-up-workers | 2026-05-04 |
| sales-agent-eval-runner-foundation | service-story | planned | sales-conversational-engine | 2026-05-04 |

## Cómo agregar story nueva

1. `/po` skill toma user story
2. Crea `{story-id}.yaml` siguiendo template
3. Vincula a capability en `../capabilities/sales-agent/{cap}.yaml`
4. /pm ratifica al merge → actualiza esta tabla
