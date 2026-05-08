---
story_id: growth-studio-actions-schemas-real
outcome: growth-copilot-layout-unification
state: done
phase: MERGED
last_artifact: CHECKPOINTS.md
last_modified: 2026-05-08T19:30:00Z
next_action: "Story merged. Archive to docs/archive/2026/stories/growth-studio-actions-schemas-real/."
audit_started_at: 2026-05-08T18:35:00Z
audit_started_by: /auditor
audit_verdict: APPROVED
audit_verdict_at: 2026-05-08T19:20:00Z
merged_at: 2026-05-08T19:30:00Z
merged_by: /pm
ratified_by_chris: true
ratified_at: 2026-05-07T04:15:00Z
ready_closed_at: 2026-05-08T00:00:00Z
ready_closed_by: /architect (orchestrator) + /architect-be + /architect-fe + /architect-agentic (parallel sub-architects)
spawned_at: 2026-05-07T03:30:00Z
spawned_by: /po (sesión refining unification 2nd pass — split de growth-studio-architectural-parity)
parallel_safe: false
parallel_safe_with: []
blocked_reason: null
blocked_by: []
audit_iterations: 0
hotfix_metadata:
  repro_verified: false
  repro_command: null
  diagnosis_validates_handoff: null
---

# Story scope — Story 2B (real actions + real schemas)

**Tipo:** service-story (FE actions + zod schemas + BE copilot tools — sin UI change visible salvo cards en chat copilot)
**Skill spec:** `/po`
**Module primario:** `analytics` (FE: `frontend/src/features/growth-studio/`)
**Module secundario:** `copilot` (consumer + registry de las actions)

## State machine — refined → ready (2026-05-08)

`/architect` orchestrator spawned 3 sub-architects in parallel and consolidated outputs:
- `/architect-be` (Opus 4.7) — 3 tools + DTOs + EtlRefreshGuard composing OutboundRateLimiter + tenant isolation + No new endpoint added (REUSE 4 existing analytics endpoints)
- `/architect-fe` (Opus 4.7) — 5 action React components + 4 zod schemas + registry mirror brand-studio pattern + 2 SSoTs cross-stack contract test
- `/architect-agentic` (Opus 4.7) — 3 tools registered in `ANALYTICS_TOOLS` group + golden update + 3 voice fidelity eval goldens + R23 owner eligibility marked

Ready package shipped (4 archivos):
- `03-arch.md` — consolidated single source of truth
- `04-validators.yaml` — 4 categories (non_functional / functional / visual / agentic_eval) + cross_cutting_audits sub-category
- `05-guidelines.md` — patterns required + forbidden + skills/rules + files in scope
- `06-tickets.yaml` — 7 atomic tickets ordered (T-1 … T-7), R23 marked for AGENTIC tickets

## Dependencies status

| Dependency | Status | Confirmed by |
|---|---|---|
| Story 2A (`growth-studio-folder-parity`) | DONE | commit `1e517b09` (T-8 verify) + `828bb3dc` (T-7 placeholders shipped) |
| Story 1 (`app-shell-sidebar-copilot-decoupling`) | DONE | commit `b123d6da` (shell pattern + scope-keyed allowlists) |

`parallel_safe: false` historical — now obsolete because BLOCKED resolved. T-1 + T-2 within Story 2B can run in parallel (consume different surfaces). T-3..T-7 sequential per dependency graph in `06-tickets.yaml`.

## Key architectural decisions (recap)

1. **NO new analytics endpoints** — REUSE 4 existing (`/{stage}/overview`, `/{stage}/groups/{group_key}`, `/channel/{slug}/dashboard`, `/attraction/refresh/{channel_slug}`, `/catalog`).
2. **NO new rate limiter** — `EtlRefreshGuard` composes `OutboundRateLimiter` Redis pipeline pattern (anti-duplication compliance).
3. **`get_funnel_metrics` REPLACED atomically** in same commit (caller audit confirmed only 2 references).
4. **Adversarial defense** via Pydantic `extra="forbid"` + `Literal[...]` enum + zod `.strict()` parity.
5. **Cross-stack contract test** ensures BE Pydantic ↔ FE zod alignment via z.toJSONSchema().
6. **Agentic tickets** (T-3, T-4) `production_code: true` → R23 hard rule: Opus 4.7 builder.
7. **Tenant isolation** read from `get_tenant_id()` context — caller-supplied tenant blocked at Pydantic parse.
8. **Spanish neutro** user-facing across 5 action components; voseo lint catches at pre-commit.

## Bitácora

- 2026-05-07 03:30 — `/po` (sesión refining unification 2nd pass) creó folder + checkpoint.md (state=refining). Split de `growth-studio-architectural-parity` ratificado por Chris. Sequential dependency en 2A. Phase=PO_DRAFTING.
- 2026-05-07 04:15 — Chris ratificó spec (8 questions answered: 3 actions in scope, exportStageReport DROPPED, rate limit hardcoded 3/hour, REPLACE legacy strategy, 2 SSoTs contract test, mirror brand registry pattern). Phase=SPEC_RATIFIED, state=refined.
- 2026-05-08 00:00 — `/architect` orchestrator spawned `/architect-{be,fe,agentic}` in parallel; consolidated outputs into `03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml`. state=ready.

## Hand off

```
state: refined → ready  (architect closed 2026-05-08)
next: /dev-team takes T-1 (BE — 3 tools + EtlRefreshGuard) + T-2 (FE — 4 schemas + 5 actions) in parallel
       Then sequentially: T-3 (agentic Opus) → T-4 (agentic Opus) → T-5 → T-6 → T-7 (verify + capability promote)
```

## Notas

- 7 tickets within ≤10 cap (story scope healthy)
- Estimated total 14-22h
- T-3 + T-4 require Opus 4.7 (R23 hard rule)
- Other tickets (T-1, T-2, T-5, T-6, T-7) qualified for Sonnet/opencode
- Capability YAML `docs/product/capabilities/analytics/growth-studio-copilot-actions.yaml` will be created at merge (status=shipped) by PM via `reconcile_capabilities.py` + `generate_backlog.py` (R32 + R33)
