# T-5 Impl Log — growth-studio-folder-parity

**Ticket:** T-5 — Phase 5 Allowlist cleanup 6 dashboards adopt useCopilotOffset
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T22:00:00Z
**Estimate:** 2h
**Acceptance validators:** scenario_4_ratchet_fsd_arch_adversarial, fe_test_shell_copilot_offset, fe_arch_fitness_full
**Depends on:** T-4 (DONE — commit 8d228af7 / 54b31642)
**Cross-story dependency:** story-1::T-7 (rename + scope-keyed allowlists) — NOT YET LANDED. Story 1 currently at T-4 done.

## Plan

6 dashboards adoptan useCopilotOffset hook. Drain allowlist post-adoption.

GATE: si story-1 T-7 LANDED (rename test-growth-studio → test-shell-copilot-offset.test.ts) → drain `KNOWN_VIOLATIONS_GROWTH = new Set()` en test-shell-copilot-offset.
GATE: si story-1 T-7 NOT YET LANDED (current state) → drain `KNOWN_VIOLATIONS = new Set()` en test-growth-studio-copilot-offset.test.ts (single set). Story 1 T-7 rename later splits scope-keyed.

- MODIFY 6 dashboards (5 sidebar dashboards + ChannelConnectionModal): adopt useCopilotOffset hook + apply paddingRight or right offset to fixed/portal elements
- Drain allowlist
- Tests vitest unit por dashboard verify hook consumption

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | Boundary matrix, arch fitness ratchet pattern | `@/hooks/` = global hooks, valid import from `features/growth-studio` |
| `tessl__react-patterns` | Baseline: accessible markup, loading/empty states | Existing dashboards compliant; adoption is `style` prop only |
| `tessl__vitest` | Mock patterns for Radix Portal, Clerk, React Query in jsdom | `vi.mock` hoisting + `importOriginal` partial Radix mock |

## Iteration log

### Iter 1 — RED (drain allowlist)

Modified `test-growth-studio-copilot-offset.test.ts`: `KNOWN_VIOLATIONS = new Set([])` (was 6 entries). Test fails: 6 violations detected (none of the 6 components imported `useCopilotOffset`).

### Iter 2 — GREEN (adopt hook in 6 components)

Modified files:
- `sidebar/youtube-organic/YouTubeDashboard.tsx` — import + hook call + `paddingRight` on fixed container
- `sidebar/mail/MailDashboard.tsx` — same pattern
- `sidebar/meta-ads/MetaAdsDashboard.tsx` — same pattern
- `sidebar/ig-organic/IgOrganicDashboard.tsx` — same pattern
- `sidebar/website/WebsiteDashboard.tsx` — same pattern
- `channel-widgets/ChannelConnectionModal.tsx` — import + hook call + `marginRight` on `DialogPrimitive.Content` (centered modal uses `marginRight` not `paddingRight`)

Arch fitness test GREEN: `test-growth-studio-copilot-offset.test.ts` 1 passed.

### Iter 3 — Unit tests written + fixed

New file: `src/features/growth-studio/__tests__/dashboards-copilot-offset-adoption.test.tsx` (9 tests).

Mocking challenges resolved:
- **MailDashboard**: Added `@clerk/nextjs` mock + `use-mail-dashboard` mock — tab sub-components call `useAuth` directly.
- **MetaAdsDashboard**: Changed mocks from `{ data: null }` to `{ data: undefined }` — `computeMetaAdsOnboardingTrigger` guards via `!== undefined`. Provided full `NoticesSummary` shape for `useMetaAdsNotices` (dashboard accesses `.perTabCounts.campanas` + `.maxSeverityPerTab`). Added all `offer-association-api` hooks to mock (`useMetricsByOffer`, etc.) since `ResumenTab` uses them.
- **ChannelConnectionModal**: `DialogOverlay` and `DialogPrimitive.Content` both have `fixed` class. Used `el.className.includes("grid")` to target Content uniquely (Content has Tailwind `grid` class, Overlay does not).

Final: 9/9 tests pass.

## Quality Gates

| Gate | Result |
|---|---|
| TypeScript `tsc --noEmit` | PASS — 0 errors |
| ESLint (0 errors) | PASS — 0 errors, 11 warnings in test file (import/order: vi.mock must precede imports per Vitest hoisting — acceptable) |
| Vitest 277 test files | PASS — 2071 tests passed |
| Architecture fitness (25 test files, 51 tests) | PASS — all green |
| Coverage | PASS — 34% / 29% / 30% / 34% (all > 20% threshold) |
| Warning baselines | SHRUNK — jsdoc 491 < 616; react-perf 1298 < 1509 |
