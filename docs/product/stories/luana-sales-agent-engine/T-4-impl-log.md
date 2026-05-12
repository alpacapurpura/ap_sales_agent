# T-4 — Lift sales_agent domain layer

## Status: in_progress (builder-agentic Opus 4.7 batch 2)
## Validators targeted: V-NF-2 (package builds + tests collect)
## R23: Opus mandatory (production agentic code)

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| sales-agent-expert | §3 protected files map (`model_tier.py` LLM_ROLE_BY_SITE SSoT). Domain layer NOT in §3 list, mechanical lift OK. | Pure mechanical lift with sed import rewrites per 05-guidelines.md §1.4. |
| backend-expert (DDD) | Domain layer = pure Python, no framework. Tenant isolation per query (incl. `get_by_id`). | Verify zero `from src.*` leaks post-sed. |
| anti-duplication | Domain layer in sales_agent CANNOT mirror anything from shared/. AISALESHT sales_agent.domain is module-canonical. | No mirror risk — domain layer is module-canonical. |
| tenant-isolation | All repository interfaces in domain/memory MUST carry tenant_id. | Verify in domain/memory/repository.py post-lift. |
| tdd-mandatory | Lift-mode tests preserve existing test contracts (not RED/GREEN cycle). | Lift existing tests + sed; verify GREEN. |
| parallel-safety | Stage by exact filename, NO `git add .`. AISALESHT untouched (read-only). | Commits target luana-platform (~/luana-platform), AISALESHT impl-logs only. |

## Lift workflow

1. `cp -r /home/chris/AISALESHT/backend/src/modules/sales_agent/domain → ~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/`
2. Apply sed per 05-guidelines.md §1.4
3. Copy domain tests
4. Run pytest isolated
5. Verify zero leaks
6. Commit luana-platform
