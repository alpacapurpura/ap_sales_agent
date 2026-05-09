---
story_id: luana-foundation
outcome: luana-platform-migration
state: refining
phase: outcome_decomposition
last_artifact: 06-tickets.yaml
last_modified: 2026-05-09T19:00:00Z
next_action: "DRAFT ready package complete. Awaiting Chris ratification Sunday 2026-05-11 — read 01-spec + 03-arch + 04-validators + 05-guidelines + 06-tickets, ratify or request changes. State refining → refined → ready when ratified. Then /dev-team picks T-1."
ratified_by_chris: false                        # ★ DRAFT ready package pending Chris ratification ★
spawned_at: 2026-05-09
spawned_by: /pm + claude-opus-4-7
parallel_safe: false                            # Sem 1 — no other Luana stories concurrent until foundation stable
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md             # po_version=1 DRAFT 2026-05-09 (Claude Opus 4.7 as /po proxy)
  - 03-arch.md             # arch_version=1 DRAFT 2026-05-09 (Claude Opus 4.7 as /architect proxy)
  - 04-validators.yaml     # schema v4, 22 validators (18 must_pass)
  - 05-guidelines.md       # patterns required + forbidden + skills + owner routing
  - 06-tickets.yaml        # 11 tickets DAG, ~7h Sonnet tool-time
audit_iterations: 0
legacy_exempt: false
sequence_in_outcome: 1
blocks: [luana-shared-lift]
blocked_by: []
target_state: developed by 2026-05-18
estimated_complexity: medium
estimated_tickets: 8-12
surface: infra (no code lift)
production_code: false                          # infra setup, not agentic prod code
owner_eligibility: [opencode, sonnet, opus]    # mechanical setup work
---

# Checkpoint — luana-foundation

## State machine

`refining` (current) → `refined` (post Chris ratify spec) → `ready` (post /architect emits package) → `developing` (/dev-team picks T-1) → `developed` (validators GREEN) → `reviewing` (Chris triggers /auditor) → `done` (auditor APPROVED + capability promoted)

## Active artifacts

- `00-story.md` — story definition (drafted 2026-05-09)
- _pending_ `01-spec.md` (service-style spec)
- _pending_ `03-arch.md` (architecture)
- _pending_ `04-validators.yaml` (must_pass:true commands)
- _pending_ `05-guidelines.md` (patterns + scope)
- _pending_ `06-tickets.yaml` (atomic tickets)

## Crash recovery (R27)

If session crashes mid-story: resume by reading `checkpoint.md` (this file) → identify `phase` → continue `next_action`. Latest artifact is `last_artifact`. Tickets in flight tracked via `T-{n}-impl-log.md`.

## Notes

- Pre-flight requirement: ADR-001 ratified by Chris
- Pre-flight requirement: GitHub Org `luana-platform` created by Chris (manual, GUI)
- Pre-flight requirement: 4 Claude Code Max subs purchased (5 total)
