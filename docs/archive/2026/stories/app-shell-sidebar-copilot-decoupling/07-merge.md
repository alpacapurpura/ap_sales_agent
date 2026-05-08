# 07-merge.md — app-shell-sidebar-copilot-decoupling (Story 1)

**Merged at:** 2026-05-08T20:30:00Z
**Merged by:** /pm
**Auditor verdict:** APPROVED (CHECKPOINTS.md C1-C5 all PASS, 11/12 categories PASS + 1 N/A forms)
**Outcome:** growth-copilot-layout-unification (1 of 4 stories — final active story; 4th parked)

## Tickets shipped (9/9)

| Ticket | Title | ADs | State |
|---|---|---|---|
| T-1 | DashboardShell pure Server Component | AD1+AD4+AD5+AD6 | audit-passed |
| T-2 | copilot-shell-widths SSoT | AD6 | audit-passed |
| T-3 | useCopilotOffset hook unified | AD3 | audit-passed |
| T-4 | min-content-width floor + mutex policy | AD2+AD4+AD8 | audit-passed |
| T-5 | mobile mutex + zustand factory tenant-keyed | AD7+AD8+AD9 | audit-passed |
| T-6 | CopilotFAB persistent reopener + aria-labels | AD5 | audit-passed |
| T-7 | arch fitness 4 NEW tests + 2 ESLint custom rules | AD5+AD6 | audit-passed |
| T-8 | Playwright VR multi-viewport + axe-core | AD10 | audit-passed |
| T-9 | Shadcn primitives migration (Phase 10) | AD5 | audit-passed |

Commits referenced: 6f4c9ab7, 0d8701c2, 6b691987, a49bfbd9, 40c30328, 55f3de42 (per impl-logs).

## Audit summary

- 9/9 tickets state=audit-passed
- C1 Code: PASS (tsc 0, eslint 0, 30 arch tests, react-perf baseline -197)
- C2 Spec: PASS (4 Gherkin scenarios validated, 10 ADs + 7 post-architect AD-Q implemented)
- C3 Architecture: PASS (Hybrid Server+Client AD1, SSoT lifts consolidated, 3 NEW arch tests)
- C4 Cross-cutting: PASS (Spanish neutro aria-labels AD9, zustand `shell-mutex-${tenantId}` factory)
- C5 Trace: PASS (14 chrome-devtools-verify screenshots, allowlists drained scope-keyed)
- 0 self-fix iter required (clean approval)
- 4 informational non-blockers (CopilotRail mutex transition, 4 Playwright fixme headless-only, 3 Shadcn UI legacy entries, COPILOT_WIDTHS naming)

## Capability impact

**No new capability promoted.** Per pattern (similar to Story 2A): structural refactor cross-app, no user-facing capability change. Shell SSoT (`copilot-shell-widths.ts`), mutex policy, content floor, z-index ladder are infrastructure improvements that benefit ALL studios but don't introduce a new "operable" capability per se.

`docs/product/modules/copilot.md` — narrative entry recommended noting cross-studio shell unification (deferred — not blocking merge).

## Outcome story_ids progress (FINAL)

`docs/product/outcomes/growth-copilot-layout-unification.md`:
- ✅ growth-studio-folder-parity → DONE 2026-05-08 (2A)
- ✅ growth-studio-actions-schemas-real → DONE 2026-05-08 (2B)
- ✅ app-shell-sidebar-copilot-decoupling → DONE 2026-05-08 (Story 1, FINAL)
- 🅿 growth-studio-visual-coherence-pass → parked (4th — pending future cycle)

**Outcome state:** 3/3 active stories DONE → outcome state can transition to `done` (1 parked story remains, optional reactivation).

## Success metrics (per outcome frontmatter)

- ✅ "main content width ≥720px en TODO studio @ viewport ≥1024px" (T-4 floor + AD2 mutex)
- ✅ "Mobile <768px AppSidebar y Copilot drawers mutuamente exclusivos; FAB copilot persistente; aria-labels" (T-5 + T-6)
- ✅ "useCopilotOffset hook y CopilotSidebar grid widths consumen mismas constantes SSoT (copilot-shell-widths.ts)" (T-2 + T-3)
- ✅ "Z-index ladder centralizado en lib/tokens/z-index.ts + arch test enforza" (T-7 test-zindex-tokens-only)
- ✅ "Agregar canal ficticio 'test-channel-x' a Growth Studio requiere ≤3 archivos nuevos + ZERO modificación a StageDispatcher/ChannelDispatcher" (Story 2A delivered)
- ✅ "Arch fitness test_studio_structure_parity verde para growth-studio (modo factory adaptado)" (Story 2A delivered)
- ✅ "Bowtie superior + métricas dashboard intactos pixel-perfect post-refactor" (Story 2A T-8 VR baselines)

**ALL 7 OUTCOME SUCCESS METRICS DELIVERED.**

## Process learnings

- Single-pass auditor for coherent FE refactor confirmed effective at 9-ticket scale (~75k tokens audit, vs ~270k if 9 separate spawns).
- Live verification via chrome-devtools-verify (14 screenshots) + axe-core + Playwright VR is the right gate combination for shell layout work.
- 4 Playwright `test.fixme` for headless-only Sheet portal issue documented as non-blocking when Chris ratifies real-browser validation. Pattern reusable.

## Deferred follow-ups

- CopilotRail.tsx — refactor internal state-cycling to flow through mutex (ratchet warn → error post-stabilization)
- 4 Playwright `test.fixme` headless investigation (Sheet primitive portal issue)
- 3 KNOWN_VIOLATIONS_SHADCN_UI (calendar/detail-panel/select) — separate Shadcn migration pass
- COPILOT_WIDTHS naming alignment with spec hint (`expanded/max` vs `OPEN_RAIL/OPEN_FULL`) — doc-only, optional

## Archive

Story folder moves to `docs/archive/2026/stories/app-shell-sidebar-copilot-decoupling/` snapshot inmutable.

## Outcome closure

After this merge, outcome `growth-copilot-layout-unification` has 3/3 active stories DONE. /pm should:
1. Update outcome frontmatter `state: done` (was: validated)
2. Append outcome closure entry to learnings.md
3. Optional: archive outcome doc to `docs/archive/2026/outcomes/` (or keep live if 4th parked story may reactivate)
