---
globs: "**/*"
description: Nicolify debug commands + error patterns
---

# Debugging

## Diagnóstico
- BE logs: `docker logs visionarias_brain_dev --tail 100`
- BE errors: `docker logs visionarias_brain_dev --tail 200 2>&1 | grep -iE 'error|traceback|exception'`
- FE logs: `docker logs visionarias_client_dev --tail 100`
- Health: `docker compose ps`
- Migration: `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic current"`
- TSC/lint/tests: ver CLAUDE.md (native).

## Top patterns (~80% bugs)
1. Missing `tenant_id` filter → empty/cross-tenant leak
2. SA 1.x `session.query()` → debe `select(Model).where(...)`
3. Docker volume stale → `docker compose up -d --build <svc>`
4. Migration no aplicada → `alembic current` vs `history`
5. Clerk token expired → 401
6. Cross-module import → viola DDD
7. Next.js build (standalone + Pages Router 404) — pre-existing
8. ETL credential expiry (Meta/GA4)
9. Missing env var (silencioso) — verify `.env` vs compose
10. Qdrant unavailable → vector search falla silencioso

## Fix Quality
Root cause only. Leave file better (cleanup tech debt mismo file). No new debt (TODO/HACK/`any`/disabled lint). Verify native antes claim. Una hipótesis por fix. **Regression test FIRST** (RED reproduce bug → fix GREEN).
