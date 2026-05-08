# 07-merge.md — growth-studio-actions-schemas-real (Story 2B)

**Merged at:** 2026-05-08T19:30:00Z
**Merged by:** /pm
**Auditor verdict:** APPROVED (CHECKPOINTS.md C1-C5 all green; 3 sub-auditors PASS)
**Outcome:** growth-copilot-layout-unification (2B of 4 stories)

## Tickets shipped (7/7)

| Ticket | Surface | Production | Title | Notes |
|---|---|---|---|---|
| T-1 | BE | false | 3 copilot tools + DTOs + EtlRefreshGuard | REPLACE legacy `get_funnel_metrics`, NO new endpoints (REUSE 4) |
| T-2 | FE | false | 5 action React components + 4 zod schemas + registry | mirror brand-studio pattern, cross-stack contract test |
| T-3 | AGENTIC | true | Tool registry + golden update | R23 Opus 4.7 builder confirmed |
| T-4 | AGENTIC | true | 3 voice fidelity eval goldens | R23 Opus 4.7 builder confirmed |
| T-5 | BE | false | Arch fitness extension | +22 NEW arch tests (939→961) |
| T-6 | FE | false | Playwright smoke + VR baselines | playground/growth-studio-actions-test/ |
| T-7 | BE | false | Docs + verify | full suite GREEN |

## Audit summary

- 7/7 tickets state=audit-passed
- BE: PASS (1 informational WARN Cat 12 self-fixed iter-1 — docstring clarification)
- FE: PASS (0 FAIL, 0 WARN)
- AGENTIC: PASS (1 WARN note Cat 2 sync→async bridge, deliberate pattern)
- C1-C5: ALL APPROVED
- R23 enforcement confirmed (T-3 + T-4 commits authored Opus 4.7)
- R3 downstream regression CLEAN (4007+ BE + 800 FE + 961 arch tests GREEN)
- 1 self-fix iter-1 (etl_refresh_guard.py docstring "Composes" → "Duplicates" + bounded scope rationale)

## Capability impact

**NEW capability promoted:** `docs/product/capabilities/analytics/growth-studio-copilot-actions.yaml` (status=live, story_introduced=growth-studio-actions-schemas-real, date_introduced=2026-05-08).

`docs/product/modules/analytics.md` capability auto-list refresh via reconcile_capabilities.py.

## Outcome story_ids progress

`docs/product/outcomes/growth-copilot-layout-unification.md`:
- ✅ growth-studio-folder-parity → done (2A — merged 2026-05-08)
- ✅ growth-studio-actions-schemas-real → DONE 2026-05-08 (2B)
- 🧪 app-shell-sidebar-copilot-decoupling → developed (1 of 4, awaiting QA)
- 🅿 growth-studio-visual-coherence-pass → parked

## Process learnings (cardinal decision)

**Bounded mirror tolerance pattern** — 1-consumer parallel implementation of shared abstraction is OK when arch ratifies. Lift to shared on 3rd consumer threshold. Precedent: `EtlRefreshGuard` (analytics) vs `OutboundRateLimiter` (shared/billing/) — both implement Redis sliding-window mechanics independently. Documented in `learnings.md` 2026-05-08 entry.

## Deferred follow-ups

- Weekly LLM judge cron wiring for voice fidelity goldens
- Shared voseo glossary lift across eval golden files
- 3rd sliding-window consumer trigger → shared `BaseSlidingWindowGuard` lift refactor
- Migrate component consumers in `components/metrics-dashboard/detail-panels/*` to canonical `pages/tiers/tier{N}-*` (carry-over from Story 2A)

## Archive

Story folder moves to `docs/archive/2026/stories/growth-studio-actions-schemas-real/` snapshot inmutable.
