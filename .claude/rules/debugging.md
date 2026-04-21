---
globs: "**/*"
description: Nicolify-specific debugging commands and common error patterns
---

# Debugging (Nicolify)

Complementa `superpowers:systematic-debugging` skill con project-specific. Cuando skill dice "reproduce"/"gather evidence"/"verify" → usar estos commands.

## Diagnostic Commands

| What | Command |
|---|---|
| BE logs | `docker logs visionarias_brain_dev --tail 100` |
| BE errors | `docker logs visionarias_brain_dev --tail 200 2>&1 \| grep -i 'error\|traceback\|exception'` |
| FE logs | `docker logs visionarias_client_dev --tail 100` |
| Container health | `docker compose ps` |
| Migration status | `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic current"` |
| TSC | `cd frontend && npx tsc --noEmit 2>&1 \| head -50` |
| BE lint | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` |
| BE tests | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| FE tests | `cd frontend && npx vitest run` |

## Common Nicolify Error Patterns

Check FIRST — cubren ~80% bugs:

1. Missing `tenant_id` filter → empty results / cross-tenant leak
2. SA 1.x syntax (`session.query()`) → must be `select(Model).where(...)`
3. Docker volume stale → old code cached. Fix: `docker compose up -d --build <svc>`
4. Migration no aplicada → table/column missing. Check `alembic current` vs `history`
5. Clerk token expired → 401, re-auth
6. Cross-module import → viola DDD, refactor a shared/event
7. Next.js build failure → pre-existing (standalone + Pages Router 404)
8. ETL credential expiry → Meta token dead, GA4 missing property_id
9. Missing env var → silent failures / connection refused. Verify `.env` vs `docker-compose.yml`
10. Qdrant unavailable → vector search fails silently, check container

## Fix Quality Mandate

- **Root cause only.** No patch symptoms. Si `systematic-debugging` Phase 1 incompleto, no code.
- **Leave it better.** Touch file → cleanup obvious tech debt (dead imports, type: any, naming). Same file only.
- **No new debt.** No `// TODO`, `// HACK`, `type: any`, disabled lint. Fix o flag.
- **Verify native.** Relevant CI commands native BEFORE claim.
- **One fix per hypothesis.** No bundle. Fix no works → revert + re-analyze.
- **Regression test FIRST.** Test reproduce bug ANTES fix. RED. Solo entonces fix (GREEN). Sin excepciones.
