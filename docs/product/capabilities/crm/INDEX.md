# Capabilities — crm

> Capability = grupo lógico de stories. NO contiene scenarios (esos viven en stories).
> Schema:
> ```yaml
> id: capability-id
> name: "Nombre legible"
> module: crm
> backbone_activity: "..."
> status: live | in-progress | planned       # derivado de stories
> stories_live: N
> stories_planned: M
> story_ids: [...]
> ```

## Capabilities

| ID | Name | Status | Stories live/planned |
|----|------|--------|----------------------|
| contacts-cdp | CDP unificado de contactos (multi-canal) | live | 3 / 0 |
| pipeline-lifecycle | Pipeline de ventas + lifecycle scoring | live | 1 / 0 |
