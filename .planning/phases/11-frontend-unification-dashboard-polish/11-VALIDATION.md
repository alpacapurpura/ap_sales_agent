---
phase: 11
slug: frontend-unification-dashboard-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
wave_0_plan_created: true
created: 2026-03-16
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Frontend-only phase (Vitest + React component testing).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest (React components) + no backend test changes for this phase |
| **Config file** | `frontend/vitest.config.mts` |
| **Quick run command** | `npm run test:unit -- marketing-studio` (subset) |
| **Full suite command** | `npm run test` (all frontend) |
| **Estimated runtime** | ~10 seconds (quick) / ~30 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `npm run test -- marketing-studio --run` (unit tests only, <10s)
- **After every plan wave:** Run `npm run test` (full frontend suite, <30s)
- **Before `/gsd:verify-work`:** Full suite must be green + manual visual regression check on staging
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-00-01 | 00 | 0 | Nyquist | unit | `npm run test -- DetailSkeleton --run` | ✅ Wave 0 | ⬜ pending |
| 11-00-02 | 00 | 0 | Nyquist | unit | `npm run test -- StageCard --run` | ✅ Wave 0 | ⬜ pending |
| 11-00-03 | 00 | 0 | Nyquist | unit | `npm run test -- MetricSidebar --run` | ✅ Wave 0 | ⬜ pending |
| 11-00-04 | 00 | 0 | Nyquist | unit | `npm run test -- useAttractionDetail --run` | ✅ Wave 0 | ⬜ pending |
| 11-01-01 | 01 | 1 | UI-01 | unit | `npm run test -- marketing-studio --run` | ✅ From Wave 0 | ⬜ pending |
| 11-01-02 | 01 | 1 | UI-02 | unit | `npm run test -- marketing-studio --run` | ✅ From Wave 0 | ⬜ pending |
| 11-01-03 | 01 | 1 | UI-03 | unit | `npm run test -- marketing-studio --run` | ✅ From Wave 0 | ⬜ pending |
| 11-02-01 | 02 | 2 | UI-01 | unit | `npm run test -- marketing-studio --run` | ✅ From Wave 0 | ⬜ pending |
| 11-02-02 | 02 | 2 | UI-04 | unit | `npm run test -- marketing-studio --run` | ✅ From Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

**Status: Plan Created (11-00-PLAN.md)**

Wave 0 scaffolding tasks will create these test files:

- [x] **PLAN**: `11-00-PLAN.md` created with 4 scaffolding tasks
- [ ] **EXECUTE**: `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/__tests__/DetailSkeleton.test.tsx` — covers UI-01 loading pattern consistency
- [ ] **EXECUTE**: `frontend/src/features/marketing-studio/components/metrics-dashboard/__tests__/StageCard.test.tsx` — covers UI-02 real data display from API hooks
- [ ] **EXECUTE**: `frontend/src/features/marketing-studio/components/metrics-dashboard/sidebar/__tests__/MetricSidebar.test.tsx` — covers sidebar interaction and drill-down
- [ ] **EXECUTE**: `frontend/src/features/marketing-studio/hooks/__tests__/useAttractionDetail.test.ts` — covers API hook pattern with parallel calls
- [ ] Framework: Vitest already in place (vitest.config.mts exists). No changes needed.

**Execution order:**
1. Run `/gsd:execute-phase 11 --wave 0` to scaffold all 4 test files
2. Verify with `npm run test -- marketing-studio --run` (should discover all 4 files, 0 errors)
3. Set `wave_0_complete: true` in VALIDATION.md frontmatter after execution passes
4. Wave 1 (Plan 11-01) can then execute with confidence that test targets exist

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stage colors WCAG AA contrast | UI-01 | Color palette choices require human visual validation against WebAIM contrast checker | Run each stage color (#hex) through https://webaim.org/resources/contrastchecker/ |
| Responsive layout on mobile (< 640px) | UI-01 | Sidebar drawer width, overflow behavior, touch target sizing require device testing | Test on iPhone SE simulator: sidebar opens, scrolls, closes without layout overflow |
| Count-up animation smoothness | Visual Polish | Animation timing and easing subjective; requires human visual assessment | Load dashboard, watch KPI numbers count up; should feel smooth at 60fps, not janky |
| Channel icon instant recognition | UI-04 | Icons must be recognizable by non-technical users without labels | Show icon grid to non-eng team member; they should identify Meta, Google, TikTok, YouTube without reading tool tips |

---

## Validation Sign-Off

- [x] Wave 0 plan created (11-00-PLAN.md) with 4 test scaffolding tasks
- [ ] All 4 Wave 0 test files exist (after execution)
- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (all 4 test files in .test.tsx files)
- [ ] No watch-mode flags in production commands
- [ ] Feedback latency < 30s (unit tests quick run)
- [ ] `nyquist_compliant: true` set in frontmatter after full phase execution
- [ ] `wave_0_complete: true` set in frontmatter after Wave 0 execution

**Approval:** Wave 0 plan created; pending execution

---

*Phase: 11-frontend-unification-dashboard-polish*
*Validation strategy updated: 2026-03-16*
*Wave 0 plan added: 2026-03-16*
