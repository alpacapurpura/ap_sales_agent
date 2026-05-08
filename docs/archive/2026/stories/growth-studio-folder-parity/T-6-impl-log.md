# T-6 Impl Log — growth-studio-folder-parity

**Ticket:** T-6 — Phase 6 Arch fitness extension adapter mode + 2 NEW arch tests
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T22:30:00Z
**Estimate:** 2h
**Acceptance validators:** fe_arch_fitness_growth, fe_arch_fitness_full, scenario_2_arch_test_hardcoded
**Depends on:** T-5 (DONE — commit 36cbb548)

## Plan

Extend test-studio-structure-parity adapter mode + 2 NEW arch tests bloquean hardcoded slugs.

- MODIFY `frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts` — STUDIO_PAGE_DIRS per-studio canonical config (factory propia adapter mode):
  - brand: section-slugs+SectionDispatcher
  - offer: idem
  - growth: stage-slugs+StageDispatcher+channel-slugs+ChannelDispatcher
- NEW `frontend/src/__tests__/architecture/test-no-hardcoded-stage-list.test.ts` — scan growth-studio source for array literals matching `["atraccion-captura", ...]` o equivalentes; permitir SOLO en `stage-registry.ts`
- NEW `frontend/src/__tests__/architecture/test-no-hardcoded-channel-slugs.test.ts` — análogo para channel slugs canonical permitir SOLO en `channel-registry.ts`

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | Always mandatory — loaded runtime-quality-checklist | Array-literal regex detection pattern, allowlist ratchet, ESLint override justifications |
| `tessl__react-patterns` | Always mandatory — baseline checks | No client components in arch tests; pure fs/path Node.js code |
| `tessl__vitest` | New test files created | Vitest describe/it/expect pattern; no async needed (sync fs reads) |

## §11 gaps from CONTEXT-BRIEF.md
None. Faithfulness flag: clean.

## Iteration log

### Iter 1 — TDD RED (initial scan)

Wrote `hasHardcodedStageArray` counting slugs anywhere in file content. Result: false positives — `GrowthStudioContext.tsx` (5/5 via object key-value map) and `StageDispatcher.tsx` (3/5 via Record keys). Both legitimate uses.

**Fix:** Changed detection to scan ARRAY LITERAL brackets only `[([^\[\]]*)]`. Each object property `"slug": [...]` has only one channel in its inner array → not flagged. Only a combined `["slug1","slug2","slug3"]` array triggers.

### Iter 2 — GREEN (array-literal regex)

Switched to array bracket scan. Re-ran validators: 13/13 PASS. Channel test: same pattern applied, ChannelDetailSidebar false positives eliminated (each channel's array bracket is independent).

### Iter 3 — ESLint clean

Auto-fix prettier formatting. Manual fix: `GROWTH_STUDIO_FEATURE` constant (sonarjs/no-duplicate-string), `// eslint-disable-next-line no-useless-escape` + `const [, arrayContent] = match` (prefer-destructuring). Final: 0 errors, 0 warnings on all 3 files.

### Final gate results

- TSC: 0 errors
- ESLint 3 files: 0 errors, 0 warnings
- Vitest 3 validators: 13/13 PASS
- Vitest full arch suite: 61/61 PASS (27 test files)

## Commit

TBD (pending push)
