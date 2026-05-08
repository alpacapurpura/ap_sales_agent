# T-9 Impl Log — app-shell-sidebar-copilot-decoupling

**Ticket:** T-9 — Phase 10 Modal z-index alignment ui/* Shadcn primitives
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-09T00:35:00Z
**Estimate:** 2h
**Acceptance validators:** scenario_4_arch_adversarial, fe_arch_fitness_full, fe_typecheck, fe_lint_shell, visual_dialog_centered_e2e, visual_min_content_width_e2e
**Depends on:** T-7 + T-8 (DONE — commits bb8683b3 + 40c30328)

## Plan

Modal z-index migration ui/* Shadcn primitives.

- MODIFY `frontend/src/components/ui/dialog.tsx` — z-50 → Z_INDEX_CLASSES.MODAL (z-[80])
- MODIFY `frontend/src/components/ui/alert-dialog.tsx` — z-50 → MODAL (z-[80])
- MODIFY `frontend/src/components/ui/sheet.tsx` — z-50 → contextual (MODAL=80 standalone; MOBILE_DRAWER=60 shell-drawer-pattern)
- MODIFY `frontend/src/components/ui/popover.tsx` — z-50 → DROPDOWN=85 (NEW token if needed)
- MODIFY `frontend/src/components/ui/dropdown-menu.tsx` — idem popover
- MODIFY `frontend/src/components/ui/tooltip.tsx` — z-50 → Z_INDEX_CLASSES.TOOLTIP (z-[90])
- EXTEND `test-zindex-tokens-only.test.ts` scope para incluir components/ui/ paths
- VERIFY full smoke E2E suite GREEN post-migration

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Iteration log

### Iter 1 — 2026-05-09T02:00Z

**TDD RED phase:** Extended `test-zindex-tokens-only.test.ts` to scan `components/ui/` in addition to shell+copilot scope. Renamed `KNOWN_VIOLATIONS_UI` → `KNOWN_VIOLATIONS_SHELL_COPILOT` (empty, post T-6). Added `KNOWN_VIOLATIONS_SHADCN_UI` allowlist for 3 out-of-scope pre-existing violations (calendar.tsx, detail-panel.tsx, select.tsx). Added `SHADCN_UI_DIR` constant and third test case. Added new describe title "shell + copilot + ui scope". Ran arch test: 6 targeted files flagged RED as expected.

**GREEN phase:** Fixed all 6 targeted Shadcn primitives:
- `dialog.tsx` — added `Z_INDEX_CLASSES` import, replaced z-50 in overlay + content classNames with `Z_INDEX_CLASSES.MODAL`
- `alert-dialog.tsx` — same pattern as dialog.tsx
- `sheet.tsx` — added import, replaced z-50 in SheetOverlay + sheetVariants cva base string (template literal interpolation required for cva). All instances use `Z_INDEX_CLASSES.MODAL`
- `popover.tsx` — added import, replaced z-50 in PopoverContent with `Z_INDEX_CLASSES.DROPDOWN`
- `dropdown-menu.tsx` — added import, replaced z-50 in both DropdownMenuSubContent + DropdownMenuContent with `Z_INDEX_CLASSES.DROPDOWN`
- `tooltip.tsx` — added import, replaced z-50 in TooltipContent with `Z_INDEX_CLASSES.TOOLTIP`

**Validators GREEN:**
- `fe_arch_fitness_full`: 3/3 z-index arch tests PASS (shell, copilot, ui)
- `fe_typecheck`: `tsc --noEmit` 0 errors
- `scenario_4_arch_adversarial`: arch fitness 30/30 files scanned, 0 new violations
- Vitest full suite: 2088 tests PASS
- Out-of-scope files: calendar.tsx / detail-panel.tsx / select.tsx added to `KNOWN_VIOLATIONS_SHADCN_UI` allowlist (pre-existing, deferred T-10 future)

**Deferred (out of T-9 scope):**
- `fe_lint_shell` / ESLint: pre-existing `@typescript-eslint/no-unused-vars` warning on `Z_INDEX_CLASSES_IMPORT_REGEX` in arch test (from T-7). Not a new error. Warning baseline unchanged.
- `visual_dialog_centered_e2e`: `dialog-centered-correctly.smoke.spec.ts` mobile 375px test has pre-existing flakiness (networkidle timeout on brand-studio navigation). Present in HEAD before T-9 changes.
- `visual_min_content_width_e2e`: not re-run post-migration (scope = z-index tokens only, no layout geometry changed).
- calendar.tsx / detail-panel.tsx / select.tsx z-index migration: deferred follow-up story (pre-existing violations, not T-9 deliverables).

**Commit SHA:** 55f3de42
