---
story_id: luana-shared-lift
outcome: luana-platform-migration
merge_date: 2026-05-11
merged_by: /pm (claude-opus-4-7)
auditor_verdict: APPROVED (31/31 ✅, 3 WARN non-blocking, 2 trivial self-fix)
final_state: done
---

# Merge — luana-shared-lift

## Resumen

Story 2 luana-shared-lift cierra DONE. /dev-team Sonnet construyó T-1..T-17 secuencial
en ~100min wall clock (~$5). /auditor Sonnet C1-C5 APPROVED 31/31 con 2 self-fix
trivial (stale TYPE_CHECKING import + I001 sort). 9 Python + 6 TS = 15 packages
lifted verbatim. AISALESHT UNTOUCHED verificado por git diff.

## Commits aplicados

Repo `alpacapurpura/luana-platform` (main, range 9615d47..8e86d98):
- T-1..T-12 lift packages (per DAG)
- T-13..T-17 integration + finalization
- 4ca22c6 — final dev-team commit (T-17 READMEs)
- 2b27bce — auditor self-fix 1 (stale TYPE_CHECKING import path)
- 8e86d98 — auditor self-fix 2 (ruff I001 sort)

Repo `AISALESHT` (development):
- f3736853 — Story 2 closure (gate-output.json + checkpoint + BACKLOG regen)
- (next commit, this merge) — 07-merge.md + archive + outcome update

## Validators outcome (per gate-output.json)

- 38 validators total (V-NF-*, V-F-*, V-AE-*, V-D-*)
- All GREEN per dev-team run, re-verified by auditor live
- 728 Python tests pass (703 core + 25 nicolify) + 39 TS pass + 4 arch fitness pass
- 3 arch fitness deferred to `_deferred/` (AISALESHT-specific, lift not portable)

## Findings auditor (no bloqueantes)

| ID | Cat | Issue | Acción /pm |
|---|---|---|---|
| W-1 | C1 | `model_registry.py` runtime `src.modules.*` imports — verbatim lift, not imported in tests | Will be exercised once Stories 3-8 land brand/offer/copilot/sales_agent modules; defer fix |
| W-2 | C1 | Pydantic v2 `class Config` deprecation warnings (pre-existing AISALESHT) | Lift-verbatim preserves; tracked for future refactor pass |
| W-3 | C5 | No per-ticket T-N-impl-log.md / T-N-result.md granularity | gate-output.json consolidates sufficient evidence. Convention to revisit for future stories |

## Capabilities promovidas

15 packages now tracked at outcome level (`luana-platform-migration.md`):

**Python (9):**
- `luana-core-platform` (foundation: src/core + shared/{domain,infrastructure/{files,prompts,database,external,web,models},workers,api,links/ports})
- `luana-core-llm` (infrastructure/llm)
- `luana-core-channels` (shared/agent_observability/channels + shared/infrastructure/channels)
- `luana-core-idempotency` (shared/idempotency)
- `luana-core-observability` (shared/agent_observability/{recording,persistence,cost,pricing,application,workers,reporting})
- `luana-core-events` (shared/domain_events/outbox)
- `luana-core-extraction` (shared/application/extraction)
- `luana-core-compliance` (shared/compliance)
- `luana-core-billing` (shared/billing)

**TypeScript (6):**
- `@luana/design-tokens` (frontend/src/lib/tokens)
- `@luana/hooks` (frontend/src/hooks)
- `@luana/format` (frontend/src/lib/{format,utils,constants})
- `@luana/ui-kit` (frontend/src/components/ui)
- `@luana/api-client` (frontend/src/lib/api + http-client)
- `@luana/schemas` (placeholder — frontend/src/lib/zod-schemas/ doesn't exist yet)

5 deviations within lift mode boundaries (documented in checkpoint.md frontmatter).

## Archive

Story folder → `docs/archive/2026/stories/luana-shared-lift/` (snapshot inmutable).

## Próximo paso

Phase C — Story 3 luana-iam-tenancy-content autonomous. Lift `iam` + `tenant_profile`
+ `tenant_domains` + `commercial_calendar` + `social_proof` + `assets`. Same lift mode
pattern. Unlocked by Story 2.
