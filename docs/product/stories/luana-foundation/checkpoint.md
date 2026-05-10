---
story_id: luana-foundation
outcome: luana-platform-migration
state: ready                                    # ★ post Chris ratification + architect revision 2026-05-10 ★
phase: ready_package_revised
last_artifact: 06-tickets.yaml
last_modified: 2026-05-10
next_action: "Ready package revised v2 per Chris ratification 2026-05-10 (monorepo + proprietary + defer GH Packages). 7 tickets, 14 validators (12 must_pass), ~5h Sonnet tool-time. /dev-team picks T-1 when ready to start sequential build."
ratified_by_chris: true                         # ★ Chris ratified scope 2026-05-10 ★
spawned_at: 2026-05-09
spawned_by: /pm + claude-opus-4-7
revised_at: 2026-05-10
revised_by: /architect (claude-opus-4-7) post Chris scope ratification
parallel_safe: false                            # 1 Claude sub sequential — no parallel sessions
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md             # po_version=2 REVISED 2026-05-10 (monorepo + anti-island)
  - 03-arch.md             # arch_version=2 REVISED 2026-05-10 (monorepo + CODEOWNERS + ADR)
  - 04-validators.yaml     # schema v4, 14 validators (12 must_pass) — REVISED
  - 05-guidelines.md       # guidelines_version=2, anti-island patterns + GH Packages forbidden
  - 06-tickets.yaml        # 7 tickets DAG, ~5h Sonnet tool-time — REVISED from 11
audit_iterations: 0
legacy_exempt: false
sequence_in_outcome: 1
blocks: [luana-shared-lift]
blocked_by: []
target_state: developed by 2026-05-18
estimated_complexity: low                       # ★ reduced from medium — scope tightened ★
estimated_tickets: 7
estimated_tool_time_min: 310                    # ~5h Sonnet sequential
surface: infra (no code lift)
production_code: false                          # infra setup, not agentic prod code
owner_eligibility: [sonnet, opus]               # mechanical setup work; opencode also OK
---

# Checkpoint — luana-foundation

## State machine

`refining` → `refined` (Chris ratified spec 2026-05-10) → **`ready` (current)** → `developing` (/dev-team picks T-1) → `developed` (12/12 must_pass validators GREEN) → `reviewing` (Chris triggers /auditor) → `done` (auditor APPROVED + capability promoted)

## Active artifacts (all v2 post 2026-05-10 revision)

- `00-story.md` — story definition (drafted 2026-05-09)
- `01-spec.md` — v2 (monorepo + anti-island + GH Packages deferred)
- `03-arch.md` — v2 (monorepo subfolder layout + CODEOWNERS + PR template + ADR scaffolding)
- `04-validators.yaml` — v2 (14 validators, 12 must_pass — down from 22/18 in v1)
- `05-guidelines.md` — v2 (anti-island patterns required; GH Packages forbidden in Story 1)
- `06-tickets.yaml` — v2 (7 tickets, ~5h Sonnet tool-time — down from 11/~7h in v1)

## Revision summary 2026-05-10

Chris ratified 3 scope decisions 2026-05-10:
1. **Monorepo** at `https://github.com/alpacapurpura/luana-platform.git` (NOT 5 separate repos)
2. **Proprietary license** (private repo, "All rights reserved")
3. **GH Packages publishing DEFERRED to Story 9** (`luana-v0-1-0-publish`)

Plus anti-island scaffolding requirement (CODEOWNERS + PR template + ADR folder) added to Story 1 scope.

Plus 1 Claude sub sequential (was 5 parallel) — affects only outcome-level orchestration, not Story 1 internals.

Architect revised all 5 ready package files in-place per `/pm` directive 2026-05-10. Each file includes `revision_notes` frontmatter explaining v1→v2 deltas.

## Crash recovery (R27)

If session crashes mid-story: resume by reading `checkpoint.md` (this file) → identify `phase` → continue `next_action`. Latest artifact is `last_artifact`. Tickets in flight tracked via `T-{n}-impl-log.md`.

## Notes

- Pre-flight requirements ALL DONE (2026-05-10):
  - ✅ ADR-001 ratified by Chris
  - ✅ Repo `alpacapurpura/luana-platform` created (private, empty)
  - ✅ Scope decisions ratified (monorepo + proprietary + defer publishing)
- 4 Claude Code Max subs purchase deferred — 1 sub sequential build OK for Story 1
- Anti-island gates from day 1: CODEOWNERS + PR template + ADR README seeded in T-1
