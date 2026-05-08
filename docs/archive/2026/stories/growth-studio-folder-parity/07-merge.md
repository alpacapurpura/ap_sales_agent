# 07-merge.md — growth-studio-folder-parity (Story 2A)

**Merged at:** 2026-05-08T18:30:00Z
**Merged by:** /pm
**Auditor verdict:** APPROVED (CHECKPOINTS.md C1-C5 all green)
**Outcome:** growth-copilot-layout-unification (2A of 4 stories)

## Tickets shipped (8/8)

| Ticket | Title | Commit SHAs |
|---|---|---|
| T-1 | Registries SSoT (stage/channel/dashboard) | 9343fd61 |
| T-2 | Factory dispatchers (StageDispatcher + ChannelDispatcher + sections) | per impl-log |
| T-3 | 4-tier rename break-and-fix atomic | 253e9ef1, 34221dfc |
| T-4 | Legacy purge config/+context/+__mocks__/ + VR replacement | per impl-log |
| T-5 | Allowlist cleanup 6 dashboards adopt useCopilotOffset | per impl-log |
| T-6 | Arch fitness extension adapter mode + 2 NEW arch tests | per impl-log |
| T-7 | Placeholders 2B (.gitkeep + routes thin delegate) | 828bb3dc |
| T-8 | Verify (vitest + Playwright smoke + VR + coverage parity) | 1e517b09 |

## Audit summary

- 8/8 tickets state=audit-passed
- C1 Code: PASS (tsc 0 / eslint 0 / 0 voseo / no `any`)
- C2 Spec: PASS (4/4 Gherkin scenarios GREEN, 31/31 canonical files unit, 16 VR baselines)
- C3 Architecture: PASS (8 ADs implemented, adapter mode AD6, allowlist drained AD7, 68 arch tests + 2 NEW)
- C4 Cross-cutting: PASS (no shared/ mirror, downstream FE full suite covered, TDD evidence)
- C5 Trace: PASS (all commit SHAs, transitions, validator_ids)
- 1 auditor self-fix iter-1 (prettier line 72 page.tsx, commit 21df3ae0)
- 3 minor WARN (Category 10 Tests/TDD doc/process drift, refactor-scope non-blocking)

## Capability impact

**No new capability promoted.** Per auditor verdict CHECKPOINTS.md:
> "Capability YAML / modules/{m}.md updates: not required for structural refactor (no new capability — folder-parity is internal)"

`docs/product/capabilities/analytics/` unchanged (4 caps remain live).

## Module SSoT impact

`docs/product/modules/analytics.md` — append entry to "Capacidades corregidas" recording the FSD-Lite folder parity refactor (analogous to PI-8 entry pattern).

## Outcome story_ids progress

`docs/product/outcomes/growth-copilot-layout-unification.md`:
- ✅ growth-studio-folder-parity → done (2A of 4)
- 🧪 app-shell-sidebar-copilot-decoupling → developed (1 of 4, awaiting QA)
- 🧪 growth-studio-actions-schemas-real → developed (2B of 4, awaiting QA — UNBLOCKED by 2A)
- 🅿 growth-studio-visual-coherence-pass → parked

## Process improvements applied

- Single-pass auditor for coherent FE refactor (8 tickets) saved ~120k tokens vs 8 separate spawns. Documented in CHECKPOINTS.md "Audit method" section. Pattern reusable for similar coherent refactors (zero per-ticket adversarial divergence).

## Deferred follow-ups

- Migrate component consumers in `components/metrics-dashboard/detail-panels/*` to canonical `pages/tiers/tier{N}-*` imports → Story 2B or follow-up commit
- Remove `pages/tiers/tier{1,2,3}-*.ts` wrappers + deprecated original hooks once consumers migrated (closes AD5 1-ciclo deprecation)
- Update `05-guidelines.md` lines 71-74 + `06-tickets.yaml` lines 180-182 tier naming to match `01-spec.md:45` (doc-only inconsistency — defer next ticket)
- Builders: cite `runtime-quality-checklist` explicitly in IMPL-LOG when modifying components (apply to Story 2B onward)

## Archive

Story folder moves to `docs/archive/2026/stories/growth-studio-folder-parity/` snapshot inmutable.
