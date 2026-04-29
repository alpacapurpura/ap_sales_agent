---
globs: "**/*"
description: Multitenant data isolation
---

# Tenant Isolation

Every data op tenant-scoped. Sin excepciones.

- BE: `.where(Model.tenant_id == tenant_id)` en TODA query (incluye `get_by_id`). `tenant_id` from `X-Tenant-ID` header (middleware). Repos reciben `tenant_id` required param.
- FE: `fetchClient` auto-inyecta `X-Tenant-ID` from Clerk. Routes incluyen `[tenantId]`. NUNCA hardcode.
