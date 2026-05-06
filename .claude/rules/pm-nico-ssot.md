---
description: DEPRECATED stub — pm-nico/ no longer exists (Wave 2 eliminated 2026-05-06)
---

# PM-Nico SSoT — DEPRECATED

> **🛑 DEPRECATED 2026-05-06 (Wave 2 pm-redesign).**
>
> `docs/pm-nico/` no longer exists. All content migrated:
> - Active functional state → `docs/product/modules/{module}.md`
> - Active capabilities → `docs/product/capabilities/{module}/`
> - Live PIs → `docs/product/outcomes/pi-{n}-{slug}.md`
> - Archived PIs → `docs/archive/2026/legacy-pis/`
> - Research/process docs → `docs/archive/2026/legacy-pm-nico-{research,current-state}/`
>
> **New SSoT functional:** `docs/product/BACKLOG.md` (auto-gen) + `docs/product/{outcomes,stories,capabilities,modules,ideas-pool.yaml}`.
>
> **New owner:** `/pm` skill (read `docs/process/pm-redesign-2026-05.md` for paradigm details).
>
> **What replaced this rule's purpose:** any session that modifies user-facing functionality should:
> 1. Update `docs/product/modules/{module}.md` (only the unique narrative + frontmatter — capabilities are auto-listed via marker)
> 2. Update `docs/product/capabilities/{module}/{cap}.yaml` (R32 reconcile_capabilities.py keeps statuses fresh)
> 3. Trigger BACKLOG regen (R33 `scripts/generate_backlog.py` auto via pre-commit hook Section 6)
>
> Detail: `.claude/skills/pm/SKILL.md` § "Capability promotion (al merge)" + `docs/process/pm-redesign-2026-05.md`.

## Migration completed (2026-05-06 Wave 2)

- `docs/pm-nico/` removed in 17 commits
- 16 modules refactored
- 6 still-active PIs migrated to outcomes/
- 11 archived PIs preserved as audit trail
- All code refs (BE arch tests, BE source, BE other tests, hooks, generators) updated to new paths

If you find any reference to `pm-nico/` in `.claude/skills/`, `.claude/rules/`, `.claude/agents/`, `backend/src/`, `frontend/src/`, or any active code path → it's a bug, fix it.
