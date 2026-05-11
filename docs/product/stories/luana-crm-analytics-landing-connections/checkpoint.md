---
story_id: luana-crm-analytics-landing-connections
outcome: luana-platform-migration
state: developed                                # All 13 tickets shipped to luana-platform main (2cac18d..981bf3b). Gate-output.json written 2026-05-11.
phase: complete
last_artifact: gate-output.json
last_modified: 2026-05-11
base_sha: ca1ab02ff55cb38d0c9acb2d86e8f7ea45ec393b
next_action: "Awaiting /auditor Conv 3 review (orchestrator spawns auditor-backend Opus)."
ratified_by_chris: true                         # pre-auth §7.2 — outcome luana-platform-migration §7.3 lift mode + §7.4 halt
spawned_at: 2026-05-09
spawned_by: /pm
parallel_safe: false                            # 1 Claude sequential per outcome §7.4
sequence_in_outcome: 4
blocks: [luana-brand-offer-studios]
blocked_by: [luana-iam-tenancy-content]
target_state: developed by 2026-05-25
estimated_complexity: high
estimated_tickets: 13
surface: backend (crm, analytics ETL framework, landing engine, connections engine)
production_code: false
owner_eligibility: [sonnet]
architect_completed_at: 2026-05-11
architect_artifacts:
  - 03-arch.md (1006 lines)
  - 04-validators.yaml (24 validators, schema v4)
  - 05-guidelines.md
  - 06-tickets.yaml (13 tickets)
deviations_count: 6                             # documented in 03-arch.md frontmatter
deferred_files_count: 9                         # 4 copilot_provider/ + 1 connections api/dependencies/ + 3 crm contacts-related + 1 test
---

## Architect summary

4 Python packages to lift from AISALESHT `backend/src/modules/{crm,analytics,landing,connections}/`
to `~/luana-platform/core/luana-core-{crm,analytics-engine,landing,connections}/`.

**Total: 13 tickets, ~11.5h sequential Sonnet time.**

Key decisions:
- **Analytics split into 3 sub-tickets** (T-3a framework+domain, T-3b providers+infrastructure, T-3c workers+scheduler) due to 123-file density.
- **9 deferred files** documented in 03-arch.md §9 + 05-guidelines.md §3.3:
  - 4 `copilot_provider/` subfolders → Story 6
  - 1 `connections/api/dependencies/__init__.py` (composition root wires `ChatOrchestrator`) → Story 7
  - 2 crm files (`contacts.py`, `contact_query_service.py`) + 1 test (`test_contacts_api.py`) → Story 8 (forward-couple to `campaigns`)
- **ETL extraction-contract regen strategy**: per-package Makefile in `core/luana-core-analytics-engine/Makefile`, script lifted to package `scripts/`, output path mapped to package `docs/extraction-contract.md`. Arch fitness test enforces idempotency.
- **Brand-specific connections adapters**: **ZERO files exist today** in AISALESHT. Spec wording refers to future Stories 11-13 work. Marketing connectors (manychat, mailerlite, shopify) are multi-tenant SaaS, NOT brand-specific — they lift to core.
- **3 NEW arch fitness tests** introduced (Story 4 brand-agnostic engines, Story 4 no-forward-imports, analytics extraction-contract drift idempotency).
- **1 NEW smoke test** introduced (connections engine stub-adapter registration).

DAG-clean. No inter-Story-4 coupling after deferrals applied. Pure dependency on Stories 2+3.

## Ready signal

State transition: `refined` → `ready`. All 4 artifacts present in story dir.

`/dev-team` may pick up T-1 immediately.
