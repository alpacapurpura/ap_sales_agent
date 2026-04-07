---
globs: "**/*"
description: Nicolify-specific debugging commands and common error patterns
---

# Debugging (Nicolify-specific)

Complements `superpowers:systematic-debugging` skill with project-specific knowledge.
When that skill says "reproduce", "gather evidence", or "verify" — use these commands.

## Diagnostic Commands

| What | Command |
|---|---|
| Backend logs | `docker logs visionarias_brain_dev --tail 100` |
| Backend errors only | `docker logs visionarias_brain_dev --tail 200 2>&1 \| grep -i 'error\|traceback\|exception'` |
| Frontend logs | `docker logs visionarias_client_dev --tail 100` |
| Container health | `docker compose ps` |
| Migration status | `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic current"` |
| TypeScript check | `cd frontend && npx tsc --noEmit 2>&1 \| head -50` |
| Backend lint | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` |
| Backend tests | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Frontend tests | `cd frontend && npx vitest run` |

## Common Nicolify Error Patterns

Check these FIRST — they cover ~80% of bugs:

1. **Missing `tenant_id` filter** → empty results or data leak across tenants
2. **SA 1.x syntax** (`session.query()`) → must be `select(Model).where(...)`
3. **Docker volume stale** → old code cached, fix: `docker compose up -d --build <service>`
4. **Migration not applied** → table/column missing, check `alembic current` vs `alembic history`
5. **Clerk token expired** → 401 errors, re-authenticate
6. **Cross-module import** → violates DDD boundaries, refactor to shared or event
7. **Next.js build failure** → known pre-existing issue (standalone + Pages Router 404 conflict)
8. **ETL credential expiry** → Meta token dead, GA4 missing property_id, check connections config
9. **Missing env var** → silent failures or connection refused, verify `.env` vs `docker-compose.yml`
10. **Qdrant unavailable** → vector search fails silently, check container health

## Fix Quality Mandate

Every bug fix MUST follow these rules:

- **Root cause only.** Never patch symptoms. If `systematic-debugging` Phase 1 isn't complete, don't write code.
- **Leave it better.** If you touch a file to fix a bug, clean up obvious tech debt in that file (dead imports, type: any, inconsistent naming). Small scope — same file only.
- **No new debt.** No `// TODO`, no `// HACK`, no `type: any`, no disabled lint rules. Fix it properly or flag it.
- **Verify natively.** Run the relevant CI commands natively (lint + tests) BEFORE claiming the fix works.
- **One fix per hypothesis.** Never bundle multiple changes. If the first fix doesn't work, revert and re-analyze.
- **Regression test FIRST.** Escribir test que reproduce el bug ANTES del fix. El test debe fallar (RED). Solo entonces implementar el fix (GREEN). Sin excepciones.
