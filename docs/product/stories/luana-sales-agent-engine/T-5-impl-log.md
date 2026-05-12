# T-5 — Lift sales_agent infrastructure/models/ + infrastructure/db/

## Status: in_progress (builder-agentic Opus 4.7 batch 2)
## Validators targeted: V-NF-2 (package builds + tests collect)

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| sales-agent-expert | §3 protected files: message_model, enrollment_model, prompt_version_model, agent_state_checkpoint_model. Hash-stable lift (sed-only). | Capture sha256 POST-sed as new canonical (T-18 V-AG-8 snapshot). |
| backend-expert | SQLA 2.0 models: `Mapped[]` + `mapped_column`. `DateTime(timezone=True)`. | Verify post-sed. |
| backend-ddd | infrastructure/db/ provides BASE = declarative base. Repositories must take `tenant_id`. | Lift verbatim per architect spec. |
| anti-duplication | SQLA Base lives in `luana_core_platform.core.database` (Story 2). NEVER mirror. | infrastructure/db/base.py imports from luana_core_platform. |
| tenant-isolation | business_repository.py: all queries `.where(Model.tenant_id == tenant_id)`. | Verify post-lift. |
| parallel-safety | Stage by exact filename. AISALESHT untouched. | luana-platform commit only. |

## Lift workflow

1. cp -r infrastructure/models + infrastructure/db
2. Apply sed
3. Verify §3 protected files in expected list (4 files)
4. Copy tests
5. Verify zero leaks
6. Commit
