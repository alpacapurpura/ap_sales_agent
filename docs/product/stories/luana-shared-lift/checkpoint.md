---
story_id: luana-shared-lift
outcome: luana-platform-migration
state: refining
phase: outcome_decomposition
last_artifact: 00-story.md
last_modified: 2026-05-09
next_action: "/po opens 01-spec.md after Story 1 done. Lift mechanico de shared/ a 10 packages versionados"
ratified_by_chris: false
spawned_at: 2026-05-09
spawned_by: /pm + claude-opus-4-7
parallel_safe: false
blocked_reason: "Awaiting Story 1 (luana-foundation) done"
artifacts:
  - 00-story.md
audit_iterations: 0
legacy_exempt: false
sequence_in_outcome: 2
blocks: [luana-iam-tenancy-content]
blocked_by: [luana-foundation]
target_state: developed by 2026-05-25
estimated_complexity: high
estimated_tickets: 12-18
surface: backend (cores: observability, billing, compliance, idempotency, llm, events, channels, extraction, platform, ui-kit base)
production_code: true                           # touches sales_agent + copilot consumers via shared
owner_eligibility: [opus]                       # R23 — production code agentic consumers
---

# Checkpoint — luana-shared-lift

State machine: `refining` → `refined` → `ready` → `developing` → `developed` → `reviewing` → `done`.
Pending: 01-spec, 03-arch, 04-validators, 05-guidelines, 06-tickets.
