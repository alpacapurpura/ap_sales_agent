---
globs: "**/*"
description: Multitenant data isolation requirements
---

# Tenant Isolation

Every data op MUST be tenant-scoped. No exceptions.

## Backend
- All queries: `.where(Model.tenant_id == tenant_id)`
- `tenant_id` from `X-Tenant-ID` header (middleware injects)
- Repository methods receive `tenant_id` as required param
- Never return data sin tenant filtering

## Frontend
- `fetchClient` auto-injects `X-Tenant-ID` from Clerk session
- Route params include `[tenantId]` en todas auth pages
- Never hardcode tenant IDs
