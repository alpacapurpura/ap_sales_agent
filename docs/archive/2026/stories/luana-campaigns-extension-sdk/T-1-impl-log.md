---
ticket: T-1
title: "Update luana-platform workspace registration for Story 8 — 3 NEW Python packages alphabetical"
story_id: luana-campaigns-extension-sdk
completed_at: 2026-05-12
iteration: 1
commit: ae8cb96
---

## Files Modified

- `~/luana-platform/pyproject.toml` — appended 3 workspace members + 3 sources entries

## Implementation

Per 06-tickets.yaml T-1 description + 05-guidelines.md §1.2 verbatim:

1. Read current `~/luana-platform/pyproject.toml` (23 Python workspace members from Stories 2-7)
2. Appended to `[tool.uv.workspace] members`:
   - `"core/luana-core-campaigns"` — Story 8, before brand apps block
   - `"core/luana-core-extension-sdk"` — Story 8, after sales-agent
   - `"apps/test-brand"` — Story 8, after core/ block
3. Appended to `[tool.uv.sources]`:
   - `luana-core-campaigns = { workspace = true }`
   - `luana-core-extension-sdk = { workspace = true }`
   - `test-brand = { workspace = true }`
4. Ran `uv sync --all-packages` — PASSES (packages declared; skeletons created in T-2/T-9/T-14)

## Validators Run

- V-NF-1: `uv sync --all-packages` → `Resolved 212 packages in 16ms; Checked 208 packages in 19ms` → PASS
- V-NF-3: grep for all 3 entries in pyproject.toml → PASS

## Deviations

None. Per 05-guidelines.md §1.2 placement guidance, campaigns before sales-agent alphabetically, extension-sdk after sales-agent, test-brand after core block. All placed in Story 8 (NEW) comment block.

Post-T-1 Python workspace count: 26 (23 baseline + 3 new) per V-NF-1 description.
