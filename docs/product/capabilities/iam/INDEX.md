# Capabilities — iam

> Capability = grupo lógico de stories. NO contiene scenarios (esos viven en stories).
> Schema:
> ```yaml
> id: capability-id
> name: "Nombre legible"
> module: iam
> backbone_activity: "..."
> status: live | in-progress | planned       # derivado de stories
> stories_live: N
> stories_planned: M
> story_ids: [...]
> ```

## Capabilities

| ID | Name | Status | Stories live/planned |
|----|------|--------|----------------------|
| auth-tenant-resolution | Auth Clerk + resolución de tenant | live | 2 / 0 |
| admin-billing-config | Configuración de planes + suscripciones tenant (admin) | live | 1 / 0 |
