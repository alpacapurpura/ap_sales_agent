---
story_id: luana-shared-lift
outcome: luana-platform-migration
state: developed                                 # ★ /dev-team closed all 17 tickets 2026-05-10 ★
phase: developed_awaiting_review
last_artifact: T-17 READMEs + DEFERRED-FILES.md
last_modified: 2026-05-10
next_action: "Chris triggers /auditor for Conv 3 review. state=developed→reviewing."
ratified_by_chris: true                         # pre-auth §7.2 lift mode
spawned_at: 2026-05-09
spawned_by: /pm + claude-opus-4-7
parallel_safe: false
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md
  - 03-arch.md                                  # ★ NEW 2026-05-11 ★
  - 04-validators.yaml                          # ★ NEW 2026-05-11 ★
  - 05-guidelines.md                            # ★ NEW 2026-05-11 ★
  - 06-tickets.yaml                             # ★ NEW 2026-05-11 ★
audit_iterations: 0
legacy_exempt: false
sequence_in_outcome: 2
blocks: [luana-iam-tenancy-content]
blocked_by: [luana-foundation]                  # done already; this block is satisfied
target_state: developed by 2026-05-25
estimated_complexity: high
estimated_tickets: 17                           # ★ /architect resolved 12-18 range → 17 tickets ★
surface: backend (9 Python cores + 6 TS packages = 15 total) + workspace integration
production_code: true                           # touches sales_agent + copilot consumers via shared (Stories 6/7 import)
owner_eligibility: [opus]                       # R23 — production code agentic consumers (foundation tickets)
deviations_from_spec:
  - "src/core/ lift into luana-core-platform (NOT in spec §2.2)"
  - "@luana/format extends to include lib/utils + lib/constants (NOT in spec §2.2 exact path)"
  - "@luana/schemas placeholder (lib/zod-schemas/ doesn't exist in AISALESHT)"
  - "4 module-coupled files deferred to Stories 6/7"
  - "9 Python packages (spec said 10 but mapping resolves to 9)"
  - "Cyclic dep platform↔llm (resolved via uv workspace sources, no refactor)"
estimated_tool_time_hours: 17
---

# Checkpoint — luana-shared-lift

State machine: `refining` → `refined` → **`ready`** (current) → `developing` → `developed` → `reviewing` → `done`.

## Ready package complete (2026-05-11)

/architect (claude-opus-4-7) produced full ready package:
- 03-arch.md (751 lines) — topology, lift order, per-package structure, workspace registration, import mapping, test strategy, arch fitness, pyproject.toml templates, deviations, research notes, cross-cutting concerns
- 04-validators.yaml (357 lines, schema v4) — 38 validators across non_functional / functional / agentic_eval / documentation categories
- 05-guidelines.md (344 lines) — patterns required/forbidden, files in scope (READ-ONLY AISALESHT + CREATE luana-platform), skills/rules to load, halt criteria, commit conventions
- 06-tickets.yaml (554 lines, 17 tickets) — DAG-ordered, owner_eligibility per ticket, validators_addressed, blocked_by/blocks, summary

## DAG topology (resolved)

```
T-1 (workspace prep)
  └─→ T-2 (foundation: platform + src/core — Opus)
        ├─→ T-3 (llm — closes cycle)        ─┐
        ├─→ T-4 (channels)                    │
        ├─→ T-5 (idempotency)                 │
        ├─→ T-6 (observability) ──┐           │
        ├─→ T-7 (events) ◄────────┘           ├─→ T-13 (integration — Opus)
        ├─→ T-8 (extraction)                  │      ├─→ T-14 (lint)
        ├─→ T-9 (compliance)                  │      ├─→ T-15 (no-publish)
        └─→ T-10 (billing) ◄──────┘           │      ├─→ T-16 (arch fitness)
                                              │      └─→ T-17 (READMEs)
  └─→ T-11 (TS foundation: design-tokens/hooks/format) ─┘
        └─→ T-12 (TS consumers: ui-kit/api-client/schemas) ─┘
```

## Bitácora
- 2026-05-09: spawned, parked (blocked_by Story 1)
- 2026-05-11: Story 1 done → unblocked. /pm self-drafted 01-spec.md per §7.2 pre-auth.
- 2026-05-11: /architect produced 03-arch + 04-validators + 05-guidelines + 06-tickets. state=refined→ready.
- 2026-05-10: /dev-team completed all 17 tickets. 728 Python tests pass, 39 TS tests pass. Pushed to alpacapurpura/luana-platform main (9615d47..4ca22c6). state=ready→developing→developed.

## Notes for /dev-team

- Ready package self-contained. Read 05-guidelines.md §3.3 BEFORE escalating "missing files" — 4 files explicitly deferred to Stories 6/7.
- Cyclic dep platform↔llm: T-2 declares stub, T-3 closes cycle, T-13 validates resolution.
- Owner: foundation tickets (T-2, T-13) are Opus; rest Sonnet per R23 lift-mode mechanical.
- AISALESHT untouched is HARD requirement — V-NF-4 verifies via git diff against base SHA. Capture base SHA before starting T-1.
