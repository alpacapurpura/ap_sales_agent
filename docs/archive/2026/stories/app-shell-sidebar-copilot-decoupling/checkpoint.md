---
story_id: app-shell-sidebar-copilot-decoupling
outcome: growth-copilot-layout-unification
state: done
phase: MERGED
last_artifact: CHECKPOINTS.md
last_modified: 2026-05-08T20:30:00Z
next_action: "Story merged. Archive scheduled. Outcome growth-copilot-layout-unification 3/3 active stories DONE (4th parked)."
audit_started_at: 2026-05-08T19:45:00Z
audit_started_by: /auditor
audit_verdict: APPROVED
audit_verdict_at: 2026-05-08T20:15:00Z
merged_at: 2026-05-08T20:30:00Z
merged_by: /pm
build_started_at: 2026-05-07T22:30:00Z
build_started_by: /dev-team
ratified_by_chris: true
ratified_at: 2026-05-07T04:15:00Z
ready_at: 2026-05-07T05:55:00Z
spawned_at: 2026-05-06T22:54:54Z
spawned_by: /po (sesión refining outcome unification 2026-05-06)
parallel_safe: true
parallel_safe_with: ["growth-studio-folder-parity"]
blocked_reason: null
audit_iterations: 0
hotfix_metadata:
  repro_verified: true
  repro_command: "chrome-devtools-verify subagent — 14 screenshots /tmp/live-repro/sidebar-copilot/, 5 viewports (500/768/1024/1440/1920) × 5 studios (offer/brand/growth/sales/settings) × 3 copilot states. See 00-live-repro.md for full evidence."
  diagnosis_validates_handoff: false
  diagnosis_correction: "Original handoff framing 'sidebar global ↔ copilot bar overlap z-index' refuted by live repro — overlap=0px in EVERY measured cell. Real bug = content area starvation (`main flex-1 min-w-0` no floor; worst 52px @ 768×expanded×open) + mutex absence (AppSidebar.isCollapsed and CopilotStore.isOpen independent) + useCopilotOffset drift (hook returns 380/60/0; CopilotSidebar grid renders 460/680/60; all dialogs/sheets mis-centered 80-220px) + mobile gaps (no left drawer for AppSidebar, no FAB to summon copilot, hamburger sin aria-label)."
---

# Story scope (post live repro + diagnosis correction)

**Tipo:** service-story (refactor shell layout cross-app)
**Skill spec:** `/po` (no `/po-ux` — bug-fix shell, no CRUD UI std)
**Module primario:** `shared` (layout shell) + `copilot` (drawer/widths SSoT)

## Problema (live evidence — see 00-live-repro.md)

Bug NO es z-index overlap. Live repro confirma overlap=0px en TODAS las
combinaciones medidas. Real root cause:

1. **`main` element es `flex-1 min-w-0`** sin floor → CopilotSidebar
   consume content space hasta degradar main. Worst case: viewport 768 ×
   sidebar expandido × copilot open = main 52px (catastrofico).
2. **AppSidebar.isCollapsed y CopilotStore.isOpen independientes** —
   sin mutex policy auto-collapse cuando ancho insuficiente.
3. **`useCopilotOffset` hook miente por 80-220px** vs CopilotSidebar grid
   widths reales (hook: 380/60/0; grid: 460/680/60). Todos modals/sheets
   mis-centered.
4. **Mobile <768:** AppSidebar carece left drawer (solo topbar 40px sin
   aria-label), no FAB para reabrir copilot.
5. **Z-index ladder undocumented** — varios z-50 empatados.

Cross-studio (offer/brand/growth/sales/settings/connections/scheduling).

## Solution (Chris ratified 2026-05-07)

Refactor layout shell parent que centraliza chrome computation.

Workstreams (11 identificados — architect decide split en `06-tickets.yaml`):
1. `<DashboardShell>` parent component
2. `useShellMutex` hook + zustand store
3. `useViewport` hook (si no existe)
4. `copilot-shell-widths.ts` SSoT + refactor consumers
5. `lib/tokens/z-index.ts` SSoT
6. AppSidebar mobile drawer (NEW Sheet izquierdo)
7. AppSidebar consume offsets DashboardShell
8. CopilotFAB component (NEW)
9. Arch test rename + scope ampliado (`test-shell-copilot-offset.test.ts`)
10. ESLint custom rules (no-shadowing-copilot-offset, use-shell-mutex)
11. Visual regression baselines + Playwright smoke (≥96 assertions)

## Spec status

`01-spec.md` v2 escrito 2026-05-07 03:55Z post live repro + diagnosis
correction. 4 scenarios corregidos:
- Scenario 1 (happy): min-content-width-enforced-via-mutex-and-floor
- Scenario 2 (negative): useCopilotOffset-aligned-with-CopilotSidebar-ssot
- Scenario 3 (edge): mobile-mutex-drawers-and-fab-and-a11y
- Scenario 4 (adversarial): arch-fitness-extends-shell-zindex-tokens-and-rejects-shadowing

10 open questions pendientes ratificación Chris.

## Bitácora

- 2026-05-06 22:54 — `/po` (sesión refining unification) creó folder +
  checkpoint.md (state=refining, hipótesis z-index overlap).
- 2026-05-07 03:00 — `/po` redacta `01-spec.md` v1 con hipótesis pre-repro
  (z-index overlap + AppSidebar consume useCopilotOffset).
- 2026-05-07 03:00 — Spawn subagent `chrome-devtools-verify` background
  para live repro 4 viewports × 8 studios × 3 copilot states.
- 2026-05-07 03:50 — Subagent completa `00-live-repro.md` con 14
  screenshots + numerical evidence + DOM dumps. **Diagnosis correction
  CRÍTICA**: bug NO es z-index overlap (overlap=0px siempre). Real = 4
  issues distintos (content starvation + mutex absence + offset drift +
  mobile gaps).
- 2026-05-07 03:55 — `/po` reescribe `01-spec.md` v2 con scenarios
  corregidos. Update outcome doc framing. Add idea
  `sales-inbox-responsive-collapse` ideas-pool. Phase=PO_DRAFT_V2_AWAITING_RATIFICATION.

## Notas

- `parallel_safe: true` con `growth-studio-folder-parity` (story 2A) — no
  overlap territorial (story 1 = shell + copilot widths SSoT; 2A =
  growth-studio folders + factory).
- NO blocks 2A ni 2B.
- Story 1 puede beneficiar 2A: el rename `test-growth-studio-copilot-offset`
  → `test-shell-copilot-offset` (story 1) destrabea cleanup allowlist
  growth-studio (story 2A) — coordinación architect.
- Architect Opus 4.7 OBLIGATORIO post-ratification (refactor shell
  cross-cutting, alto ROI).
- Single sub-architect `/architect-fe` (sin BE ni agentic surfaces).
