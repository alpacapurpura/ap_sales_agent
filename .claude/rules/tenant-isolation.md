---
globs: "**/*"
description: Multitenant data isolation requirements
---

# Tenant Isolation

**Every data operation MUST be scoped to a tenant. No exceptions.**

## Backend
- All queries: `.where(Model.tenant_id == tenant_id)`
- `tenant_id` comes from `X-Tenant-ID` header (injected by middleware)
- Repository methods receive `tenant_id` as a required parameter
- Never return data without tenant filtering

## Frontend
- `fetchClient` automatically injects `X-Tenant-ID` from Clerk session
- Route params include `[tenantId]` for all authenticated pages
- Never hardcode tenant IDs
