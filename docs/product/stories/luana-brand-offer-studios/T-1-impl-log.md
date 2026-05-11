---
ticket: T-1
title: "Update luana-platform workspace registration for 2 Story 5 Python packages"
started_at: 2026-05-11
state: assigned
---

## Plan

1. Read current pyproject.toml workspace members + sources (Story 4 end state = 19 packages)
2. Add 2 new Story 5 packages per 03-arch.md §4.1 template:
   - `core/luana-core-brand-studio`
   - `core/luana-core-offer-studio`
3. Run `uv sync --all-packages` to verify resolution (packages don't exist yet — uv tolerates temporarily)
4. Commit: `chore(workspace): register Story 5 packages in uv workspace`

## Notes

- DO NOT create package folders yet (T-2 and T-9 do that)
- Only modify pyproject.toml workspace members + [tool.uv.sources]
- Validators: V-NF-1, V-NF-2, V-NF-3
