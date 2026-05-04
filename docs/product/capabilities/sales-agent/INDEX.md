# Capabilities — sales-agent

> Capability = grupo lógico de stories. NO contiene scenarios (esos viven en stories).
> Schema:
> ```yaml
> id: capability-id
> name: "Nombre legible"
> module: sales-agent
> backbone_activity: "..."
> status: live | in-progress | planned       # derivado de stories
> stories_live: N
> stories_planned: M
> story_ids: [...]
> ```

## Capabilities

| ID | Name | Status | Stories live/planned |
|----|------|--------|----------------------|
| sales-conversational-engine | Motor conversacional sales_agent — supervisor + specialists + voz tenant | live | 3/0 |
| sales-tools-scheduling-payment | Tools sales_agent — scheduling + payment + enrollment | live | 2/0 |
| sales-outbound-orchestrator | OutboundOrchestrator — campaign launches outbound | live | 1/0 |
| sales-observability-cost-tracking | Observabilidad sales_agent — traces + llm_call + cost tracking | live | 2/0 |
| sales-follow-up-workers | Workers sales_agent — follow-up + payment reminder + frozen detection | live | 2/0 |
