# T-6 — Lift sales_agent infrastructure repositories + memory + monitoring + prompts

## Status: in_progress (builder-agentic Opus 4.7 batch 2)
## Validators targeted: V-NF-2

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| sales-agent-expert | No §3 protected files in T-6 scope (closer to T-7). Repositories use SQLA 2.0 + tenant_id. | Pure mechanical lift. |
| backend-expert | SQLA 2.0 `select(Model).where(...)` not legacy `session.query()`. | Verify post-lift. |
| backend-ddd | Repository pattern: implements domain interface, takes tenant_id. AsyncSession new code. | Tenant isolation verified. |
| tenant-isolation | Each repository method must filter `tenant_id`. | Verified in lifted files. |
| anti-duplication | Vector store wraps Qdrant — must consume from luana_core_platform / shared infra (not mirror). | Verify imports post-lift. |
| parallel-safety | Stage by exact filename. | luana-platform commit only. |

## Lift workflow

1. cp -r repositories + memory + monitoring + prompts (incl. templates/ + legacy/)
2. Apply sed
3. Run tests (no new test additions — most repo tests need T-12 services + fixtures)
4. Verify zero leaks
5. Commit
